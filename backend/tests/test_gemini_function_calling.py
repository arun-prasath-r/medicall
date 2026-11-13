"""
Phase 2: Comprehensive Test Suite for Gemini Function Calling,
Database Integration, Confirmation Flows, and Security Hardening.
"""

import time
import uuid
from datetime import date, datetime, time as dtime, timedelta, timezone
from unittest import mock
import pytest
from fastapi.testclient import TestClient
from google.genai import types

from app.core.config import Settings, settings
from app.core.datetime_utils import slot_to_utc_datetime
from app.models.appointment import Appointment, AppointmentStatus
from app.models.availability import Availability, AvailabilityStatus
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.ai.services.gemini_service import GeminiGenerationResult, GeminiService
from app.ai.services.safety_service import SafetyService
from app.ai.tools.confirmation import (
    ConfirmationError,
    generate_confirmation_token,
    verify_confirmation_token,
)
from app.ai.tools.dispatcher import ToolDispatcher
from app.ai.tools.doctor_tools import (
    execute_get_doctor_availability,
    execute_search_doctors,
)
from app.ai.tools.appointment_tools import (
    execute_book_appointment,
    execute_cancel_appointment,
    execute_get_my_appointments,
    execute_reschedule_appointment,
)
from app.ai.router import get_gemini_service


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def patient_auth_header(client, sample_patient):
    """Logs in sample_patient and provides authorization bearer header."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "patient.test@example.com",
        "password": "PatientPass123!"
    })
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_appointment(db_session, sample_patient, sample_doctor, sample_slot):
    """Creates a sample active appointment for test scenarios."""
    sample_slot.status = AvailabilityStatus.BOOKED
    appt = Appointment(
        appointment_reference=f"MED-TEST-{uuid.uuid4().hex[:6].upper()}",
        patient_id=sample_patient.id,
        doctor_id=sample_doctor.id,
        availability_id=sample_slot.id,
        appointment_datetime=slot_to_utc_datetime(sample_slot.slot_date, sample_slot.start_time),
        end_datetime=slot_to_utc_datetime(sample_slot.slot_date, sample_slot.end_time),
        status=AppointmentStatus.SCHEDULED,
        chief_complaint="Routine cardiology checkup"
    )
    db_session.add(appt)
    db_session.commit()
    db_session.refresh(appt)
    return appt


# ============================================================================
# 1. PRODUCTION JWT SECURITY VALIDATION TESTS
# ============================================================================

def test_production_jwt_rejects_default_dev_secrets():
    """Verify that in production mode, known insecure dev secrets are strictly rejected."""
    insecure_keys = [
        "default-dev-secret-key-must-be-replaced-in-production-env",
        "change-this-to-a-super-secret-random-32-byte-string-in-production",
        "secret",
        "changeme",
        "password",
        "123456",
    ]
    for key in insecure_keys:
        with pytest.raises(ValueError) as exc:
            Settings(ENVIRONMENT="production", JWT_SECRET_KEY=key)
        assert "Production security violation" in str(exc.value)


def test_production_jwt_enforces_minimum_32_characters():
    """Verify that in production mode, short keys (< 32 chars) are strictly rejected."""
    with pytest.raises(ValueError) as exc:
        Settings(ENVIRONMENT="production", JWT_SECRET_KEY="short-secret-key-less-than-32")
    assert "at least 32 characters long" in str(exc.value)


def test_production_jwt_accepts_strong_secret():
    """Verify that a valid 32+ character production secret is accepted."""
    strong_key = "a-very-strong-production-secret-key-with-sufficient-entropy-12345"
    s = Settings(ENVIRONMENT="production", JWT_SECRET_KEY=strong_key)
    assert s.ENVIRONMENT == "production"
    assert s.JWT_SECRET_KEY == strong_key


def test_development_mode_allows_dev_secret():
    """Verify that development mode continues to allow default dev keys for easy testing."""
    s = Settings(ENVIRONMENT="development")
    assert s.ENVIRONMENT == "development"


# ============================================================================
# 2. EMERGENCY RED-FLAG NEGATION & HISTORICAL CONTEXT TESTS
# ============================================================================

def test_emergency_negation_does_not_trigger_emergency():
    """Verify linguistic negation prevents false emergency alerts."""
    negated_statements = [
        "I do not have chest pain, just a runny nose and slight cough",
        "I don't have chest pain",
        "Patient denies chest pain or shortness of breath",
        "No chest pain or breathing issues, just scheduling a routine physical",
        "Negative for chest pain",
        "Without chest pain, only lower back discomfort",
    ]
    for text in negated_statements:
        is_emerg, conditions, _ = SafetyService.evaluate_emergency_red_flags(text)
        assert is_emerg is False, f"False positive on negated phrase: '{text}'"
        assert len(conditions) == 0


def test_emergency_rule_out_is_not_treated_as_negation():
    """Verify clinical 'rule out' statements are treated as potential emergencies, NOT negation."""
    rule_out_statements = [
        "My doctor wants to rule out a stroke.",
        "Rule out chest pain, urgent ECG review",
    ]
    for text in rule_out_statements:
        is_emerg, conditions, _ = SafetyService.evaluate_emergency_red_flags(text)
        assert is_emerg is True, f"'Rule out' must not be negated: '{text}'"


def test_emergency_historical_context_does_not_trigger_emergency():
    """Verify historical references without acute symptoms do not trigger emergency alerts."""
    historical_statements = [
        "I had chest pain 3 years ago and had a stent, today I feel fine and want a follow-up",
        "History of heart attack in 2020, completely recovered",
        "Had a stroke 5 years ago, coming in for regular checkup",
        "Past history of severe allergic reaction in 2018, no issues today",
    ]
    for text in historical_statements:
        is_emerg, conditions, _ = SafetyService.evaluate_emergency_red_flags(text)
        assert is_emerg is False, f"False positive on historical phrase: '{text}'"


def test_emergency_acute_recurrence_triggers_emergency():
    """Verify that a historical condition with acute recurrence DOES trigger emergency."""
    acute_recurrence_statements = [
        "Had heart attack 2 years ago, but now having severe chest pain again",
        "History of heart condition and currently experiencing acute chest pressure",
    ]
    for text in acute_recurrence_statements:
        is_emerg, conditions, guidance = SafetyService.evaluate_emergency_red_flags(text)
        assert is_emerg is True, f"Failed to detect acute recurrence: '{text}'"
        assert len(conditions) > 0
        assert "112" in guidance or "Emergency" in guidance


def test_genuine_acute_emergencies_trigger_immediate_escalation():
    """Verify that genuine acute medical emergencies are strictly caught."""
    emergencies = [
        "Sudden weakness on one side of face and slurred speech",
        "Coughing blood since this morning",
        "Cannot breathe and gasping for air",
        "Severe crushing chest pain radiating to my left arm",
        "Throat closing and severe allergic reaction",
        "I want to die, cannot take this pain anymore",
    ]
    for text in emergencies:
        is_emerg, conditions, guidance = SafetyService.evaluate_emergency_red_flags(text)
        assert is_emerg is True, f"Failed to detect emergency: '{text}'"
        assert len(conditions) > 0
        assert "112" in guidance
        assert "Medicall AI is an informational scheduling assistant" in guidance


# ============================================================================
# 3. DOCTOR SEARCH & AVAILABILITY TOOLS TESTS
# ============================================================================

def test_tool_search_doctors_filters_and_verifies(db_session, sample_doctor):
    """Verify execute_search_doctors returns only verified doctors and supports filtering."""
    # Search by specialty
    result = execute_search_doctors(db_session, specialty=sample_doctor.specialty)
    assert result["success"] is True
    assert result["total_found"] >= 1
    doc_ids = [d["id"] for d in result["doctors"]]
    assert str(sample_doctor.id) in doc_ids

    # Search by doctor name
    result_name = execute_search_doctors(db_session, doctor_name=sample_doctor.first_name)
    assert result_name["success"] is True
    assert any(sample_doctor.first_name in d["name"] for d in result_name["doctors"])

    # Search non-matching specialty
    result_none = execute_search_doctors(db_session, specialty="NonexistentSpecialtyXYZ")
    assert result_none["success"] is True
    assert result_none["total_found"] == 0


def test_tool_get_doctor_availability(db_session, sample_doctor, sample_slot):
    """Verify execute_get_doctor_availability returns active available slots."""
    result = execute_get_doctor_availability(
        db=db_session,
        doctor_id=str(sample_doctor.id),
        date_from=sample_slot.slot_date.isoformat(),
        date_to=sample_slot.slot_date.isoformat()
    )
    assert result["success"] is True
    assert result["doctor_name"] == f"Dr. {sample_doctor.first_name} {sample_doctor.last_name}"
    assert result["available_slots_count"] >= 1
    slot_ids = [s["slot_id"] for s in result["slots"]]
    assert str(sample_slot.id) in slot_ids


def test_tool_get_doctor_availability_invalid_uuid(db_session):
    """Verify invalid doctor UUID returns safe error."""
    result = execute_get_doctor_availability(db_session, doctor_id="not-a-valid-uuid")
    assert result["success"] is False
    assert "Invalid doctor_id" in result["error"]


# ============================================================================
# 4. APPOINTMENT OWNERSHIP & RETRIEVAL TESTS
# ============================================================================

def test_tool_get_my_appointments_isolation(db_session, sample_patient, test_appointment):
    """Verify get_my_appointments strictly returns authenticated patient's records."""
    result = execute_get_my_appointments(db_session, current_user=sample_patient.user)
    assert result["success"] is True
    assert result["total_appointments"] >= 1
    appts = result["appointments"]
    assert any(a["appointment_id"] == str(test_appointment.id) for a in appts)


