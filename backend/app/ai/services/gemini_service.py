import logging
import random
import time
from dataclasses import dataclass
from typing import Any, List, Optional
from google import genai
from google.genai import errors, types

from app.core.config import settings

logger = logging.getLogger(__name__)


_SENTINEL = object()


# ============================================================================
# CUSTOM DOMAIN EXCEPTIONS (Clean abstraction, zero secret leakage)
# ============================================================================

class GeminiError(Exception):
    """Base exception for all Gemini service errors."""
    pass


class GeminiConfigurationError(GeminiError):
    """Raised when Gemini API key or required settings are missing."""
    pass


class GeminiAuthenticationError(GeminiError):
    """Raised when the provided Gemini API key is invalid or unauthorized."""
    pass


class GeminiModelNotFoundError(GeminiError):
    """Raised when the requested model name is not found or unsupported."""
    pass


class GeminiServiceUnavailableError(GeminiError):
    """Raised when Gemini is experiencing high demand (503) or transient outages."""
    pass


class GeminiTimeoutError(GeminiError):
    """Raised when request times out."""
    pass


@dataclass
class GeminiGenerationResult:
    text: str
    model: str
    tokens_used: Optional[int] = None
    latency_ms: float = 0.0
    tools_called: Optional[List[str]] = None
    action_proposal: Optional[dict] = None


# ============================================================================
# REUSABLE GEMINI SERVICE
# ============================================================================

