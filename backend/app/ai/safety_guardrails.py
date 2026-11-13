import re
from typing import Tuple, List
from app.core.config import settings
from app.ai.services.safety_service import (
    CLINICAL_DISCLAIMER,
    RED_FLAG_PATTERNS,
    SafetyService,
)


class SafetyGuardrails:
    """
    Deterministic clinical safety guardrails for Medicall AI.
    Executes BEFORE any LLM processing to safeguard patients from life-threatening delays.
    Delegates to SafetyService for consistent, negation-aware clinical emergency evaluation.
    """

    @staticmethod
    def evaluate_emergency_red_flags(text: str) -> Tuple[bool, List[str], str]:
        return SafetyService.evaluate_emergency_red_flags(text)

    @staticmethod
    def get_clinical_disclaimer() -> str:
        return SafetyService.get_clinical_disclaimer()

    @staticmethod
    def sanitize_patient_input(text: str) -> str:
        return SafetyService.sanitize_user_input(text)

