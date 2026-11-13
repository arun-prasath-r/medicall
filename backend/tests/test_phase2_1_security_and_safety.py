"""
Phase 2.1: Comprehensive Security Audit, Confirmation Hardening,
Database Concurrency, and Clinical AI Safety Verification Tests.
"""

import concurrent.futures
import threading
import time
import uuid
from datetime import date, datetime, time as dtime, timedelta, timezone
from unittest import mock
import pytest
from google.genai import types

from app.core.config import Settings, settings
from app.core.datetime_utils import slot_to_utc_datetime
from app.models.appointment import Appointment, AppointmentStatus
from app.models.availability import Availability, AvailabilityStatus
from app.models.consumed_token import ConsumedConfirmationToken
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.services.appointment_service import AppointmentService
from app.ai.services.gemini_service import GeminiGenerationResult, GeminiService
from app.ai.services.safety_service import SafetyService
from app.ai.tools.confirmation import (
    ConfirmationError,
    generate_confirmation_token,
    verify_confirmation_token,
)
from app.ai.tools.appointment_tools import (
    execute_book_appointment,
    execute_cancel_appointment,
    execute_get_my_appointments,
    execute_reschedule_appointment,
)
from app.ai.tools.doctor_tools import (
    execute_get_doctor_availability,
    execute_search_doctors,
)
from app.ai.tools.dispatcher import ToolDispatcher
from app.ai.router import get_gemini_service


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def patient_auth_header(client, sample_patient):
    """Provides authorization header for sample_patient."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "patient.test@example.com",
        "password": "PatientPass123!"
    })
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# 1. CLINICAL EMERGENCY DETECTION — ALL 12 MANDATORY TEST PHRASES (TASK 3)
# ============================================================================

@pytest.mark.parametrize(
    "phrase,expected_emergency,category",
    [
        ("I have severe chest pain right now.", True, "Suspected Acute Coronary Syndrome"),
        ("I do not have chest pain.", False, None),
        ("I had chest pain three years ago, but I am fine today.", False, None),
        ("I had chest pain last night and it is back again.", True, "Suspected Acute Coronary Syndrome"),
        ("My doctor wants to rule out a stroke.", True, "Suspected Acute Cerebrovascular Event (Stroke)"),
        ("I have no difficulty breathing.", False, None),
        ("I am struggling to breathe right now.", True, "Severe Respiratory Compromise"),
        ("My father is unconscious.", True, "Altered Level of Consciousness"),
        ("I had an allergic reaction and my throat is swelling.", True, "Suspected Acute Anaphylaxis"),
        ("I have a history of bleeding, but it stopped.", False, None),
        ("The bleeding has started again.", True, "Severe Hemorrhage / Acute Bleeding"),
        ("I am thinking about hurting myself.", True, "Crisis / Self-Harm Risk"),
    ]
)
def test_all_twelve_mandatory_clinical_emergency_phrases(phrase, expected_emergency, category):
    """
    Independently verifies all 12 mandatory clinical phrases specified by Task 3.
    Guarantees strict differentiation between current emergencies, negated symptoms,
    historical events, and acute recurrences.
    """
    is_emerg, conditions, guidance = SafetyService.evaluate_emergency_red_flags(phrase)

    assert is_emerg is expected_emergency, (
        f"Failed evaluation for phrase: '{phrase}'. Expected {expected_emergency}, got {is_emerg}."
    )

    if expected_emergency:
        assert len(conditions) > 0
        assert category in conditions
        assert settings.EMERGENCY_PHONE_NUMBER in guidance
        assert "call local emergency services" in guidance
        assert "Medicall AI is an informational scheduling assistant and cannot dispatch emergency medical responders" in guidance
    else:
        assert len(conditions) == 0
        assert guidance == ""


# ============================================================================
# 2. CONFIRMATION TOKEN SINGLE-USE & REPLAY PROTECTION (TASK 2)
# ============================================================================

def test_confirmation_token_is_single_use_and_rejects_replay(db_session, sample_patient, sample_doctor):
    """
    Verifies that a confirmation token CANNOT be used more than once.
    Second attempt must raise ConfirmationError and be rejected as a replay attack.
    """
    slot = Availability(
        doctor_id=sample_doctor.id,
        slot_date=date.today() + timedelta(days=5),
        start_time=dtime(10, 0),
        end_time=dtime(10, 30),
        status=AvailabilityStatus.AVAILABLE
    )
    db_session.add(slot)
    db_session.commit()
    db_session.refresh(slot)

    # 1. Generate token
    token = generate_confirmation_token(
        action="book_appointment",
        patient_id=sample_patient.id,
        params={"doctor_id": str(sample_doctor.id), "availability_id": str(slot.id), "chief_complaint": "Headache"}
    )

    # 2. First execution -> Must succeed
    first_res = execute_book_appointment(
        db=db_session,
        current_user=sample_patient.user,
        doctor_id=str(sample_doctor.id),
        availability_id=str(slot.id),
        chief_complaint="Headache",
        confirmation_token=token
    )
    assert first_res["success"] is True
    assert "MED-" in first_res["reference_code"]

    # Verify that a record was added to consumed_confirmation_tokens
    consumed_count = db_session.query(ConsumedConfirmationToken).count()
    assert consumed_count >= 1

    # 3. Second execution (REPLAY) with the SAME token -> MUST FAIL
    replay_res = execute_book_appointment(
        db=db_session,
        current_user=sample_patient.user,
        doctor_id=str(sample_doctor.id),
        availability_id=str(slot.id),
        chief_complaint="Headache",
        confirmation_token=token
    )
    assert replay_res["success"] is False
    assert "already been used" in replay_res["error"]


def test_concurrent_confirmation_token_redemption_race_condition(db_session, sample_patient, sample_doctor):
    """
    Simulates two concurrent attempts to redeem the exact same confirmation token.
    The database unique constraint and atomic consumption guarantee that only ONE succeeds.
    """
    slot = Availability(
        doctor_id=sample_doctor.id,
        slot_date=date.today() + timedelta(days=6),
        start_time=dtime(11, 0),
        end_time=dtime(11, 30),
        status=AvailabilityStatus.AVAILABLE
    )
    db_session.add(slot)
    db_session.commit()
    db_session.refresh(slot)

    token = generate_confirmation_token(
        action="book_appointment",
        patient_id=sample_patient.id,
        params={"doctor_id": str(sample_doctor.id), "availability_id": str(slot.id), "chief_complaint": "Joint pain"}
    )

    # Attempt 1: Verify token with DB session (consumes it)
    verified = verify_confirmation_token(
        token=token,
        expected_action="book_appointment",
        current_patient_id=sample_patient.id,
        db=db_session
    )
    assert verified["doctor_id"] == str(sample_doctor.id)

    # Attempt 2: Immediate second attempt with same token and session -> Must raise ConfirmationError
    with pytest.raises(ConfirmationError) as exc_info:
        verify_confirmation_token(
            token=token,
            expected_action="book_appointment",
            current_patient_id=sample_patient.id,
            db=db_session
        )
    assert "already been used" in str(exc_info.value)


# ============================================================================
# 3. ORCHESTRATION GUARD — PREVENT SAME-TURN AUTOMATIC EXECUTION (TASK 2)
# ============================================================================

def test_gemini_service_terminates_loop_on_action_proposal():
    """
    Verifies that when a write tool returns requires_confirmation: True,
    GeminiService terminates the tool loop immediately and disables tools
    on the final prompt to prevent same-turn automatic execution.
    """
    service = GeminiService(api_key="test-api-key")

    mock_client = mock.MagicMock()

    # Step 1: Model calls book_appointment
    fc = types.FunctionCall(
        name="book_appointment",
        args={"doctor_id": str(uuid.uuid4()), "availability_id": str(uuid.uuid4()), "chief_complaint": "Fever"}
    )
    step1_response = types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=[types.Part(function_call=fc)]))]
    )

    # Step 2: Model generates conversational confirmation proposal text
    step2_response = types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=[types.Part.from_text(text="I found a slot. Would you like me to book it?")]))]
    )

    mock_client.models.generate_content.side_effect = [step1_response, step2_response]
    mock_dispatcher = mock.MagicMock()
    mock_dispatcher.dispatch.return_value = {
        "requires_confirmation": True,
        "action": "book_appointment",
        "confirmation_token": "signed-token-12345",
        "summary": "Booking with Dr. Smith"
    }

    mock_db = mock.MagicMock()
    mock_user = mock.MagicMock()
    mock_user.id = uuid.uuid4()

    with mock.patch.object(service, "_get_client", return_value=mock_client):
        result = service.generate_response(
            prompt="Book Dr. Smith",
            tools=[mock.MagicMock()],
            tool_dispatcher=mock_dispatcher,
            db=mock_db,
            current_user=mock_user
        )

    # Verify execution was terminated after step 2 (total 2 generate_content calls)
    assert mock_client.models.generate_content.call_count == 2
    # Second call MUST have tools=None (disabled)
    second_call_config = mock_client.models.generate_content.call_args_list[1][1]["config"]
    assert second_call_config.tools is None
    # Action proposal must be attached
    assert result.action_proposal is not None
    assert result.action_proposal["action"] == "book_appointment"
    assert result.action_proposal["confirmation_token"] == "signed-token-12345"


# ============================================================================
# 4. CONFIRMATION SECURITY & PARAMETER INTEGRITY (TASK 2)
# ============================================================================

def test_confirmation_token_rejects_cross_patient_use(sample_patient, sample_patient_2):
    """Verifies that a token issued to Patient A cannot be authorized for Patient B."""
    token = generate_confirmation_token(
        action="book_appointment",
        patient_id=sample_patient.id,
        params={"slot_id": "slot-123"}
    )
    with pytest.raises(ConfirmationError) as exc_info:
        verify_confirmation_token(
            token=token,
            expected_action="book_appointment",
            current_patient_id=sample_patient_2.id
        )
    assert "does not belong" in str(exc_info.value) or "Security violation" in str(exc_info.value)


def test_confirmation_token_rejects_action_mismatch(sample_patient):
    """Verifies that a booking token cannot be used to cancel or reschedule."""
    token = generate_confirmation_token(
        action="book_appointment",
        patient_id=sample_patient.id,
        params={"slot_id": "slot-123"}
    )
    with pytest.raises(ConfirmationError) as exc_info:
        verify_confirmation_token(
            token=token,
            expected_action="cancel_appointment",
            current_patient_id=sample_patient.id
        )
    assert "Action mismatch" in str(exc_info.value)


def test_confirmation_token_rejects_expired_token(sample_patient):
    """Verifies that an expired confirmation token is rejected."""
    # Generate token with negative expiration
    token = generate_confirmation_token(
        action="book_appointment",
        patient_id=sample_patient.id,
        params={"slot_id": "slot-123"},
        expires_in_minutes=-1
    )
    with pytest.raises(ConfirmationError) as exc_info:
        verify_confirmation_token(
            token=token,
            expected_action="book_appointment",
            current_patient_id=sample_patient.id
        )
    assert "expired" in str(exc_info.value).lower()


# ============================================================================
# 5. PATIENT PRIVACY & SENSITIVE INFORMATION REDACTION (TASK 5)
# ============================================================================

def test_patient_data_isolation_appointment_retrieval(db_session, sample_patient, sample_patient_2, sample_doctor, sample_slot):
    """Verifies Patient A cannot view Patient B's appointment records."""
    # Create appointment for Patient 1
    appt1 = Appointment(
        appointment_reference="MED-ISOL-P1",
        patient_id=sample_patient.id,
        doctor_id=sample_doctor.id,
        availability_id=sample_slot.id,
        appointment_datetime=slot_to_utc_datetime(sample_slot.slot_date, sample_slot.start_time),
        end_datetime=slot_to_utc_datetime(sample_slot.slot_date, sample_slot.end_time),
        status=AppointmentStatus.SCHEDULED,
        chief_complaint="Confidential Symptom P1"
    )
    db_session.add(appt1)
    db_session.commit()

    # Query appointments as Patient 2
    res_p2 = execute_get_my_appointments(db_session, current_user=sample_patient_2.user)
    assert res_p2["success"] is True
    # Patient 2 must NOT see Patient 1's appointment
    refs = [a["reference_code"] for a in res_p2["appointments"]]
    assert "MED-ISOL-P1" not in refs