def test_tool_get_my_appointments_rejects_non_patient(db_session, sample_doctor):
    """Verify accounts without a patient profile receive clean error."""
    result = execute_get_my_appointments(db_session, current_user=sample_doctor.user)
    assert result["success"] is False
    assert "patient profile" in result["error"].lower()


# ============================================================================
# 5. APPOINTMENT BOOKING CONFIRMATION FLOW TESTS
# ============================================================================

def test_tool_book_appointment_proposal_and_confirmation(db_session, sample_patient, sample_doctor):
    """
    Two-stage appointment booking test:
    Stage 1: Calling without confirmation token returns structured proposal and token.
             Database slot remains AVAILABLE.
    Stage 2: Calling with valid confirmation token commits transaction.
             Database slot changes to BOOKED.
    """
    # Create a fresh slot for this test
    slot = Availability(
        doctor_id=sample_doctor.id,
        slot_date=date.today() + timedelta(days=2),
        start_time=dtime(14, 0),
        end_time=dtime(14, 30),
        status=AvailabilityStatus.AVAILABLE
    )
    db_session.add(slot)
    db_session.commit()
    db_session.refresh(slot)

    # STAGE 1: Call without confirmation_token -> Proposal
    proposal = execute_book_appointment(
        db=db_session,
        current_user=sample_patient.user,
        doctor_id=str(sample_doctor.id),
        availability_id=str(slot.id),
        chief_complaint="Seasonal asthma follow-up"
    )

    assert proposal["requires_confirmation"] is True
    assert proposal["action"] == "book_appointment"
    token = proposal["confirmation_token"]
    assert bool(token)
    assert "Dr." in proposal["doctor_name"]

    # Verify slot is STILL AVAILABLE in the database
    db_session.refresh(slot)
    assert slot.status == AvailabilityStatus.AVAILABLE

    # STAGE 2: Call WITH confirmation_token -> Commit
    booking_result = execute_book_appointment(
        db=db_session,
        current_user=sample_patient.user,
        doctor_id=str(sample_doctor.id),
        availability_id=str(slot.id),
        chief_complaint="Seasonal asthma follow-up",
        confirmation_token=token
    )

    assert booking_result["success"] is True
    assert booking_result["status"] == AppointmentStatus.SCHEDULED.value
    assert "MED-" in booking_result["reference_code"]

    # Verify slot is now BOOKED in the database
    db_session.refresh(slot)
    assert slot.status == AvailabilityStatus.BOOKED


