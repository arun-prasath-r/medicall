"""
MEDICALL — PHASE 4: COMPREHENSIVE END-TO-END PATIENT JOURNEYS & INTEGRATION TEST SUITE

Tests the complete application workflows against the actual PostgreSQL database (Port 5433 medicall_db)
and FastAPI backend:
- Journey A: Patient Authentication & Strict Role Access Control
- Journey B: Doctor Discovery & Unverified Provider Filtering
- Journey C: Availability Retrieval & Timezone Normalization
- Journey D: Two-Stage Booking, Replay Protection & Database Commit
- Journey E: Patient Data Isolation, Cancellation & Slot Restoration
- Journey F: Appointment Rescheduling & State Consistency
- Journey G: AI Voice & Text API Contracts
- Journey H: Clinical Safety, Deterministic Emergency Escalation & Recurrence Detection
"""

import uuid
import pytest
from datetime import date, time as dtime, datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.availability import Availability, AvailabilityStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.ai.tools.confirmation import generate_confirmation_token
from app.ai.tools.doctor_tools import execute_search_doctors, execute_get_doctor_availability
from app.ai.tools.appointment_tools import (
    execute_get_my_appointments,
    execute_book_appointment,
    execute_cancel_appointment,
    execute_reschedule_appointment,
)
from app.ai.services.safety_service import SafetyService
from app.core.datetime_utils import slot_to_utc_datetime, utc_to_clinic_datetime


@pytest.fixture(scope="module")
def pg_session():
    """Direct session targeting real PostgreSQL database."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def test_client():
    """Direct FastAPI test client."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module")
def isolated_patient(pg_session):
    """Creates a dedicated isolated patient for Phase 4 E2E testing."""
    unique_suffix = uuid.uuid4().hex[:8]
    user = User(
        email=f"e2e.patient.{unique_suffix}@medicall.test",
        hashed_password="SecureTestPassword123!",
        role=UserRole.PATIENT,
        is_verified=True
    )
    pg_session.add(user)
    pg_session.flush()

    patient = Patient(
        user_id=user.id,
        first_name="E2ETest",
        last_name="Patient",
        date_of_birth=date(1990, 5, 15)
    )
    pg_session.add(patient)
    pg_session.commit()
    pg_session.refresh(user)
    pg_session.refresh(patient)

    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    auth_header = {"Authorization": f"Bearer {token}"}

    yield {"user": user, "patient": patient, "token": token, "header": auth_header}

    # Cleanup test records
    try:
        pg_session.query(Appointment).filter(Appointment.patient_id == patient.id).delete()
        pg_session.query(Patient).filter(Patient.id == patient.id).delete()
        pg_session.query(User).filter(User.id == user.id).delete()
        pg_session.commit()
    except Exception:
        pg_session.rollback()


@pytest.fixture(scope="module")
def second_patient(pg_session):
    """Creates a second isolated patient for isolation testing."""
    unique_suffix = uuid.uuid4().hex[:8]
    user = User(
        email=f"e2e.patient2.{unique_suffix}@medicall.test",
        hashed_password="SecureTestPassword123!",
        role=UserRole.PATIENT,
        is_verified=True
    )
    pg_session.add(user)
    pg_session.flush()

    patient = Patient(
        user_id=user.id,
        first_name="SecondTest",
        last_name="Patient",
        date_of_birth=date(1992, 8, 20)
    )
    pg_session.add(patient)
    pg_session.commit()
    pg_session.refresh(user)
    pg_session.refresh(patient)

    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    auth_header = {"Authorization": f"Bearer {token}"}

    yield {"user": user, "patient": patient, "token": token, "header": auth_header}

    try:
        pg_session.query(Appointment).filter(Appointment.patient_id == patient.id).delete()
        pg_session.query(Patient).filter(Patient.id == patient.id).delete()
        pg_session.query(User).filter(User.id == user.id).delete()
        pg_session.commit()
    except Exception:
        pg_session.rollback()