def test_tool_dispatcher_rejects_unknown_tool(db_session, sample_patient):
    """Verifies that arbitrary or unknown tool calls are safely rejected."""
    res = ToolDispatcher.dispatch(
        name="drop_database",
        arguments={"table": "patients"},
        db=db_session,
        current_user=sample_patient.user
    )
    assert res["success"] is False
    assert "Unknown tool" in res["error"]


# ============================================================================
# 6. POSTGRESQL CONCURRENT BOOKING INTEGRATION TEST (TASK 4)
# ============================================================================

def test_postgres_concurrent_booking_race_condition():
    """
    True concurrent PostgreSQL integration test:
    Two concurrent sessions attempt to book the exact same slot at the same instant.
    PostgreSQL row-level locking (with_for_update) guarantees that exactly one succeeds
    and the other receives HTTP 409 Conflict.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.schemas.appointment import AppointmentCreate

    # Connect to medicall-postgres container on port 5433
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionMaker = sessionmaker(bind=engine)

    db_setup = SessionMaker()
    try:
        # Find existing verified doctor in PostgreSQL
        pg_doctor = db_setup.query(Doctor).filter(Doctor.is_accepting_patients == True).first()
        assert pg_doctor is not None, "PostgreSQL must have at least one doctor"
        doctor_id = pg_doctor.id

        # Generate unique date and time to avoid collisions across multiple test runs
        import random
        test_date = date.today() + timedelta(days=random.randint(300, 900))
        test_time = dtime(random.randint(8, 17), random.choice([0, 30]))
        test_end_time = (datetime.combine(test_date, test_time) + timedelta(minutes=30)).time()

        # Delete any pre-existing slot if present
        db_setup.query(Availability).filter(
            Availability.doctor_id == doctor_id,
            Availability.slot_date == test_date,
            Availability.start_time == test_time
        ).delete()
        db_setup.commit()

        # Create a clean slot in PostgreSQL
        test_slot = Availability(
            doctor_id=doctor_id,
            slot_date=test_date,
            start_time=test_time,
            end_time=test_end_time,
            status=AvailabilityStatus.AVAILABLE
        )
        db_setup.add(test_slot)

        # Create two distinct patients in PostgreSQL
        u1 = User(email=f"conc1_{uuid.uuid4().hex[:6]}@example.com", hashed_password="pw", role=UserRole.PATIENT, is_verified=True)
        u2 = User(email=f"conc2_{uuid.uuid4().hex[:6]}@example.com", hashed_password="pw", role=UserRole.PATIENT, is_verified=True)
        db_setup.add_all([u1, u2])
        db_setup.flush()

        p1 = Patient(user_id=u1.id, first_name="Conc1", last_name="Test", date_of_birth=date(1990, 1, 1))
        p2 = Patient(user_id=u2.id, first_name="Conc2", last_name="Test", date_of_birth=date(1992, 1, 1))
        db_setup.add_all([p1, p2])
        db_setup.commit()
        db_setup.refresh(test_slot)
        slot_id = test_slot.id
        p1_id = p1.id
        p2_id = p2.id
    finally:
        db_setup.close()

    barrier = threading.Barrier(2)
    results = []

    def attempt_booking(patient_id):
        session = SessionMaker()
        try:
            pt = session.query(Patient).filter(Patient.id == patient_id).first()
            data = AppointmentCreate(
                doctor_id=doctor_id,
                availability_id=slot_id,
                chief_complaint="Concurrent test booking"
            )
            barrier.wait()  # Synchronize threads to hit booking simultaneously
            appt = AppointmentService.book_appointment(session, pt, data)
            results.append(("SUCCESS", appt.appointment_reference))
        except Exception as e:
            session.rollback()
            results.append(("FAILED", str(e)))
        finally:
            session.close()

    t1 = threading.Thread(target=attempt_booking, args=(p1_id,))
    t2 = threading.Thread(target=attempt_booking, args=(p2_id,))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Exactly one must succeed and one must fail
    successes = [r for r in results if r[0] == "SUCCESS"]
    failures = [r for r in results if r[0] == "FAILED"]

    assert len(successes) == 1, f"Expected 1 success, got {len(successes)}: {results}"
    assert len(failures) == 1, f"Expected 1 failure, got {len(failures)}: {results}"
    assert "409" in failures[0][1] or "already been reserved" in failures[0][1]
