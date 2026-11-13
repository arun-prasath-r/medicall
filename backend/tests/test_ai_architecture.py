import pytest
from app.ai.ai_service import AIService
from app.ai.safety_guardrails import SafetyGuardrails, CLINICAL_DISCLAIMER
from app.ai.schemas import (
    SymptomAssessmentRequest,
    TriageClassificationRequest,
    DoctorMatchingRequest,
    ReportSummaryRequest,
    UrgencyLevel
)
from app.models.doctor import Doctor
import uuid
from decimal import Decimal


def test_safety_guardrails_cardiac_red_flag_triggers_emergency():
    """Verify that acute cardiac symptoms deterministically trigger EMERGENCY without LLM."""
    emergency_text = "Patient experiencing sudden severe chest pain radiating to left arm and crushing pressure."
    is_emergency, conditions, guidance = SafetyGuardrails.evaluate_emergency_red_flags(emergency_text)

    assert is_emergency is True
    assert "Suspected Acute Coronary Syndrome" in conditions
    assert "911" in guidance or "Emergency" in guidance


def test_safety_guardrails_stroke_red_flag_triggers_emergency():
    """Verify that acute stroke symptoms (FAST) trigger immediate emergency advice."""
    emergency_text = "Sudden slurred speech and right side face drooping noticed 10 minutes ago."
    is_emergency, conditions, guidance = SafetyGuardrails.evaluate_emergency_red_flags(emergency_text)

    assert is_emergency is True
    assert "Suspected Acute Cerebrovascular Event (Stroke)" in conditions


def test_safety_guardrails_routine_symptoms_not_flagged():
    """Verify that non-emergency symptoms pass through guardrails safely."""
    routine_text = "Mild seasonal allergy symptoms, runny nose and occasional sneeze for 3 days."
    is_emergency, conditions, guidance = SafetyGuardrails.evaluate_emergency_red_flags(routine_text)

    assert is_emergency is False
    assert len(conditions) == 0
    assert guidance == ""


def test_ai_service_symptom_assessment_emergency_escalation():
    """Verify AIService immediately aborts scheduling and escalates when red-flag is present."""
    service = AIService()
    req = SymptomAssessmentRequest(
        symptoms="I cannot breathe and my chest hurts severely with radiating arm pain",
        severity_scale=10
    )
    resp = service.assess_symptoms(req)

    assert resp.is_emergency is True
    assert resp.urgency_level == UrgencyLevel.EMERGENCY
    assert "Emergency Medicine" in resp.possible_specialties
    assert CLINICAL_DISCLAIMER in resp.clinical_disclaimer


def test_ai_service_symptom_assessment_routine_flow():
    """Verify AIService analyzes routine symptoms safely with non-diagnostic disclaimer."""
    service = AIService()
    req = SymptomAssessmentRequest(
        symptoms="Mild knee joint stiffness after morning jogging.",
        duration_days=5,
        severity_scale=3,
        patient_age=34
    )
    resp = service.assess_symptoms(req)

    assert resp.is_emergency is False
    assert resp.urgency_level in (UrgencyLevel.ROUTINE, UrgencyLevel.MODERATE)
    assert any("Orthopedics" in s or "General Medicine" in s for s in resp.possible_specialties)
    assert len(resp.suggested_questions_for_doctor) > 0
    assert CLINICAL_DISCLAIMER in resp.clinical_disclaimer


def test_ai_service_triage_classification():
    """Verify triage classification scores outpatient symptoms correctly."""
    service = AIService()
    req = TriageClassificationRequest(chief_complaint="Routine annual physical examination.")
    resp = service.classify_triage(req)

    assert resp.urgency_level == UrgencyLevel.ROUTINE
    assert resp.triage_score >= 3
    assert CLINICAL_DISCLAIMER in resp.clinical_disclaimer


def test_ai_service_doctor_matching():
    """Verify doctor matching matches practitioner specialties against symptoms."""
    service = AIService()
    fake_doctors = [
        Doctor(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            first_name="Arthur",
            last_name="Conan",
            license_number="LIC-1",
            specialty="Cardiology",
            qualifications="MD",
            consultation_fee=Decimal("150.00")
        ),
        Doctor(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            first_name="Jane",
            last_name="Doe",
            license_number="LIC-2",
            specialty="Dermatology",
            qualifications="MD",
            consultation_fee=Decimal("120.00")
        )
    ]

    req = DoctorMatchingRequest(symptom_summary="High blood pressure and palpitations", preferred_specialty="Cardiology")
    resp = service.match_doctors(req, fake_doctors)

    assert resp.matched_specialty == "Cardiology"
    assert len(resp.recommendations) > 0
    assert resp.recommendations[0].specialty == "Cardiology"
    assert resp.recommendations[0].match_score > resp.recommendations[1].match_score

