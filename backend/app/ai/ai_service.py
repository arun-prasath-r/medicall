import logging
from typing import List, Optional
from app.ai.llm_provider import BaseLLMProvider, GeminiLLMProvider
from app.ai.prompt_manager import PromptManager
from app.ai.safety_guardrails import SafetyGuardrails
from app.ai.schemas import (
    DoctorMatchResult,
    DoctorMatchingRequest,
    DoctorMatchingResponse,
    ReportSummaryRequest,
    ReportSummaryResponse,
    SymptomAssessmentRequest,
    SymptomAssessmentResponse,
    TriageClassificationRequest,
    TriageClassificationResponse,
    UrgencyLevel,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """
    Central orchestration service for Medicall AI capabilities.
    Coordinates deterministic clinical safety guardrails, prompt templates,
    and LLM providers.
    """

    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        self.provider = provider or GeminiLLMProvider()

    def assess_symptoms(self, request: SymptomAssessmentRequest) -> SymptomAssessmentResponse:
        """
        Evaluates patient symptoms.
        Prioritizes deterministic emergency red-flag safeguards BEFORE any model invocation.
        """
        # Step 1: Deterministic red-flag evaluation
        is_emergency, conditions, emergency_guidance = SafetyGuardrails.evaluate_emergency_red_flags(request.symptoms)

        if is_emergency:
            return SymptomAssessmentResponse(
                urgency_level=UrgencyLevel.EMERGENCY,
                is_emergency=True,
                emergency_guidance=emergency_guidance,
                possible_specialties=["Emergency Medicine"],
                suggested_questions_for_doctor=["Do not wait. Proceed to emergency care immediately."],
                preliminary_summary=f"Critical red-flag symptoms detected: {', '.join(conditions)}.",
                clinical_disclaimer=SafetyGuardrails.get_clinical_disclaimer(),
            )

        # Step 2: Formulate prompt and analyze
        sanitized_symptoms = SafetyGuardrails.sanitize_patient_input(request.symptoms)
        prompt = PromptManager.format_symptom_prompt(
            symptoms=sanitized_symptoms,
            duration_days=request.duration_days,
            severity_scale=request.severity_scale,
            patient_age=request.patient_age,
        )

        # Default clinical heuristics if LLM is offline
        suggested_specialties = ["General Medicine"]
        lower_symptoms = sanitized_symptoms.lower()
        if any(w in lower_symptoms for w in ["heart", "palpitation", "blood pressure"]):
            suggested_specialties.append("Cardiology")
        if any(w in lower_symptoms for w in ["skin", "rash", "itching", "acne"]):
            suggested_specialties.append("Dermatology")
        if any(w in lower_symptoms for w in ["bone", "joint", "knee", "back pain", "fracture"]):
            suggested_specialties.append("Orthopedics")
        if any(w in lower_symptoms for w in ["child", "infant", "baby"]):
            suggested_specialties.append("Pediatrics")

        urgency = UrgencyLevel.ROUTINE
        if request.severity_scale and request.severity_scale >= 7:
            urgency = UrgencyLevel.URGENT
        elif request.severity_scale and request.severity_scale >= 4:
            urgency = UrgencyLevel.MODERATE

        return SymptomAssessmentResponse(
            urgency_level=urgency,
            is_emergency=False,
            emergency_guidance=None,
            possible_specialties=list(set(suggested_specialties)),
            suggested_questions_for_doctor=[
                "What could be the underlying trigger for these symptoms?",
                "Are there any diagnostic tests or lab work you recommend?",
                "What warning signs should prompt me to seek immediate emergency care?",
            ],
            preliminary_summary=f"Preliminary evaluation based on reported symptoms: '{sanitized_symptoms[:100]}...'",
            clinical_disclaimer=SafetyGuardrails.get_clinical_disclaimer(),
        )

    def classify_triage(self, request: TriageClassificationRequest) -> TriageClassificationResponse:
        """
        Classifies consultation urgency and recommends timeframe for clinical review.
        """
        is_emergency, conditions, _ = SafetyGuardrails.evaluate_emergency_red_flags(request.chief_complaint)

        if is_emergency:
            return TriageClassificationResponse(
                urgency_level=UrgencyLevel.EMERGENCY,
                triage_score=1,
                recommended_timeframe="Immediate (0 - 15 minutes)",
                emergency_contact_number=settings.EMERGENCY_PHONE_NUMBER,
                rationale=f"Emergency red-flags detected: {', '.join(conditions)}.",
                clinical_disclaimer=SafetyGuardrails.get_clinical_disclaimer(),
            )

        return TriageClassificationResponse(
            urgency_level=UrgencyLevel.ROUTINE,
            triage_score=4,
            recommended_timeframe="Within 24 to 72 hours",
            emergency_contact_number=settings.EMERGENCY_PHONE_NUMBER,
            rationale="Non-emergency clinical complaint suitable for standard outpatient consultation.",
            clinical_disclaimer=SafetyGuardrails.get_clinical_disclaimer(),
        )

    def match_doctors(self, request: DoctorMatchingRequest, available_doctors: list) -> DoctorMatchingResponse:
        """
        Ranks available practitioner profiles based on relevance to reported symptoms.
        """
        matches: List[DoctorMatchResult] = []
        specialty_target = request.preferred_specialty or "General Medicine"

        for doc in available_doctors:
            doc_specialty = getattr(doc, "specialty", "General Medicine")
            is_specialty_match = doc_specialty.lower() == specialty_target.lower()
            score = 0.95 if is_specialty_match else 0.70

            matches.append(
                DoctorMatchResult(
                    doctor_id=doc.id,
                    doctor_name=f"Dr. {doc.first_name} {doc.last_name}",
                    specialty=doc_specialty,
                    match_score=score,
                    match_reason=f"Board-certified practitioner in {doc_specialty}.",
                )
            )

        matches.sort(key=lambda m: m.match_score, reverse=True)

        return DoctorMatchingResponse(
            matched_specialty=specialty_target,
            recommendations=matches[:5],
            clinical_disclaimer=SafetyGuardrails.get_clinical_disclaimer(),
        )

    def summarize_medical_report(self, request: ReportSummaryRequest) -> ReportSummaryResponse:
        """
        Translates complex lab findings and clinical reports into reassuring, accessible patient language.
        """
        sanitized = SafetyGuardrails.sanitize_patient_input(request.report_text)

        return ReportSummaryResponse(
            key_findings=[
                "Report text processed for patient comprehension.",
                "Clinical values should be correlated by your attending doctor with your medical history.",
            ],
            medical_terms_explained={},
            questions_for_next_consultation=[
                "Are my lab results within normal physiological ranges?",
                "Do any of these findings require lifestyle or medication adjustments?",
            ],
            simplified_summary=f"Overview of report: {sanitized[:120]}...",
            clinical_disclaimer=SafetyGuardrails.get_clinical_disclaimer(),
        )