def test_tool_book_appointment_rejects_expired_or_tampered_token(db_session, sample_patient, sample_doctor, sample_slot):
    """Verify expired or forged confirmation tokens are rejected."""
    # Tampered token
    tampered_result = execute_book_appointment(
        db=db_session,
        current_user=sample_patient.user,
        doctor_id=str(sample_doctor.id),
        availability_id=str(sample_slot.id),
        chief_complaint="Asthma checkup",
        confirmation_token="invalid.corrupted.jwt-token-string"
    )
    assert tampered_result["success"] is False
    assert "Confirmation validation failed" in tampered_result["error"]


def test_tool_book_appointment_rejects_wrong_patient_token(db_session, sample_patient, sample_doctor, sample_slot):
    """Verify that a confirmation token generated for patient A cannot be used by patient B."""
    other_patient_id = uuid.uuid4()
    forged_token = generate_confirmation_token(
        action="book_appointment",
        patient_id=other_patient_id,
        params={"doctor_id": str(sample_doctor.id), "availability_id": str(sample_slot.id)}
    )

    result = execute_book_appointment(
        db=db_session,
        current_user=sample_patient.user,
        doctor_id=str(sample_doctor.id),
        availability_id=str(sample_slot.id),
        chief_complaint="Checkup",
        confirmation_token=forged_token
    )
    assert result["success"] is False
    assert "Security violation" in result["error"] or "does not belong" in result["error"]


