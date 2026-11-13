import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.datetime_utils import (
    ensure_utc,
    get_clinic_timezone,
    slot_to_utc_datetime,
    utc_to_clinic_datetime,
)
from app.core.dependencies import get_db
from app.core.security import hash_password
from app.db.base import Base
from app.main import app
from app.models.appointment import Appointment, AppointmentStatus
from app.models.availability import Availability, AvailabilityStatus
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User, UserRole


# ============================================================================
# 1. UNIT TESTS: DATETIME CONVERSION UTILITIES
# ============================================================================

def test_clinic_timezone_configuration():
    """Verifies that the clinic timezone standard is configured to Asia/Kolkata."""
    assert settings.CLINIC_TIMEZONE == "Asia/Kolkata"
    tz = get_clinic_timezone()
    assert tz == ZoneInfo("Asia/Kolkata")


def test_mandatory_test_case_conversion():
    """
    MANDATORY TEST CASE:
    Patient selects: 11 November 2026, 04:00 PM IST (16:00:00)
    Expected UTC instant: 11 November 2026, 10:30 AM UTC (2026-11-11 10:30:00+00:00)
    """
    slot_date = date(2026, 11, 11)
    slot_time = time(16, 0, 0)

    utc_dt = slot_to_utc_datetime(slot_date, slot_time)

    assert utc_dt.tzinfo == timezone.utc
    assert utc_dt.year == 2026
    assert utc_dt.month == 11
    assert utc_dt.day == 11
    assert utc_dt.hour == 10
    assert utc_dt.minute == 30
    assert utc_dt.second == 0

    # Verify reverse conversion back to clinic timezone
    clinic_dt = utc_to_clinic_datetime(utc_dt)
    assert clinic_dt.year == 2026
    assert clinic_dt.month == 11
    assert clinic_dt.day == 11
    assert clinic_dt.hour == 16
    assert clinic_dt.minute == 0


def test_midnight_boundary_conversion():
    """
    EDGE CASE: Midnight boundary across days.
    Slot in Asia/Kolkata: 12 November 2026, 02:00 AM IST (02:00:00)
    Expected UTC instant: 11 November 2026, 08:30 PM UTC (2026-11-11 20:30:00+00:00)
    """
    slot_date = date(2026, 11, 12)
    slot_time = time(2, 0, 0)

    utc_dt = slot_to_utc_datetime(slot_date, slot_time)

    assert utc_dt.tzinfo == timezone.utc
    assert utc_dt.year == 2026
    assert utc_dt.month == 11
    assert utc_dt.day == 11  # Day shifts to day D-1 in UTC
    assert utc_dt.hour == 20
    assert utc_dt.minute == 30

    # Reverse conversion back to Asia/Kolkata
    clinic_dt = utc_to_clinic_datetime(utc_dt)
    assert clinic_dt.year == 2026
    assert clinic_dt.month == 11
    assert clinic_dt.day == 12  # Day returns to day D in IST
    assert clinic_dt.hour == 2
    assert clinic_dt.minute == 0


def test_month_boundary_conversion():
    """
    EDGE CASE: Month boundary across months.
    Slot in Asia/Kolkata: 01 December 2026, 02:00 AM IST (02:00:00)
    Expected UTC instant: 30 November 2026, 08:30 PM UTC (2026-11-30 20:30:00+00:00)
    """
    slot_date = date(2026, 12, 1)
    slot_time = time(2, 0, 0)

    utc_dt = slot_to_utc_datetime(slot_date, slot_time)

    assert utc_dt.tzinfo == timezone.utc
    assert utc_dt.year == 2026
    assert utc_dt.month == 11  # Month shifts to November in UTC
    assert utc_dt.day == 30
    assert utc_dt.hour == 20
    assert utc_dt.minute == 30

    # Reverse conversion back to Asia/Kolkata
    clinic_dt = utc_to_clinic_datetime(utc_dt)
    assert clinic_dt.year == 2026
    assert clinic_dt.month == 12
    assert clinic_dt.day == 1
    assert clinic_dt.hour == 2
    assert clinic_dt.minute == 0


