import logging
from typing import Optional
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.prompts.healthcare_assistant import (
    HEALTHCARE_ASSISTANT_SYSTEM_INSTRUCTION,
    format_assistant_prompt,
)
from app.ai.schemas import (
    AIChatRequest,
    AIChatResponse,
    AIConfirmActionRequest,
    AIConfirmActionResponse,
    AIMetadata,
    UrgencyLevel,
)
from app.ai.services.gemini_service import (
    GeminiAuthenticationError,
    GeminiConfigurationError,
    GeminiError,
    GeminiModelNotFoundError,
    GeminiService,
    GeminiServiceUnavailableError,
    GeminiTimeoutError,
)
from app.ai.services.safety_service import SafetyService
from app.ai.tools import MEDICALL_GEMINI_TOOL, ToolDispatcher
from app.ai.tools.appointment_tools import (
    _require_patient_user,
    execute_book_appointment,
    execute_cancel_appointment,
    execute_reschedule_appointment,
)
from app.core.dependencies import get_current_user, get_db
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Clinical Assistant"])

# Singleton / Shared instance
_default_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Dependency provider for GeminiService (easily mockable in tests)."""
    global _default_gemini_service
    if _default_gemini_service is None:
        _default_gemini_service = GeminiService()
    return _default_gemini_service


@router.post(
    "/chat",
    response_model=AIChatResponse,
    summary="AI Voice & Text Healthcare Triage Chat",
    description=(
        "Processes patient health inquiries with deterministic emergency detection, "
        "medical safety guardrails, Gemini function calling, and verified healthcare services integration."
    )
)
def chat_with_ai(
    request: AIChatRequest,
    current_user: User = Depends(get_current_user),
    service: GeminiService = Depends(get_gemini_service),
    db: Session = Depends(get_db)
) -> AIChatResponse:
    """
    Primary conversational healthcare triage endpoint.
    1. Validates authenticated user.
    2. Runs deterministic emergency red-flag analysis on patient input.
    3. Escalates immediately if acute life-threatening symptoms are detected.
    4. Invokes Google Gemini with verified healthcare tools and bounded loop orchestration.
    5. Validates model output safety and returns structured response with disclaimers.
    """
    raw_message = request.message

    # STEP 1: Deterministic Red-Flag Emergency Triage
    is_emergency, conditions, emergency_guidance = SafetyService.evaluate_emergency_red_flags(raw_message)

    if is_emergency:
        logger.warning(
            "User %s triggered medical emergency red-flag conditions: %s",
            current_user.id,
            conditions
        )
        return AIChatResponse(
            response=(
                f"⚠️ MEDICAL EMERGENCY DIRECTIVE:\n\n{emergency_guidance}\n\n"
                "Please do not delay seeking immediate clinical care. Medicall online appointment scheduling "
                "is not equipped for life-threatening acute medical emergencies."
            ),
            urgency_level=UrgencyLevel.EMERGENCY,
            is_emergency=True,
            emergency_guidance=emergency_guidance,
            disclaimer=SafetyService.get_clinical_disclaimer(),
            metadata=AIMetadata(
                model="deterministic-safety-guardrail",
                tokens_used=0,
                latency_ms=0.0,
                is_emergency=True,
                matched_red_flags=conditions
            ),
            success=True
        )

    # STEP 2: Sanitize User Input
    clean_message = SafetyService.sanitize_user_input(raw_message)

    # Format history turns if present
    history_dicts = None
    if request.conversation_history:
        history_dicts = [
            {"role": turn.role, "content": turn.content}
            for turn in request.conversation_history
        ]

    prompt = format_assistant_prompt(
        user_message=clean_message,
        conversation_history=history_dicts,
        confirmation_token=request.confirmation_token
    )

    # STEP 3: Execute Gemini AI Request with Real-Time Function Calling Tools
    try:
        result = service.generate_response(
            prompt=prompt,
            system_instruction=HEALTHCARE_ASSISTANT_SYSTEM_INSTRUCTION,
            temperature=0.2,
            max_output_tokens=1024,
            tools=[MEDICALL_GEMINI_TOOL],
            tool_dispatcher=ToolDispatcher,
            db=db,
            current_user=current_user
        )

        # STEP 4: Post-Generation Output Guardrail Validation
        verified_output = SafetyService.verify_output_safety(result.text)

        action_prop = result.action_proposal
        has_confirmation_req = bool(action_prop and action_prop.get("requires_confirmation"))

        return AIChatResponse(
            response=verified_output,
            urgency_level=UrgencyLevel.ROUTINE,
            is_emergency=False,
            emergency_guidance=None,
            disclaimer=SafetyService.get_clinical_disclaimer(),
            metadata=AIMetadata(
                model=result.model,
                tokens_used=result.tokens_used,
                latency_ms=result.latency_ms,
                is_emergency=False,
                matched_red_flags=None,
                tools_called=result.tools_called,
                requires_confirmation=has_confirmation_req,
                confirmation_action=action_prop.get("action") if action_prop else None,
                confirmation_token=action_prop.get("confirmation_token") if action_prop else None,
            ),
            pending_confirmation=action_prop if has_confirmation_req else None,
            success=True
        )

    except GeminiServiceUnavailableError as sue:
        logger.error("Gemini service unavailable for user %s: %s", current_user.id, sue)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Gemini AI service is currently experiencing high demand or is temporarily unavailable. Please try again shortly or consult a practitioner directly."
        ) from sue

    except GeminiAuthenticationError as ae:
        logger.critical("Gemini authentication failure: %s", ae)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service configuration error. Please contact clinic administrator."
        ) from ae

    except GeminiModelNotFoundError as mnf:
        logger.error("Gemini model not found: %s", mnf)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configured AI model is not available."
        ) from mnf

    except GeminiTimeoutError as te:
        logger.error("Gemini timeout: %s", te)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The AI service request timed out. Please try again."
        ) from te

    except GeminiConfigurationError as gce:
        logger.error("Gemini unconfigured: %s", gce)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured on this server."
        ) from gce

    except GeminiError as ge:
        logger.error("Gemini general error: %s", ge)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while communicating with the AI service."
        ) from ge


@router.get(
    "/status",
    summary="Check AI Provider Status",
    description="Returns current Google Gemini connection and model availability status."
)
def get_ai_status(
    current_user: User = Depends(get_current_user),
    service: GeminiService = Depends(get_gemini_service)
):
    """Admin and practitioner inspection of Gemini integration health."""
    return service.health_check()


@router.post(
    "/confirm",
    response_model=AIConfirmActionResponse,
    summary="Explicit Patient Appointment Confirmation",
    description=(
        "Executes a proposed appointment operation (booking, cancellation, rescheduling) "
        "using an explicit patient-confirmed single-use cryptographic confirmation token."
    )
)
def confirm_appointment_action(
    request: AIConfirmActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> AIConfirmActionResponse:
    """
    Explicit, deterministic execution of appointment write actions.
    1. Validates that the caller is an authenticated patient.
    2. Inspects token to identify proposed action and bound parameters.
    3. Calls the verified tool with the confirmation token (enforcing cryptographic validity,
       ownership binding, expiration, single-use nonce tracking, and row-level locking).
    4. Commits the transaction and returns structured completion confirmation.
    """
    # 1. Require authenticated patient
    try:
        patient = _require_patient_user(current_user)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(ve)
        )

    # 2. Inspect token payload for action routing
    raw_token = request.confirmation_token.strip()
    try:
        unverified_payload = jwt.decode(
            raw_token,
            options={"verify_signature": False}
        )
        action = unverified_payload.get("action")
        params = unverified_payload.get("params", {})
    except Exception as e:
        logger.warning("Invalid confirmation token structure presented: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The confirmation token is corrupted or has an invalid structure."
        )

    # 3. Route to dedicated tool with confirmation token (which verifies signatures, patient ownership & single-use)
    if action == "book_appointment":
        result = execute_book_appointment(
            db=db,
            current_user=current_user,
            doctor_id=params.get("doctor_id", ""),
            availability_id=params.get("availability_id", ""),
            chief_complaint=params.get("chief_complaint", "Consultation"),
            confirmation_token=raw_token
        )
    elif action == "cancel_appointment":
        result = execute_cancel_appointment(
            db=db,
            current_user=current_user,
            appointment_id=params.get("appointment_id", ""),
            reason=params.get("reason"),
            confirmation_token=raw_token
        )
    elif action == "reschedule_appointment":
        result = execute_reschedule_appointment(
            db=db,
            current_user=current_user,
            appointment_id=params.get("appointment_id", ""),
            new_availability_id=params.get("new_availability_id", ""),
            confirmation_token=raw_token
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported confirmation action: '{action}'."
        )

    # 4. Handle result
    if not result.get("success"):
        error_detail = result.get("error", "The appointment operation could not be confirmed.")
        logger.warning("Action confirmation rejected for user %s: %s", current_user.id, error_detail)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail
        )

    return AIConfirmActionResponse(
        success=True,
        action=action,
        message=result.get("message", "Appointment operation successfully completed."),
        appointment_id=result.get("appointment_id"),
        reference_code=result.get("reference_code"),
        details=result
    )