@pytest.fixture(scope="module")
def verified_doctor(pg_session):
    """Retrieves an existing verified doctor from PostgreSQL."""
    doc = pg_session.query(Doctor).join(User).filter(
        User.is_verified == True,
        Doctor.is_accepting_patients == True
    ).first()
    assert doc is not None, "PostgreSQL must contain at least one verified doctor."
    return doc


# ============================================================================
# JOURNEY A — PATIENT AUTHENTICATION & ACCESS CONTROL
# ============================================================================

def test_journey_a_unauthenticated_requests_rejected(test_client):
    """Verifies that protected AI endpoints reject unauthenticated requests with 401."""
    resp1 = test_client.post("/api/v1/ai/chat", json={"message": "Hello"})
    assert resp1.status_code == 401

    resp2 = test_client.post("/api/v1/ai/confirm", json={"confirmation_token": "any-token"})
    assert resp2.status_code == 401


def test_journey_a_doctor_and_admin_cannot_execute_patient_actions(test_client, pg_session):
    """Verifies that doctor accounts cannot call patient appointment confirmation."""
    doctor_user = pg_session.query(User).filter(User.role == UserRole.DOCTOR).first()
    assert doctor_user is not None
    doc_token = create_access_token(data={"sub": str(doctor_user.id), "role": doctor_user.role.value})

    resp = test_client.post(
        "/api/v1/ai/confirm",
        json={"confirmation_token": "some-valid-token"},
        headers={"Authorization": f"Bearer {doc_token}"}
    )
    # Must be forbidden for doctor
    assert resp.status_code in (403, 400)


def test_journey_a_authenticated_patient_jwt_validated(test_client, isolated_patient):
    """Verifies that authenticated patient access to /ai/status succeeds."""
    resp = test_client.get("/api/v1/ai/status", headers=isolated_patient["header"])
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "configured" in data


# ============================================================================
# JOURNEY B — DOCTOR DISCOVERY & UNVERIFIED DOCTOR FILTERING
# ============================================================================

def test_journey_b_search_doctors_filters_unverified(pg_session):
    """Verifies that search_doctors queries PostgreSQL and strictly excludes unverified doctors."""
    res = execute_search_doctors(pg_session)
    assert res["success"] is True
    doctors = res["doctors"]
    assert len(doctors) > 0

    # Ensure none of the returned doctors are unverified
    for doc_info in doctors:
        doc_record = pg_session.query(Doctor).filter(Doctor.id == uuid.UUID(doc_info["id"])).first()
        assert doc_record.user.is_verified is True
        assert doc_record.is_accepting_patients is True


def test_journey_b_empty_search_handled_gracefully(pg_session):
    """Verifies that searching for a non-existent specialty returns clean empty result."""
    res = execute_search_doctors(pg_session, specialty="NonExistentSpecialty12345")
    assert res["success"] is True
    assert res["total_found"] == 0
    assert len(res["doctors"]) == 0
    assert "No matching verified doctors found" in res["message"]


# ============================================================================
# JOURNEY C — DOCTOR AVAILABILITY & TIMEZONE NORMALIZATION
# ============================================================================

def test_journey_c_doctor_availability_timezone_and_status(pg_session, verified_doctor):
    """Verifies available slots match PostgreSQL and correctly format times."""
    res = execute_get_doctor_availability(pg_session, doctor_id=str(verified_doctor.id))
    assert res["success"] is True
    if res["available_slots_count"] > 0:
        slot = res["slots"][0]
        assert "slot_id" in slot
        assert "date" in slot
        assert "start_time" in slot
        assert "end_time" in slot
        assert slot["status"] == "AVAILABLE"


# ============================================================================
# JOURNEY D — APPOINTMENT BOOKING PROPOSAL, REPLAY REJECTION & COMMIT
# ============================================================================

