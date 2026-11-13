import concurrent.futures
import uuid
from datetime import date, time, timedelta
from decimal import Decimal
import psycopg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.dependencies import get_db
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.main import app
from app.models.appointment import Appointment, AppointmentStatus
from app.models.availability import Availability, AvailabilityStatus
from app.models.doctor import Doctor
from app.models.doctor_schedule import DoctorSchedule
from app.models.patient import Patient
from app.models.user import User, UserRole

POSTGRES_TEST_URL = settings.DATABASE_URL

pg_engine = create_engine(POSTGRES_TEST_URL, pool_pre_ping=True)
PgTestingSession = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine, expire_on_commit=False)


@pytest.fixture(scope="module")
def pg_db():
    """Provides a PostgreSQL session with verified migrations applied."""
    # Ensure tables exist
    Base.metadata.create_all(bind=pg_engine)
    session = PgTestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def pg_client(pg_db):
    """TestClient wired directly to the real PostgreSQL database."""
    def override_get_db():
        session = PgTestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ============================================================================
# 1. POSTGRESQL SCHEMA & TABLE VERIFICATION
# ============================================================================

def test_postgres_tables_and_metadata():
    """Verifies that all six core entities exist in PostgreSQL with expected schemas."""
    inspector = inspect(pg_engine)
    tables = inspector.get_table_names()

    required_tables = {
        "users",
        "patients",
        "doctors",
        "doctor_schedules",
        "availability",
        "appointments"
    }
    for table in required_tables:
        assert table in tables, f"Expected table '{table}' not found in PostgreSQL."

    # Verify foreign keys
    fks_patient = {fk["referred_table"] for fk in inspector.get_foreign_keys("patients")}
    assert "users" in fks_patient

    fks_doctor = {fk["referred_table"] for fk in inspector.get_foreign_keys("doctors")}
    assert "users" in fks_doctor

    fks_appointments = {fk["referred_table"] for fk in inspector.get_foreign_keys("appointments")}
    assert "patients" in fks_appointments
    assert "doctors" in fks_appointments
    assert "availability" in fks_appointments

    # Verify indexes
    appt_indexes = {idx["name"] for idx in inspector.get_indexes("appointments")}
    assert "idx_appointments_patient_dt" in appt_indexes
    assert "idx_appointments_doctor_dt" in appt_indexes

    avail_indexes = {idx["name"] for idx in inspector.get_indexes("availability")}
    assert "idx_availability_search" in avail_indexes
    assert "idx_availability_date_status" in avail_indexes


# ============================================================================
# 2. CONCURRENT APPOINTMENT BOOKING VERIFICATION (POSTGRESQL LOCKING)
# ============================================================================

