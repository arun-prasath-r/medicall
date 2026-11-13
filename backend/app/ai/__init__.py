# AI Foundation Exports
from app.ai.router import router as ai_router
from app.ai.schemas import (
    AIChatMessage,
    AIChatRequest,
    AIChatResponse,
    AIMetadata,
    ChatMessage,
    ChatAssistantRequest,
    ChatAssistantResponse,
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
from app.ai.services.gemini_service import (
    GeminiAuthenticationError,
    GeminiConfigurationError,
    GeminiError,
    GeminiGenerationResult,
    GeminiModelNotFoundError,
    GeminiService,
    GeminiServiceUnavailableError,
    GeminiTimeoutError,
)
from app.ai.services.safety_service import CLINICAL_DISCLAIMER, SafetyService

# Legacy / Extended workflow adapters (preserved for test compatibility)
from app.ai.ai_service import AIService
from app.ai.llm_provider import BaseLLMProvider, GeminiLLMProvider
from app.ai.prompt_manager import PromptManager
from app.ai.safety_guardrails import SafetyGuardrails

__all__ = [
    # Router
    "ai_router",
    # Core Schemas
    "AIChatRequest",
    "AIChatResponse",
    "AIMetadata",
    "AIChatMessage",
    "UrgencyLevel",
    # Core Services
    "GeminiService",
    "GeminiGenerationResult",
    "GeminiError",
    "GeminiConfigurationError",
    "GeminiAuthenticationError",
    "GeminiModelNotFoundError",
    "GeminiServiceUnavailableError",
    "GeminiTimeoutError",
    "SafetyService",
    "CLINICAL_DISCLAIMER",
    # Legacy / Extended Workflow components
    "AIService",
    "SafetyGuardrails",
    "PromptManager",
    "BaseLLMProvider",
    "GeminiLLMProvider",
    "SymptomAssessmentRequest",
    "SymptomAssessmentResponse",
    "TriageClassificationRequest",
    "TriageClassificationResponse",
    "DoctorMatchingRequest",
    "DoctorMatchingResponse",
    "ReportSummaryRequest",
    "ReportSummaryResponse",
    "ChatMessage",
    "ChatAssistantRequest",
    "ChatAssistantResponse",
    "DoctorMatchResult",
]