# ============================================================================
# 6. APPOINTMENT CANCELLATION CONFIRMATION FLOW TESTS
# ============================================================================

def test_tool_cancel_appointment_proposal_and_confirmation(db_session, sample_patient, test_appointment):
    """Verify cancel_appointment proposal followed by confirmed cancellation."""
    # Stage 1: Proposal
    proposal = execute_cancel_appointment(
        db=db_session,
        current_user=sample_patient.user,
        appointment_id=str(test_appointment.id),
        reason="Scheduling conflict"
    )
    assert proposal["requires_confirmation"] is True
    assert proposal["action"] == "cancel_appointment"
    token = proposal["confirmation_token"]

    # Verify appointment is still SCHEDULED
    db_session.refresh(test_appointment)
    assert test_appointment.status == AppointmentStatus.SCHEDULED

    # Stage 2: Confirmed execution
    cancel_res = execute_cancel_appointment(
        db=db_session,
        current_user=sample_patient.user,
        appointment_id=str(test_appointment.id),
        confirmation_token=token
    )
    assert cancel_res["success"] is True
    assert cancel_res["status"] == AppointmentStatus.CANCELLED_PATIENT.value

    # Verify appointment is now CANCELLED_PATIENT
    db_session.refresh(test_appointment)
    assert test_appointment.status == AppointmentStatus.CANCELLED_PATIENT


# ============================================================================
# 7. APPOINTMENT RESCHEDULING CONFIRMATION FLOW TESTS
# ============================================================================

def test_tool_reschedule_appointment_proposal_and_confirmation(db_session, sample_patient, sample_doctor):
    """Verify reschedule_appointment proposal followed by confirmed execution."""
    # Setup initial booked slot & appointment
    slot1 = Availability(
        doctor_id=sample_doctor.id,
        slot_date=date.today() + timedelta(days=3),
        start_time=dtime(9, 0),
        end_time=dtime(9, 30),
        status=AvailabilityStatus.BOOKED
    )
    slot2 = Availability(
        doctor_id=sample_doctor.id,
        slot_date=date.today() + timedelta(days=3),
        start_time=dtime(11, 0),
        end_time=dtime(11, 30),
        status=AvailabilityStatus.AVAILABLE
    )
    db_session.add_all([slot1, slot2])
    db_session.commit()
    db_session.refresh(slot1)
    db_session.refresh(slot2)

    appt = Appointment(
        appointment_reference=f"MED-TEST-{uuid.uuid4().hex[:6].upper()}",
        patient_id=sample_patient.id,
        doctor_id=sample_doctor.id,
        availability_id=slot1.id,
        appointment_datetime=slot_to_utc_datetime(slot1.slot_date, slot1.start_time),
        end_datetime=slot_to_utc_datetime(slot1.slot_date, slot1.end_time),
        status=AppointmentStatus.SCHEDULED,
        chief_complaint="Initial appointment"
    )
    db_session.add(appt)
    db_session.commit()
    db_session.refresh(appt)

    # Stage 1: Proposal
    proposal = execute_reschedule_appointment(
        db=db_session,
        current_user=sample_patient.user,
        appointment_id=str(appt.id),
        new_availability_id=str(slot2.id)
    )
    assert proposal["requires_confirmation"] is True
    assert proposal["action"] == "reschedule_appointment"
    token = proposal["confirmation_token"]

    # Verify slot1 is still BOOKED and slot2 is still AVAILABLE
    db_session.refresh(slot1)
    db_session.refresh(slot2)
    assert slot1.status == AvailabilityStatus.BOOKED
    assert slot2.status == AvailabilityStatus.AVAILABLE

    # Stage 2: Confirmed execution
    resched_res = execute_reschedule_appointment(
        db=db_session,
        current_user=sample_patient.user,
        appointment_id=str(appt.id),
        new_availability_id=str(slot2.id),
        confirmation_token=token
    )
    assert resched_res["success"] is True
    assert resched_res["status"] == AppointmentStatus.RESCHEDULED.value

    # Verify slot1 freed to AVAILABLE, slot2 booked to BOOKED
    db_session.refresh(slot1)
    db_session.refresh(slot2)
    assert slot1.status == AvailabilityStatus.AVAILABLE
    assert slot2.status == AvailabilityStatus.BOOKED


# ============================================================================
# 8. MULTI-TURN GEMINI FUNCTION CALLING ORCHESTRATION TESTS
# ============================================================================