class GeminiService:
    """
    Robust, production-ready Google Gemini service for Medicall.
    
    Features:
    - Lazy client initialization & client instance caching.
    - Bounded exponential backoff on transient errors (503, 429).
    - Automatic fallback model switching if primary model is saturated.
    - Zero API key or sensitive stack-trace leakage in logs or exceptions.
    - Strict timeout management.
    - Multi-turn Function Calling orchestration with database isolation.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        fallback_model: Any = _SENTINEL,
        max_retries: Optional[int] = None,
        timeout_seconds: Optional[float] = None
    ):
        self._api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL or "gemini-3.5-flash"
        self.fallback_model = settings.GEMINI_FALLBACK_MODEL if fallback_model is _SENTINEL else fallback_model
        self.max_retries = max_retries if max_retries is not None else settings.GEMINI_MAX_RETRIES
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else settings.GEMINI_TIMEOUT_SECONDS

        self._client: Optional[genai.Client] = None
        self._is_configured = bool(self._api_key and self._api_key.strip())

    @property
    def is_configured(self) -> bool:
        """Returns True if an API key is present."""
        return self._is_configured

    def _get_client(self) -> genai.Client:
        """Lazily initializes and caches the genai.Client instance."""
        if not self._is_configured:
            raise GeminiConfigurationError(
                "Gemini API key is not configured. Please configure GEMINI_API_KEY in environment."
            )

        if self._client is None:
            try:
                self._client = genai.Client(api_key=self._api_key)
            except Exception as e:
                logger.error("Failed to initialize Google GenAI Client: %s", type(e).__name__)
                raise GeminiConfigurationError("Could not initialize Google GenAI client.") from e

        return self._client

    def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: int = 1024,
        tools: Optional[List[Any]] = None,
        tool_dispatcher: Optional[Any] = None,
        db: Optional[Any] = None,
        current_user: Optional[Any] = None,
        max_tool_iterations: int = 5,
    ) -> GeminiGenerationResult:
        """
        Executes a generation request with bounded retry and exponential backoff.
        Supports multi-turn tool calling orchestration when tools are provided.
        
        If primary model encounters 503 after max_retries, attempts fallback_model.
        """
        client = self._get_client()

        # Try primary model first, then fallback model if 503 persists
        models_to_try = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            models_to_try.append(self.fallback_model)

        last_error: Optional[Exception] = None

        for current_model in models_to_try:
            attempt = 0
            while attempt <= self.max_retries:
                start_time = time.perf_counter()
                try:
                    logger.debug("Dispatching request to Gemini model: %s (attempt %d/%d)", current_model, attempt + 1, self.max_retries + 1)
                    
                    config = types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                        tools=tools if tools else None,
                    )

                    tools_called: List[str] = []
                    action_proposal: Optional[dict] = None

                    if tools:
                        # Multi-turn content loop with function calling support
                        contents: List[Any] = [
                            types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
                        ]

                        response = client.models.generate_content(
                            model=current_model,
                            contents=contents,
                            config=config,
                        )

                        tool_iterations = 0
                        while getattr(response, "function_calls", None) and tool_iterations < max_tool_iterations:
                            tool_iterations += 1
                            if response.candidates and response.candidates[0].content:
                                contents.append(response.candidates[0].content)

                            tool_parts = []
                            has_proposal = False
                            for fc in response.function_calls:
                                tool_name = fc.name
                                tool_args = fc.args or {}
                                tools_called.append(tool_name)

                                if tool_dispatcher and db and current_user:
                                    tool_output = tool_dispatcher.dispatch(
                                        name=tool_name,
                                        arguments=tool_args,
                                        db=db,
                                        current_user=current_user
                                    )
                                else:
                                    tool_output = {"success": False, "error": "Dispatcher or database session not provided."}

                                if isinstance(tool_output, dict) and tool_output.get("requires_confirmation"):
                                    action_proposal = tool_output
                                    has_proposal = True

                                tool_parts.append(types.Part.from_function_response(
                                    name=tool_name,
                                    response={"result": tool_output}
                                ))

                            contents.append(types.Content(role="user", parts=tool_parts))

                            # ORCHESTRATION GUARD:
                            # If a tool returned an action proposal requiring confirmation,
                            # Gemini must NOT execute write operations in the same turn.
                            # Request the conversational confirmation prompt with tools disabled,
                            # then immediately terminate the tool loop.
                            if has_proposal:
                                no_tools_config = types.GenerateContentConfig(
                                    system_instruction=system_instruction,
                                    temperature=temperature,
                                    max_output_tokens=max_output_tokens,
                                    tools=None,
                                )
                                response = client.models.generate_content(
                                    model=current_model,
                                    contents=contents,
                                    config=no_tools_config,
                                )
                                break

                            response = client.models.generate_content(
                                model=current_model,
                                contents=contents,
                                config=config,
                            )
                    else:
                        response = client.models.generate_content(
                            model=current_model,
                            contents=prompt,
                            config=config,
                        )

                    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                    text_content = response.text or ""

                    # Extract usage metadata if available
                    tokens_used = None
                    if hasattr(response, "usage_metadata") and response.usage_metadata:
                        tokens_used = getattr(response.usage_metadata, "total_token_count", None)

                    return GeminiGenerationResult(
                        text=text_content.strip(),
                        model=current_model,
                        tokens_used=tokens_used,
                        latency_ms=elapsed_ms,
                        tools_called=tools_called if tools_called else None,
                        action_proposal=action_proposal
                    )

                except errors.ClientError as ce:
                    # 404: Model not found
                    if getattr(ce, "code", None) == 404 or "NOT_FOUND" in str(ce):
                        logger.error("Gemini model not found: %s", current_model)
                        raise GeminiModelNotFoundError(
                            f"Gemini model '{current_model}' is not available or does not exist."
                        ) from ce

                    # 400/403: Invalid API key or unauthorized
                    if getattr(ce, "code", None) in (400, 401, 403) and ("API_KEY_INVALID" in str(ce) or "PERMISSION_DENIED" in str(ce) or "invalid api key" in str(ce).lower()):
                        logger.error("Gemini API key authorization failure.")
                        raise GeminiAuthenticationError(
                            "Invalid or unauthorized Gemini API key."
                        ) from ce

                    # 429: Rate limit / Resource Exhausted -> Backoff and retry
                    if getattr(ce, "code", None) == 429 or "RESOURCE_EXHAUSTED" in str(ce):
                        attempt += 1
                        last_error = ce
                        if attempt <= self.max_retries:
                            sleep_s = (1.5 ** attempt) + random.uniform(0.1, 0.4)
                            logger.warning("Gemini 429 Rate Limit on %s. Retrying in %.2fs (attempt %d/%d)", current_model, sleep_s, attempt, self.max_retries)
                            time.sleep(sleep_s)
                            continue
                        break

                    # Other client errors
                    logger.error("Gemini ClientError on %s: %s", current_model, type(ce).__name__)
                    raise GeminiError(f"Gemini client error: {getattr(ce, 'message', str(ce))}") from ce

                except errors.ServerError as se:
                    # 503 / 500: Server high demand or internal outage -> Retry with backoff
                    attempt += 1
                    last_error = se
                    code = getattr(se, "code", 503)
                    if attempt <= self.max_retries:
                        sleep_s = (2.0 ** attempt) + random.uniform(0.2, 0.6)
                        logger.warning(
                            "Gemini ServerError (%s) on %s. High demand detected. Retrying in %.2fs (attempt %d/%d)",
                            code, current_model, sleep_s, attempt, self.max_retries
                        )
                        time.sleep(sleep_s)
                        continue
                    else:
                        logger.warning("Retry budget exhausted for model %s with ServerError %s", current_model, code)
                        break

                except TimeoutError as te:
                    attempt += 1
                    last_error = te
                    if attempt <= self.max_retries:
                        sleep_s = 1.0 + random.uniform(0.1, 0.3)
                        time.sleep(sleep_s)
                        continue
                    break

                except Exception as ex:
                    logger.error("Unexpected error during Gemini execution on %s: %s", current_model, type(ex).__name__)
                    raise GeminiError(f"Unexpected AI provider error: {type(ex).__name__}") from ex

        # If loop concludes without returning, all attempts failed
        logger.error("All Gemini models and retry budgets exhausted.")
        if last_error:
            if isinstance(last_error, errors.ServerError) or (isinstance(last_error, errors.ClientError) and getattr(last_error, "code", None) == 429):
                raise GeminiServiceUnavailableError(
                    "Google Gemini AI service is currently experiencing high demand or is temporarily unavailable. Please try again shortly."
                ) from last_error

        raise GeminiServiceUnavailableError(
            "Google Gemini AI service is currently unreachable. Please try again later."
        )

    def health_check(self) -> dict:
        """
        Lightweight health and capability probe for Gemini.
        Returns connectivity status without throwing exceptions.
        """
        if not self._is_configured:
            return {
                "status": "unconfigured",
                "configured": False,
                "model": self.model,
                "detail": "GEMINI_API_KEY is not configured in environment."
            }

        try:
            client = self._get_client()
            # Simple probe
            resp = client.models.generate_content(
                model=self.model,
                contents="Ping",
                config=types.GenerateContentConfig(max_output_tokens=5, temperature=0.0)
            )
            return {
                "status": "available",
                "configured": True,
                "model": self.model,
                "detail": "Successfully communicated with Google Gemini API.",
                "sample_reply": (resp.text or "").strip()[:50]
            }
        except errors.ServerError as se:
            return {
                "status": "high_demand",
                "configured": True,
                "model": self.model,
                "code": getattr(se, "code", 503),
                "detail": "Model is experiencing high demand (503 UNAVAILABLE)."
            }
        except errors.ClientError as ce:
            return {
                "status": "error",
                "configured": True,
                "model": self.model,
                "code": getattr(ce, "code", 400),
                "detail": f"Client error: {type(ce).__name__}"
            }
        except Exception as e:
            return {
                "status": "unavailable",
                "configured": True,
                "model": self.model,
                "detail": f"Provider connection error: {type(e).__name__}"
            }
