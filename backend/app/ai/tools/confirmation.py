import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from sqlalchemy.orm import Session

from app.core.config import settings


class ConfirmationError(Exception):
    """Raised when an action confirmation token is invalid, expired, unauthorized, or replayed."""
    pass


def generate_confirmation_token(
    action: str,
    patient_id: uuid.UUID,
    params: Dict[str, Any],
    expires_in_minutes: int = 10
) -> str:
    """
    Generates a cryptographically signed, short-lived JWT token to bind an intended
    write operation (booking, cancelling, rescheduling) to an explicit patient identity,
    immutable parameters, and a unique single-use nonce (jti).
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_in_minutes)

    # Convert any UUIDs in params to strings for JSON serialization
    serialized_params: Dict[str, Any] = {}
    for k, v in params.items():
        if isinstance(v, uuid.UUID):
            serialized_params[k] = str(v)
        else:
            serialized_params[k] = v

    jti = str(uuid.uuid4())
    payload = {
        "jti": jti,
        "sub": "medicall_ai_confirmation",
        "action": action,
        "patient_id": str(patient_id),
        "params": serialized_params,
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_confirmation_token(
    token: str,
    expected_action: str,
    current_patient_id: uuid.UUID,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Verifies the confirmation token's cryptographic integrity, expiration,
    action type, patient ownership, and atomic single-use nonce consumption.
    Returns the validated operation parameters.
    """
    if not token or not token.strip():
        raise ConfirmationError("Confirmation token is required for this action.")

    try:
        payload = jwt.decode(
            token.strip(),
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError as e:
        raise ConfirmationError(
            "The confirmation token has expired. For clinical safety, appointment actions require prompt confirmation. Please request the action again."
        ) from e
    except jwt.InvalidTokenError as e:
        raise ConfirmationError(
            "The confirmation token is invalid or corrupted. Please request the action again."
        ) from e

    # Verify subject scope
    if payload.get("sub") != "medicall_ai_confirmation":
        raise ConfirmationError("Invalid token scope: not an action confirmation token.")

    # Verify action type
    token_action = payload.get("action")
    if token_action != expected_action:
        raise ConfirmationError(
            f"Action mismatch: token was generated for '{token_action}', but attempted '{expected_action}'."
        )

    # Verify patient ownership (Strict Patient Authorization - Never trust Gemini or Client)
    token_patient_id = payload.get("patient_id")
    if token_patient_id != str(current_patient_id):
        raise ConfirmationError(
            "Security violation: Confirmation token does not belong to the authenticated patient."
        )

    # Persistent Atomic Single-Use Replay Protection
    if db is not None:
        jti = payload.get("jti")
        if not jti:
            raise ConfirmationError("Security violation: Token is missing a unique nonce identifier (jti).")

        from app.models.consumed_token import ConsumedConfirmationToken
        from sqlalchemy.exc import IntegrityError

        # Check if already consumed in database
        existing = db.query(ConsumedConfirmationToken).filter(
            ConsumedConfirmationToken.jti == jti
        ).first()
        if existing:
            raise ConfirmationError(
                "Confirmation token has already been used. Tokens are strictly single-use to prevent replay."
            )

        # Register consumption in the current database transaction
        consumed_record = ConsumedConfirmationToken(
            jti=jti,
            action=token_action,
            patient_id=uuid.UUID(token_patient_id),
            consumed_at=datetime.now(timezone.utc),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        )
        try:
            db.add(consumed_record)
            db.flush()
        except IntegrityError as ie:
            db.rollback()
            raise ConfirmationError(
                "Confirmation token has already been used. Concurrent replay detected."
            ) from ie

    return payload.get("params", {})