def test_multi_turn_gemini_tool_calling_loop(client, patient_auth_header, db_session, sample_doctor):
    """
    Integration test: Gemini calls search_doctors -> backend executes tool ->
    result returned in conversation context -> Gemini produces final text.
    """
    mock_service = mock.MagicMock(spec=GeminiService)
    mock_service.generate_response.return_value = GeminiGenerationResult(
        text=f"I found Dr. {sample_doctor.first_name} {sample_doctor.last_name}, a verified {sample_doctor.specialty} specialist.",
        model="gemini-3.5-flash",
        tokens_used=120,
        latency_ms=250.0,
        tools_called=["search_doctors"],
        action_proposal=None
    )

    from app.main import app
    app.dependency_overrides[get_gemini_service] = lambda: mock_service

    try:
        resp = client.post(
            "/api/v1/ai/chat",
            json={"message": f"Can you find me a doctor in {sample_doctor.specialty}?"},
            headers=patient_auth_header
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert sample_doctor.first_name in data["response"]
        assert data["metadata"]["tools_called"] == ["search_doctors"]
        assert data["metadata"]["requires_confirmation"] is False

        # Verify that tools, dispatcher, db, and current_user were passed to generate_response
        call_kwargs = mock_service.generate_response.call_args[1]
        assert "tools" in call_kwargs
        assert "tool_dispatcher" in call_kwargs
        assert "db" in call_kwargs
        assert "current_user" in call_kwargs
    finally:
        app.dependency_overrides.clear()


def test_multi_turn_gemini_action_proposal_returns_pending_confirmation(client, patient_auth_header):
    """
    Integration test: When a write tool requires confirmation, API response surfaces
    pending_confirmation object and metadata flags for frontend or voice client.
    """
    sample_token = "mock-signed-confirmation-token-xyz"
    mock_service = mock.MagicMock(spec=GeminiService)
    mock_service.generate_response.return_value = GeminiGenerationResult(
        text="I found an available slot with Dr. Sarah Smith on Friday at 10:00 AM. Would you like me to book it?",
        model="gemini-3.5-flash",
        tokens_used=135,
        latency_ms=210.0,
        tools_called=["book_appointment"],
        action_proposal={
            "requires_confirmation": True,
            "action": "book_appointment",
            "confirmation_token": sample_token,
            "doctor_name": "Dr. Sarah Smith",
            "summary": "Booking with Dr. Sarah Smith on Friday at 10:00 AM"
        }
    )

    from app.main import app
    app.dependency_overrides[get_gemini_service] = lambda: mock_service

    try:
        resp = client.post(
            "/api/v1/ai/chat",
            json={"message": "Please book an appointment with Dr. Sarah Smith tomorrow morning"},
            headers=patient_auth_header
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["metadata"]["requires_confirmation"] is True
        assert data["metadata"]["confirmation_action"] == "book_appointment"
        assert data["metadata"]["confirmation_token"] == sample_token
        assert data["pending_confirmation"] is not None
        assert data["pending_confirmation"]["action"] == "book_appointment"
    finally:
        app.dependency_overrides.clear()


def test_api_confirm_appointment_booking_success_and_replay_protection(
    client,
    patient_auth_header,
    sample_patient,
    sample_doctor,
    sample_slot,
    db_session
):
    """
    Tests the dedicated explicit confirmation endpoint POST /api/v1/ai/confirm:
    1. Generates a valid proposal token for a slot.
    2. Calls /api/v1/ai/confirm -> succeeds (200 OK), books appointment.
    3. Replays the same token -> rejected with HTTP 400.
    """
    token = generate_confirmation_token(
        action="book_appointment",
        patient_id=sample_patient.id,
        params={
            "doctor_id": str(sample_doctor.id),
            "availability_id": str(sample_slot.id),
            "chief_complaint": "Persistent migraines"
        }
    )

    # First attempt: explicit confirmation
    resp1 = client.post(
        "/api/v1/ai/confirm",
        json={"confirmation_token": token},
        headers=patient_auth_header
    )
    assert resp1.status_code == 200, resp1.text
    data1 = resp1.json()
    assert data1["success"] is True
    assert data1["action"] == "book_appointment"
    assert data1["reference_code"] is not None
    assert "successfully confirmed" in data1["message"].lower()

    # Replay attempt: must fail with HTTP 400
    resp2 = client.post(
        "/api/v1/ai/confirm",
        json={"confirmation_token": token},
        headers=patient_auth_header
    )
    assert resp2.status_code == 400
    assert "already been used" in resp2.json()["detail"].lower()