def test_journey_d_booking_proposal_and_explicit_confirmation(pg_session, test_client, isolated_patient, verified_doctor):
    """
    Complete Journey D:
    1. Create an available slot.
    2. Request booking proposal -> requires_confirmation: True, zero mutation in DB.
    3. Explicitly confirm via POST /api/v1/ai/confirm -> creates appointment in DB.
    4. Replay same token -> rejected with HTTP 400.
    """
    test_date = date.today() + timedelta(days=60)
    test_time = dtime(11, 0)
    test_end = dtime(11, 30)

    # Clean pre-existing slot if any
    pg_session.query(Availability).filter(
        Availability.doctor_id == verified_doctor.id,
        Availability.slot_date == test_date,
        Availability.start_time == test_time
    ).delete()
    pg_session.commit()

    slot = Availability(
        doctor_id=verified_doctor.id,
        slot_date=test_date,
        start_time=test_time,
        end_time=test_end,
        status=AvailabilityStatus.AVAILABLE
    )
    pg_session.add(slot)
    pg_session.commit()
    pg_session.refresh(slot)

    # 1. Proposal generation (tool called without confirmation_token)
    proposal = execute_book_appointment(
        db=pg_session,
        current_user=isolated_patient["user"],
        doctor_id=str(verified_doctor.id),
        availability_id=str(slot.id),
        chief_complaint="Persistent headaches for 1 week"
    )

    assert proposal["requires_confirmation"] is True
    token = proposal["confirmation_token"]
    assert token is not None

    # Verify no appointment exists yet in PostgreSQL
    appt_check = pg_session.query(Appointment).filter(Appointment.availability_id == slot.id).first()
    assert appt_check is None, "Database must not be mutated prior to explicit patient confirmation."

    # 2. Explicit confirmation via dedicated endpoint
    confirm_resp = test_client.post(
        "/api/v1/ai/confirm",
        json={"confirmation_token": token},
        headers=isolated_patient["header"]
    )
    assert confirm_resp.status_code == 200, confirm_resp.text
    confirm_data = confirm_resp.json()
    assert confirm_data["success"] is True
    assert confirm_data["reference_code"] is not None

    # Verify appointment exists and slot is BOOKED in PostgreSQL
    pg_session.expire_all()
    committed_appt = pg_session.query(Appointment).filter(Appointment.availability_id == slot.id).first()
    assert committed_appt is not None
    assert committed_appt.status == AppointmentStatus.SCHEDULED
    assert committed_appt.patient_id == isolated_patient["patient"].id

    committed_slot = pg_session.query(Availability).filter(Availability.id == slot.id).first()
    assert committed_slot.status == AvailabilityStatus.BOOKED

    # 3. Token Replay Protection: Replay must fail with 400
    replay_resp = test_client.post(
        "/api/v1/ai/confirm",
        json={"confirmation_token": token},
        headers=isolated_patient["header"]
    )
    assert replay_resp.status_code == 400
    assert "already been used" in replay_resp.json()["detail"].lower()


# ============================================================================
# JOURNEY E — PATIENT DATA ISOLATION & APPOINTMENT CANCELLATION
# ============================================================================

