import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ConsumedConfirmationToken(Base):
    """
    Persistent registry of consumed AI action confirmation tokens (nonces).
    Guarantees atomic single-use execution and prevents token replay attacks
    across multiple backend workers, process restarts, and distributed deployments.
    """
    __tablename__ = "consumed_confirmation_tokens"

    jti: Mapped[str] = mapped_column(
        sa.String(64),
        primary_key=True,
        index=True,
        doc="Unique JWT ID (nonce) identifying the confirmation token"
    )
    action: Mapped[str] = mapped_column(
        sa.String(64),
        nullable=False,
        doc="Target write action (book_appointment, cancel_appointment, reschedule_appointment)"
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        index=True,
        doc="Authenticated patient ID who authorized and executed the token"
    )
    consumed_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.func.now(),
        nullable=False,
        doc="Timestamp when the token was consumed and transaction committed"
    )
    expires_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        doc="Original expiration timestamp of the token for pruning"
    )

