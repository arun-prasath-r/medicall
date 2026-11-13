import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.appointment import Appointment


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    first_name: Mapped[str] = mapped_column(
        sa.String(100),
        nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        sa.String(100),
        nullable=False
    )
    date_of_birth: Mapped[date] = mapped_column(
        sa.Date,
        nullable=False
    )
    gender: Mapped[Optional[str]] = mapped_column(
        sa.String(32),
        nullable=True
    )
    blood_group: Mapped[Optional[str]] = mapped_column(
        sa.String(10),
        nullable=True
    )
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(
        sa.String(100),
        nullable=True
    )
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(
        sa.String(32),
        nullable=True
    )
    allergies: Mapped[Optional[str]] = mapped_column(
        sa.Text,
        nullable=True
    )
    medical_notes: Mapped[Optional[str]] = mapped_column(
        sa.Text,
        nullable=True
    )
    consent_given_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="patient"
    )
    appointments: Mapped[List["Appointment"]] = relationship(
        "Appointment",
        back_populates="patient",
        cascade="all, delete-orphan"
    )