def test_postgres_concurrent_booking_race_condition(pg_client, pg_db):
    """
    Simulates two simultaneous concurrent requests attempting to book the
    exact same availability slot in PostgreSQL.
    Verifies that row-level locking (SELECT ... FOR UPDATE) and transaction
    isolation ensures exactly ONE succeeds (201 Created) and the other
    receives an immediate HTTP 409 Conflict.
    """
    # 1. Seed Verified Doctor in PostgreSQL
    doc_user = User(
        email=f"pg.doc.{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("DocPass123!"),
        role=UserRole.DOCTOR,
        is_active=True,
        is_verified=True
    )
    pg_db.add(doc_user)
    pg_db.flush()

    doctor = Doctor(
        user_id=doc_user.id,
        first_name="Marcus",
        last_name="Welby",
        license_number=f"LIC-PG-{uuid.uuid4().hex[:6]}",
        specialty="Family Medicine",
        qualifications="MD",
        consultation_fee=Decimal("100.00"),
        is_accepting_patients=True
    )
    pg_db.add(doctor)
    pg_db.flush()

    # 2. Seed Availability Slot in PostgreSQL
    slot = Availability(
        doctor_id=doctor.id,
        slot_date=date(2026, 12, 10),
        start_time=time(9, 0),
        end_time=time(9, 30),
        status=AvailabilityStatus.AVAILABLE
    )
    pg_db.add(slot)
    pg_db.flush()

    # 3. Seed Two Distinct Patients in PostgreSQL
    p1_user = User(
        email=f"pg.pat1.{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("Pat1Pass123!"),
        role=UserRole.PATIENT,
        is_active=True,
        is_verified=True
    )
    p2_user = User(
        email=f"pg.pat2.{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("Pat2Pass123!"),
        role=UserRole.PATIENT,
        is_active=True,
        is_verified=True
    )
    pg_db.add_all([p1_user, p2_user])
    pg_db.flush()

    pat1 = Patient(
        user_id=p1_user.id,
        first_name="PatientOne",
        last_name="Test",
        date_of_birth=date(1992, 4, 10)
    )
    pat2 = Patient(
        user_id=p2_user.id,
        first_name="PatientTwo",
        last_name="Test",
        date_of_birth=date(1994, 8, 20)
    )
    pg_db.add_all([pat1, pat2])
    pg_db.commit()

    # Generate JWT tokens for both patients
    token1 = create_access_token({"sub": str(p1_user.id), "role": "PATIENT"})
    token2 = create_access_token({"sub": str(p2_user.id), "role": "PATIENT"})

    booking_payload = {
        "doctor_id": str(doctor.id),
        "availability_id": str(slot.id),
        "chief_complaint": "Persistent migraines under load"
    }

    # Execute concurrent requests against PostgreSQL
    def attempt_booking(token):
        with TestClient(app) as local_client:
            return local_client.post(
                "/api/v1/appointments",
                json=booking_payload,
                headers={"Authorization": f"Bearer {token}"}
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(attempt_booking, token1)
        future2 = executor.submit(attempt_booking, token2)
        resp1 = future1.result()
        resp2 = future2.result()

    status_codes = sorted([resp1.status_code, resp2.status_code])
    assert status_codes == [201, 409], (
        f"Expected exactly one 201 Created and one 409 Conflict under PostgreSQL locking, "
        f"got: {resp1.status_code} and {resp2.status_code}"
    )

    # Verify that in PostgreSQL, the slot is now BOOKED and exactly 1 appointment exists
    pg_db.expire_all()
    slot_in_pg = pg_db.query(Availability).filter(Availability.id == slot.id).first()
    assert slot_in_pg.status == AvailabilityStatus.BOOKED

    appts_in_pg = pg_db.query(Appointment).filter(Appointment.availability_id == slot.id).all()
    assert len(appts_in_pg) == 1


# ============================================================================
# 3. CANCELLATION & RESCHEDULING SLOT STATE VERIFICATION (POSTGRESQL)
# ============================================================================

def test_postgres_cancellation_and_rescheduling_state_restoration(pg_client, pg_db):
    """Verifies that cancellation releases slots and rescheduling transitions states properly."""
    # Seed Doctor
    doc_user = User(
        email=f"pg.doc.state.{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("DocPass123!"),
        role=UserRole.DOCTOR,
        is_active=True,
        is_verified=True
    )
    pg_db.add(doc_user)
    pg_db.flush()

    doctor = Doctor(
        user_id=doc_user.id,
        first_name="Allison",
        last_name="Cameron",
        license_number=f"LIC-CAM-{uuid.uuid4().hex[:6]}",
        specialty="Immunology",
        qualifications="MD",
        consultation_fee=Decimal("120.00"),
        is_accepting_patients=True
    )
    pg_db.add(doctor)
    pg_db.flush()

    slot_a = Availability(
        doctor_id=doctor.id,
        slot_date=date(2026, 12, 11),
        start_time=time(10, 0),
        end_time=time(10, 30),
        status=AvailabilityStatus.AVAILABLE
    )
    slot_b = Availability(
        doctor_id=doctor.id,
        slot_date=date(2026, 12, 11),
        start_time=time(11, 0),
        end_time=time(11, 30),
        status=AvailabilityStatus.AVAILABLE
    )
    pg_db.add_all([slot_a, slot_b])
    pg_db.flush()

    pat_user = User(
        email=f"pg.pat.state.{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("PatPass123!"),
        role=UserRole.PATIENT,
        is_active=True,
        is_verified=True
    )
    pg_db.add(pat_user)
    pg_db.flush()

    pat = Patient(
        user_id=pat_user.id,
        first_name="State",
        last_name="Verifier",
        date_of_birth=date(1991, 2, 15)
    )
    pg_db.add(pat)
    pg_db.commit()

    token = create_access_token({"sub": str(pat_user.id), "role": "PATIENT"})

    # 1. Book Slot A
    book_resp = pg_client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": str(doctor.id),
            "availability_id": str(slot_a.id),
            "chief_complaint": "Seasonal allergies"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert book_resp.status_code == 201
    appt_id = book_resp.json()["id"]

    # 2. Reschedule to Slot B
    resched_resp = pg_client.patch(
        f"/api/v1/appointments/{appt_id}/reschedule",
        json={"new_availability_id": str(slot_b.id)},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resched_resp.status_code == 200
    assert resched_resp.json()["status"] == "RESCHEDULED"

    # Verify in PostgreSQL: Slot A is AVAILABLE, Slot B is BOOKED
    pg_db.expire_all()
    slot_a_refreshed = pg_db.query(Availability).filter(Availability.id == slot_a.id).first()
    slot_b_refreshed = pg_db.query(Availability).filter(Availability.id == slot_b.id).first()
    assert slot_a_refreshed.status == AvailabilityStatus.AVAILABLE
    assert slot_b_refreshed.status == AvailabilityStatus.BOOKED

    # 3. Cancel Appointment
    cancel_resp = pg_client.patch(
        f"/api/v1/appointments/{appt_id}/cancel",
        json={"cancellation_reason": "Schedule resolved itself."},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED_PATIENT"

    # Verify in PostgreSQL: Slot B is restored to AVAILABLE
    pg_db.expire_all()
    slot_b_after_cancel = pg_db.query(Availability).filter(Availability.id == slot_b.id).first()
    assert slot_b_after_cancel.status == AvailabilityStatus.AVAILABLE


# ============================================================================
# 4. DOCTOR VERIFICATION CHECKS
# ============================================================================

def test_unverified_doctor_cannot_offer_consultations(pg_client, pg_db):
    """
    Verifies that unverified doctors cannot offer bookable consultations.
    An attempt to book an unverified doctor's slot must be rejected with 400.
    """
    # 1. Register a doctor via public API -> By design, is_verified is FALSE
    doc_email = f"unverified.doc.{uuid.uuid4().hex[:6]}@example.com"
    reg_resp = pg_client.post(
        "/api/v1/auth/register",
        json={
            "email": doc_email,
            "password": "UnverifiedPass123!",
            "role": "DOCTOR",
            "first_name": "Unverified",
            "last_name": "Doctor",
            "license_number": f"UNVERIFIED-{uuid.uuid4().hex[:6]}",
            "specialty": "Neurology",
            "qualifications": "MBBS",
            "consultation_fee": 150.00
        }
    )
    assert reg_resp.status_code == 201
    assert reg_resp.json()["is_verified"] is False
    doc_profile_id = uuid.UUID(reg_resp.json()["profile_id"])

    # Create slot for this unverified doctor directly in PostgreSQL
    slot = Availability(
        doctor_id=doc_profile_id,
        slot_date=date(2026, 12, 15),
        start_time=time(14, 0),
        end_time=time(14, 30),
        status=AvailabilityStatus.AVAILABLE
    )
    pg_db.add(slot)
    pg_db.commit()

    # Seed verified patient
    pat_user = User(
        email=f"pat.unver.{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("PatPass123!"),
        role=UserRole.PATIENT,
        is_active=True,
        is_verified=True
    )
    pg_db.add(pat_user)
    pg_db.flush()

    pat = Patient(
        user_id=pat_user.id,
        first_name="Tester",
        last_name="Patient",
        date_of_birth=date(1990, 5, 5)
    )
    pg_db.add(pat)
    pg_db.commit()

    token = create_access_token({"sub": str(pat_user.id), "role": "PATIENT"})

    # Attempt to book consultation with the unverified doctor
    book_resp = pg_client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": str(doc_profile_id),
            "availability_id": str(slot.id),
            "chief_complaint": "Neurological consultation"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert book_resp.status_code == 400
    assert "unverified doctor" in book_resp.json()["detail"].lower()


# ============================================================================
# 5. SECURITY & PRIVACY VERIFICATION
# ============================================================================

def test_security_jwt_expiration_and_tampering(pg_client):
    """Verifies that expired or tampered JWT tokens are strictly rejected."""
    # 1. Expired token
    expired_token = create_access_token(
        data={"sub": str(uuid.uuid4()), "role": "PATIENT"},
        expires_delta=timedelta(seconds=-10)
    )
    resp_expired = pg_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert resp_expired.status_code == 401
    assert "expired" in resp_expired.json()["detail"].lower()

    # 2. Tampered token
    tampered_token = expired_token[:-4] + "fake"
    resp_tampered = pg_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"}
    )
    assert resp_tampered.status_code == 401

    # 3. Missing authorization header
    resp_missing = pg_client.get("/api/v1/auth/me")
    assert resp_missing.status_code == 401


def test_security_no_passwords_in_responses(pg_client, pg_db):
    """Verifies that password hashes are never leaked in any API response."""
    email = f"sec.check.{uuid.uuid4().hex[:6]}@example.com"
    pwd = "SecPassword123!"
    reg_resp = pg_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": pwd,
            "role": "PATIENT",
            "first_name": "Security",
            "last_name": "Check",
            "date_of_birth": "1990-01-01"
        }
    )
    data = reg_resp.json()
    assert "password" not in data
    assert "hashed_password" not in data

    login_resp = pg_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": pwd}
    )
    login_data = login_resp.json()
    assert "password" not in login_data
    assert "hashed_password" not in login_data
    assert "password" not in login_data.get("user", {})
    assert "hashed_password" not in login_data.get("user", {})
