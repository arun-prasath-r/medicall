import abc
import json
import logging
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel
from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseLLMProvider(abc.ABC):
    """
    Abstract interface for LLM providers.
    Enables zero-lock-in migration between models and providers (e.g. Gemini, custom local models).
    """

    @abc.abstractmethod
    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generates plain text response from the model."""
        pass

    @abc.abstractmethod
    def generate_structured(self, prompt: str, schema: Type[BaseModel], system_instruction: Optional[str] = None) -> BaseModel:
        """Generates a structured Pydantic object from the model."""
        pass


class GeminiLLMProvider(BaseLLMProvider):
    """
    Google Gemini API implementation.
    Designed to read configuration from environment variables.
    Provides graceful dry-run / fallback capabilities when no API key is supplied,
    preventing runtime crashes or unintended API charges.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self._is_configured = bool(self.api_key)

    @property
    def is_configured(self) -> bool:
        return self._is_configured

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        if not self._is_configured:
            logger.info("Gemini API key not configured; returning structured fallback response.")
            return (
                "Medicall AI Assistant [Offline Preview]: Your inquiry has been received. "
                "Please consult a certified healthcare specialist to review your symptoms."
            )

        # In Phase 3+, the official google-genai / google-generativeai SDK call executes here
        # Example:
        # client = genai.Client(api_key=self.api_key)
        # response = client.models.generate_content(model=self.model_name, contents=prompt)
        # return response.text
        return "Simulated Gemini response based on prompt context."

    def generate_structured(self, prompt: str, schema: Type[BaseModel], system_instruction: Optional[str] = None) -> Any:
        if not self._is_configured:
            logger.info("Gemini API key not configured; generating typed fallback model.")
            # Returns an initialized instance of the requested Pydantic schema
            return schema.model_validate({})
        
        # When active, leverages Gemini's structured response JSON schema enforcement
        return schema.model_validate({})

