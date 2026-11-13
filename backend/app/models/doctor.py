import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.doctor_schedule import DoctorSchedule
    from app.models.availability import Availability
    from app.models.appointment import Appointment


class Doctor(Base):
    __tablename__ = "doctors"

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
    license_number: Mapped[str] = mapped_column(
        sa.String(100),
        unique=True,
        nullable=False,
        index=True
    )
    specialty: Mapped[str] = mapped_column(
        sa.String(100),
        nullable=False,
        index=True
    )
    qualifications: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False
    )
    experience_years: Mapped[int] = mapped_column(
        sa.Integer,
        default=0,
        nullable=False
    )
    bio: Mapped[Optional[str]] = mapped_column(
        sa.Text,
        nullable=True
    )
    consultation_fee: Mapped[Decimal] = mapped_column(
        sa.Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    clinic_address: Mapped[Optional[str]] = mapped_column(
        sa.Text,
        nullable=True
    )
    is_accepting_patients: Mapped[bool] = mapped_column(
        sa.Boolean,
        default=True,
        nullable=False
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

    __table_args__ = (
        sa.CheckConstraint("experience_years >= 0", name="chk_doctor_experience_years"),
        sa.CheckConstraint("consultation_fee >= 0", name="chk_doctor_consultation_fee"),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="doctor"
    )
    schedules: Mapped[List["DoctorSchedule"]] = relationship(
        "DoctorSchedule",
        back_populates="doctor",
        cascade="all, delete-orphan"
    )
    availability_slots: Mapped[List["Availability"]] = relationship(
        "Availability",
        back_populates="doctor",
        cascade="all, delete-orphan"
    )
    appointments: Mapped[List["Appointment"]] = relationship(
        "Appointment",
        back_populates="doctor"
    )

    @property
    def is_verified(self) -> bool:
        return bool(self.user.is_verified) if self.user else False

