import enum
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class UrgencyLevel(str, enum.Enum):
    ROUTINE = "ROUTINE"
    MODERATE = "MODERATE"
    URGENT = "URGENT"
    EMERGENCY = "EMERGENCY"


# ============================================================================
# 1. AI CHAT SCHEMAS (Medicall AI Assistant Foundation)
# ============================================================================

class AIChatMessage(BaseModel):
    role: str = Field(description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(min_length=1, max_length=2000, description="Message text")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        clean_role = v.strip().lower()
        if clean_role not in ("user", "assistant", "system"):
            raise ValueError("Role must be 'user', 'assistant', or 'system'")
        return clean_role

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        clean_content = v.strip()
        if not clean_content:
            raise ValueError("Message content cannot be empty or whitespace only")
        return clean_content


class AIChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
        description="Patient clinical question or symptom inquiry (1 - 2000 characters)"
    )
    conversation_history: Optional[List[AIChatMessage]] = Field(
        default=None,
        max_length=10,
        description="Optional prior conversation turns for multi-turn context (maximum 10 turns)"
    )
    confirmation_token: Optional[str] = Field(
        default=None,
        description="Optional cryptographically signed confirmation token from a previous proposal turn"
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        clean_msg = v.strip()
        if not clean_msg:
            raise ValueError("User message cannot be empty or contain only whitespace.")
        return clean_msg


class AIMetadata(BaseModel):
    model: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None
    is_emergency: bool = False
    matched_red_flags: Optional[List[str]] = None
    tools_called: Optional[List[str]] = None
    requires_confirmation: bool = False
    confirmation_action: Optional[str] = None
    confirmation_token: Optional[str] = None


class AIChatResponse(BaseModel):
    response: str
    urgency_level: UrgencyLevel = UrgencyLevel.ROUTINE
    is_emergency: bool = False
    emergency_guidance: Optional[str] = None
    disclaimer: str
    metadata: AIMetadata
    pending_confirmation: Optional[dict] = None
    success: bool = True
    error_message: Optional[str] = None


class AIConfirmActionRequest(BaseModel):
    confirmation_token: str = Field(
        min_length=10,
        description="Cryptographically signed confirmation token from a previous proposal turn"
    )

    @field_validator("confirmation_token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Confirmation token cannot be empty.")
        return clean


class AIConfirmActionResponse(BaseModel):
    success: bool
    action: str
    message: str
    appointment_id: Optional[str] = None
    reference_code: Optional[str] = None
    details: Optional[dict] = None
    error: Optional[str] = None


# ============================================================================
# 2. LEGACY / EXTENDED WORKFLOW SCHEMAS (Preserved Intact)
# ============================================================================

class ChatMessage(BaseModel):
    role: str = Field(description="'user' or 'assistant' or 'system'")
    content: str


class ChatAssistantRequest(BaseModel):
    messages: List[ChatMessage]
    patient_id: Optional[uuid.UUID] = None


class ChatAssistantResponse(BaseModel):
    reply: str
    detected_intent: Optional[str] = None
    is_emergency: bool = False
    suggested_actions: List[str] = Field(default_factory=list)
    clinical_disclaimer: str


class SymptomAssessmentRequest(BaseModel):
    symptoms: str = Field(min_length=3, description="Patient description of current symptoms")
    duration_days: Optional[int] = Field(ge=0, default=None)
    severity_scale: Optional[int] = Field(ge=1, le=10, default=None, description="Self-reported 1-10 severity")
    patient_age: Optional[int] = Field(ge=0, le=130, default=None)
    existing_conditions: Optional[List[str]] = Field(default_factory=list)


class SymptomAssessmentResponse(BaseModel):
    urgency_level: UrgencyLevel
    is_emergency: bool = False
    emergency_guidance: Optional[str] = None
    possible_specialties: List[str] = Field(default_factory=list)
    suggested_questions_for_doctor: List[str] = Field(default_factory=list)
    preliminary_summary: str
    clinical_disclaimer: str


class TriageClassificationRequest(BaseModel):
    chief_complaint: str = Field(min_length=3)
    patient_id: Optional[uuid.UUID] = None
    vital_signs_notes: Optional[str] = None


class TriageClassificationResponse(BaseModel):
    urgency_level: UrgencyLevel
    triage_score: int = Field(ge=1, le=5, description="1=Immediate resuscitation, 5=Non-urgent")
    recommended_timeframe: str
    emergency_contact_number: str
    rationale: str
    clinical_disclaimer: str


class DoctorMatchingRequest(BaseModel):
    symptom_summary: str = Field(min_length=3)
    preferred_specialty: Optional[str] = None
    max_fee: Optional[float] = None


class DoctorMatchResult(BaseModel):
    doctor_id: uuid.UUID
    doctor_name: str
    specialty: str
    match_score: float = Field(ge=0.0, le=1.0)
    match_reason: str


class DoctorMatchingResponse(BaseModel):
    matched_specialty: str
    recommendations: List[DoctorMatchResult] = Field(default_factory=list)
    clinical_disclaimer: str


class ReportSummaryRequest(BaseModel):
    report_text: str = Field(min_length=10, description="Raw clinical report or lab findings")
    summary_format: str = Field(default="patient_friendly", description="patient_friendly | bulleted | key_findings")


class ReportSummaryResponse(BaseModel):
    key_findings: List[str] = Field(default_factory=list)
    medical_terms_explained: dict = Field(default_factory=dict)
    questions_for_next_consultation: List[str] = Field(default_factory=list)
    simplified_summary: str
    clinical_disclaimer: str