def test_ensure_utc_helper():
    """Verifies that naive datetimes gain UTC tzinfo and aware datetimes are converted."""
    naive_dt = datetime(2026, 11, 11, 10, 30, 0)
    aware_dt = ensure_utc(naive_dt)
    assert aware_dt.tzinfo == timezone.utc
    assert aware_dt.hour == 10

    ist_dt = datetime(2026, 11, 11, 16, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    converted_dt = ensure_utc(ist_dt)
    assert converted_dt.tzinfo == timezone.utc
    assert converted_dt.hour == 10
    assert converted_dt.minute == 30


# ============================================================================
# 2. INTEGRATION TESTS: API BOOKING & RESCHEDULING TIMEZONE LIFECYCLE
# ============================================================================

def test_api_booking_stores_and_returns_utc(
    client, sample_patient, sample_doctor, db_session
):
    """
    Tests the mandatory test case through the full FastAPI appointment booking endpoint:
    - Slot: 2026-11-11, 16:00:00 - 16:30:00 (Asia/Kolkata / IST)
    - Booking API payload sent
    - Response contains UTC timestamp '2026-11-11T10:30:00+00:00'
    - DB record stores 2026-11-11 10:30:00 UTC
    """
    # Create mandatory test case slot (11 Nov 2026, 16:00:00 IST)
    test_slot = Availability(
        id=uuid.uuid4(),
        doctor_id=sample_doctor.id,
        slot_date=date(2026, 11, 11),
        start_time=time(16, 0, 0),
        end_time=time(16, 30, 0),
        status=AvailabilityStatus.AVAILABLE,
    )
    db_session.add(test_slot)
    db_session.commit()

    # Patient logs in
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "patient.test@example.com",
        "password": "PatientPass123!"
    })
    token = login_resp.json()["access_token"]

    # Book appointment
    booking_resp = client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": str(sample_doctor.id),
            "availability_id": str(test_slot.id),
            "chief_complaint": "Mandatory timezone audit test consultation."
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert booking_resp.status_code == 201
    data = booking_resp.json()

    # Verify API response serializes UTC timestamp
    assert data["appointment_datetime"].startswith("2026-11-11T10:30:00")
    assert "+00:00" in data["appointment_datetime"] or data["appointment_datetime"].endswith("Z")

    # Verify database model directly
    appointment = db_session.query(Appointment).filter(
        Appointment.id == uuid.UUID(data["id"])
    ).first()
    assert appointment is not None
    # Normalized to UTC
    appt_dt_utc = ensure_utc(appointment.appointment_datetime)
    assert appt_dt_utc.year == 2026
    assert appt_dt_utc.month == 11
    assert appt_dt_utc.day == 11
    assert appt_dt_utc.hour == 10
    assert appt_dt_utc.minute == 30