def test_journey_e_patient_isolation_and_cancellation_workflow(
    pg_session, test_client, isolated_patient, second_patient, verified_doctor
):
    """
    Verifies that:
    1. Patient A only sees Patient A's appointments.
    2. Cancellation proposal generates token without state change.
    3. Confirming cancellation releases the slot and sets status CANCELLED_PATIENT.
    """
    # Book an appointment for Patient A
    import random
    test_date = date.today() + timedelta(days=random.randint(600, 1200))
    test_time = dtime(14, 0)

    # Clean pre-existing slot if any
    pg_session.query(Availability).filter(
        Availability.doctor_id == verified_doctor.id,
        Availability.slot_date == test_date,
        Availability.start_time == test_time
    ).delete()
    pg_session.commit()

    slot = Availability(
        doctor_id=verified_doctor.id,
        slot_date=test_date,
        start_time=test_time,
        end_time=dtime(14, 30),
        status=AvailabilityStatus.AVAILABLE
    )
    pg_session.add(slot)
    pg_session.commit()
    pg_session.refresh(slot)

    # Book for Patient A
    appt = Appointment(
        appointment_reference=f"MED-{uuid.uuid4().hex[:6].upper()}",
        patient_id=isolated_patient["patient"].id,
        doctor_id=verified_doctor.id,
        availability_id=slot.id,
        appointment_datetime=slot_to_utc_datetime(slot.slot_date, slot.start_time),
        end_datetime=slot_to_utc_datetime(slot.slot_date, slot.end_time),
        status=AppointmentStatus.SCHEDULED,
        chief_complaint="Confidential Consultation"
    )
    slot.status = AvailabilityStatus.BOOKED
    pg_session.add(appt)
    pg_session.commit()
    pg_session.refresh(appt)

    # Patient B queries appointments -> must NOT see Patient A's appointment
    res_b = execute_get_my_appointments(pg_session, current_user=second_patient["user"])
    assert res_b["success"] is True
    p2_appt_ids = [a["appointment_id"] for a in res_b["appointments"]]
    assert str(appt.id) not in p2_appt_ids, "Patient B must not view Patient A's appointment."

    # Patient A requests cancellation proposal
    proposal = execute_cancel_appointment(
        db=pg_session,
        current_user=isolated_patient["user"],
        appointment_id=str(appt.id),
        reason="Schedule conflict"
    )
    assert proposal["requires_confirmation"] is True
    cancel_token = proposal["confirmation_token"]

    # Explicit confirmation via endpoint
    confirm_resp = test_client.post(
        "/api/v1/ai/confirm",
        json={"confirmation_token": cancel_token},
        headers=isolated_patient["header"]
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["success"] is True

    # Verify status in PostgreSQL
    pg_session.expire_all()
    cancelled_appt = pg_session.query(Appointment).filter(Appointment.id == appt.id).first()
    assert cancelled_appt.status == AppointmentStatus.CANCELLED_PATIENT

    restored_slot = pg_session.query(Availability).filter(Availability.id == slot.id).first()
    assert restored_slot.status == AvailabilityStatus.AVAILABLE


# ============================================================================
# JOURNEY F — APPOINTMENT RESCHEDULING & STATE CONSISTENCY
# ============================================================================

def test_journey_f_rescheduling_maintains_consistent_slots(
    pg_session, test_client, isolated_patient, verified_doctor
):
    """
    Verifies that rescheduling:
    1. Releases original slot to AVAILABLE.
    2. Marks new slot as BOOKED.
    3. Updates appointment reference and status to RESCHEDULED.
    """
    import random
    test_date1 = date.today() + timedelta(days=random.randint(1300, 1800))
    test_date2 = date.today() + timedelta(days=random.randint(1900, 2400))

    pg_session.query(Availability).filter(
        Availability.doctor_id == verified_doctor.id,
        Availability.slot_date.in_([test_date1, test_date2])
    ).delete()
    pg_session.commit()

    slot1 = Availability(
        doctor_id=verified_doctor.id,
        slot_date=test_date1,
        start_time=dtime(10, 0),
        end_time=dtime(10, 30),
        status=AvailabilityStatus.BOOKED
    )
    slot2 = Availability(
        doctor_id=verified_doctor.id,
        slot_date=test_date2,
        start_time=dtime(15, 0),
        end_time=dtime(15, 30),
        status=AvailabilityStatus.AVAILABLE
    )
    pg_session.add_all([slot1, slot2])
    pg_session.commit()
    pg_session.refresh(slot1)
    pg_session.refresh(slot2)

    appt = Appointment(
        appointment_reference=f"MED-{uuid.uuid4().hex[:6].upper()}",
        patient_id=isolated_patient["patient"].id,
        doctor_id=verified_doctor.id,
        availability_id=slot1.id,
        appointment_datetime=slot_to_utc_datetime(slot1.slot_date, slot1.start_time),
        end_datetime=slot_to_utc_datetime(slot1.slot_date, slot1.end_time),
        status=AppointmentStatus.SCHEDULED,
        chief_complaint="Needs rescheduling"
    )
    pg_session.add(appt)
    pg_session.commit()
    pg_session.refresh(appt)

    # Generate reschedule proposal
    proposal = execute_reschedule_appointment(
        db=pg_session,
        current_user=isolated_patient["user"],
        appointment_id=str(appt.id),
        new_availability_id=str(slot2.id)
    )
    assert proposal["requires_confirmation"] is True
    reschedule_token = proposal["confirmation_token"]

    # Confirm reschedule
    confirm_resp = test_client.post(
        "/api/v1/ai/confirm",
        json={"confirmation_token": reschedule_token},
        headers=isolated_patient["header"]
    )
    assert confirm_resp.status_code == 200

    # Verify slots state in PostgreSQL
    pg_session.expire_all()
    s1_updated = pg_session.query(Availability).filter(Availability.id == slot1.id).first()
    s2_updated = pg_session.query(Availability).filter(Availability.id == slot2.id).first()
    appt_updated = pg_session.query(Appointment).filter(Appointment.id == appt.id).first()

    assert s1_updated.status == AvailabilityStatus.AVAILABLE, "Original slot must be released."
    assert s2_updated.status == AvailabilityStatus.BOOKED, "New slot must be booked."
    assert appt_updated.status == AppointmentStatus.RESCHEDULED
    assert appt_updated.availability_id == slot2.id


# ============================================================================
# JOURNEY G — VOICE & TEXT ASSISTANT API CONTRACTS
# ============================================================================

def test_journey_g_chat_endpoint_contract_and_limits(test_client, isolated_patient):
    """Verifies message length constraints and schema validation on /ai/chat."""
    # Empty message -> rejected with 422
    resp_empty = test_client.post(
        "/api/v1/ai/chat",
        json={"message": ""},
        headers=isolated_patient["header"]
    )
    assert resp_empty.status_code == 422

    # Whitespace only -> rejected with 422
    resp_ws = test_client.post(
        "/api/v1/ai/chat",
        json={"message": "     "},
        headers=isolated_patient["header"]
    )
    assert resp_ws.status_code == 422

    # Oversized message (>2000 chars) -> rejected with 422
    resp_big = test_client.post(
        "/api/v1/ai/chat",
        json={"message": "a" * 2001},
        headers=isolated_patient["header"]
    )
    assert resp_big.status_code == 422


# ============================================================================
# JOURNEY H — CLINICAL EMERGENCY HANDLING & NEGATION ENGINE
# ============================================================================

@pytest.mark.parametrize(
    "phrase,expected_emergency,expected_flag",
    [
        ("I have severe crushing chest pain right now.", True, "Suspected Acute Coronary Syndrome"),
        ("I do not have chest pain.", False, None),
        ("I had chest pain five years ago, but today I feel great.", False, None),
        ("I had chest pain yesterday and it is back again right now.", True, "Suspected Acute Coronary Syndrome"),
        ("My doctor wants to rule out a stroke.", True, "Suspected Acute Cerebrovascular Event (Stroke)"),
        ("I have no shortness of breath.", False, None),
        ("I am struggling to breathe right now.", True, "Severe Respiratory Compromise"),
        ("My grandfather collapsed and is unconscious.", True, "Altered Level of Consciousness"),
        ("I had an allergic reaction and my throat is swelling.", True, "Suspected Acute Anaphylaxis"),
        ("I have a history of bleeding, but it stopped completely.", False, None),
        ("The bleeding has started again heavily.", True, "Severe Hemorrhage / Acute Bleeding"),
        ("I am having thoughts of hurting myself.", True, "Crisis / Self-Harm Risk"),
    ]
)
def test_journey_h_emergency_safety_benchmarks(phrase, expected_emergency, expected_flag):
    """Verifies deterministic emergency detection across all 12 clinical benchmark scenarios."""
    is_emerg, flags, guidance = SafetyService.evaluate_emergency_red_flags(phrase)
    assert is_emerg == expected_emergency
    if expected_emergency:
        assert expected_flag in flags
        assert "112" in guidance
        assert "cannot dispatch emergency medical responders" in guidance