def test_api_rescheduling_maintains_utc_standardization(
    client, sample_patient, sample_doctor, db_session
):
    """
    Tests rescheduling from standard time to a midnight boundary slot:
    - Original slot: 2026-11-11 16:00:00 IST (10:30 UTC)
    - Reschedule target: 2026-11-12 02:00:00 IST (20:30 UTC on 2026-11-11)
    - Verifies DB and API response update to the correct UTC instant.
    """
    slot_1 = Availability(
        id=uuid.uuid4(),
        doctor_id=sample_doctor.id,
        slot_date=date(2026, 11, 11),
        start_time=time(16, 0, 0),
        end_time=time(16, 30, 0),
        status=AvailabilityStatus.AVAILABLE,
    )
    # Midnight boundary slot (02:00 AM IST on Nov 12 = 20:30 UTC on Nov 11)
    slot_2 = Availability(
        id=uuid.uuid4(),
        doctor_id=sample_doctor.id,
        slot_date=date(2026, 11, 12),
        start_time=time(2, 0, 0),
        end_time=time(2, 30, 0),
        status=AvailabilityStatus.AVAILABLE,
    )
    db_session.add_all([slot_1, slot_2])
    db_session.commit()

    # Patient logs in
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "patient.test@example.com",
        "password": "PatientPass123!"
    })
    token = login_resp.json()["access_token"]

    # Book slot 1
    booking_resp = client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": str(sample_doctor.id),
            "availability_id": str(slot_1.id),
            "chief_complaint": "Initial booking before rescheduling."
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert booking_resp.status_code == 201
    appt_id = booking_resp.json()["id"]

    # Reschedule to slot 2 (midnight boundary)
    resched_resp = client.patch(
        f"/api/v1/appointments/{appt_id}/reschedule",
        json={"new_availability_id": str(slot_2.id)},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resched_resp.status_code == 200
    resched_data = resched_resp.json()

    # UTC instant is 2026-11-11 20:30:00 UTC
    assert resched_data["appointment_datetime"].startswith("2026-11-11T20:30:00")

    # Verify DB record
    db_session.expire_all()
    appointment = db_session.query(Appointment).filter(Appointment.id == uuid.UUID(appt_id)).first()
    appt_dt_utc = ensure_utc(appointment.appointment_datetime)
    assert appt_dt_utc.year == 2026
    assert appt_dt_utc.month == 11
    assert appt_dt_utc.day == 11
    assert appt_dt_utc.hour == 20
    assert appt_dt_utc.minute == 30


# ============================================================================
# 3. POSTGRESQL TIMESTAMPTZ COLUMN & SQL ENGINE VERIFICATION
# ============================================================================

def test_postgresql_timestamptz_mandatory_case():
    """
    Runs directly against PostgreSQL in docker container (medicall_test_db).
    Verifies:
    1. Table 'appointments' has column 'appointment_datetime' of type 'timestamp with time zone'.
    2. Booking 11 Nov 2026 16:00:00 IST stores 11 Nov 2026 10:30:00+00 in PostgreSQL.
    3. PostgreSQL 'AT TIME ZONE' SQL queries return exact expected values.
    """
    POSTGRES_TEST_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/medicall_test_db"
    pg_engine = create_engine(POSTGRES_TEST_URL, pool_pre_ping=True)
    PgSession = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)

    Base.metadata.create_all(bind=pg_engine)
    session = PgSession()

    try:
        # Check column datatype in PostgreSQL information_schema
        col_type_query = text("""
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_name = 'appointments' AND column_name = 'appointment_datetime'
        """)
        res = session.execute(col_type_query).fetchone()
        assert res is not None
        assert res.data_type == "timestamp with time zone"
        assert res.udt_name == "timestamptz"

        # Create isolated doctor and patient in PostgreSQL
        unique_suffix = uuid.uuid4().hex[:8]
        user_doc = User(
            id=uuid.uuid4(),
            email=f"tz_doc_{unique_suffix}@example.com",
            hashed_password=hash_password("Pass123!"),
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True
        )
        doc = Doctor(
            id=uuid.uuid4(),
            user_id=user_doc.id,
            first_name="Timezone",
            last_name="Specialist",
            specialty="Internal Medicine",
            qualifications="MD Internal Medicine",
            license_number=f"TZ-{unique_suffix}",
            consultation_fee=Decimal("150.00"),
            is_accepting_patients=True
        )
        user_pat = User(
            id=uuid.uuid4(),
            email=f"tz_pat_{unique_suffix}@example.com",
            hashed_password=hash_password("Pass123!"),
            role=UserRole.PATIENT,
            is_active=True
        )
        pat = Patient(
            id=uuid.uuid4(),
            user_id=user_pat.id,
            first_name="Timezone",
            last_name="Patient",
            date_of_birth=date(1990, 5, 20),
            emergency_contact_phone=f"+1555{unique_suffix[:7]}"
        )
        slot = Availability(
            id=uuid.uuid4(),
            doctor_id=doc.id,
            slot_date=date(2026, 11, 11),
            start_time=time(16, 0, 0),
            end_time=time(16, 30, 0),
            status=AvailabilityStatus.AVAILABLE
        )
        session.add_all([user_doc, doc, user_pat, pat, slot])
        session.commit()

        # Wire TestClient to PostgreSQL
        def override_get_db():
            pg_s = PgSession()
            try:
                yield pg_s
            finally:
                pg_s.close()

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as pg_client:
            # Login as patient
            login_resp = pg_client.post("/api/v1/auth/login", json={
                "email": user_pat.email,
                "password": "Pass123!"
            })
            token = login_resp.json()["access_token"]

            # Book appointment
            book_resp = pg_client.post(
                "/api/v1/appointments",
                json={
                    "doctor_id": str(doc.id),
                    "availability_id": str(slot.id),
                    "chief_complaint": "Testing PostgreSQL TIMESTAMPTZ storage for 04:00 PM IST."
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            assert book_resp.status_code == 201
            appt_id = book_resp.json()["id"]

            # Verify PostgreSQL raw row directly
            sql_check = text("""
                SELECT 
                    appointment_datetime,
                    appointment_datetime AT TIME ZONE 'UTC' as utc_time,
                    appointment_datetime AT TIME ZONE 'Asia/Kolkata' as ist_time
                FROM appointments
                WHERE id = :appt_id
            """)
            row = session.execute(sql_check, {"appt_id": uuid.UUID(appt_id)}).fetchone()
            assert row is not None

            # row.appointment_datetime is stored in PostgreSQL as TIMESTAMPTZ:
            # In UTC: 2026-11-11 10:30:00+00
            assert row.appointment_datetime.tzinfo is not None
            utc_version = row.appointment_datetime.astimezone(timezone.utc)
            assert utc_version.year == 2026
            assert utc_version.month == 11
            assert utc_version.day == 11
            assert utc_version.hour == 10
            assert utc_version.minute == 30

            # Direct PostgreSQL AT TIME ZONE queries
            assert row.utc_time == datetime(2026, 11, 11, 10, 30, 0)
            assert row.ist_time == datetime(2026, 11, 11, 16, 0, 0)

        app.dependency_overrides.clear()
    finally:
        session.close()
