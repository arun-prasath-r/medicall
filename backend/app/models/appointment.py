import uuid
from datetime import datetime, timezone
import enum
from typing import TYPE_CHECKING, Optional
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.doctor import Doctor
    from app.models.availability import Availability


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED_PATIENT = "CANCELLED_PATIENT"
    CANCELLED_DOCTOR = "CANCELLED_DOCTOR"
    RESCHEDULED = "RESCHEDULED"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    appointment_reference: Mapped[str] = mapped_column(
        sa.String(32),
        unique=True,
        nullable=False,
        index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("doctors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    availability_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("availability.id"),
        unique=True,
        nullable=True,
        index=True
    )
    appointment_datetime: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        index=True
    )
    end_datetime: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        sa.Enum(AppointmentStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
        index=True
    )
    chief_complaint: Mapped[str] = mapped_column(
        sa.Text,
        nullable=False
    )
    triage_summary: Mapped[Optional[str]] = mapped_column(
        sa.Text,
        nullable=True
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        sa.Text,
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

    __table_args__ = (
        sa.CheckConstraint("end_datetime > appointment_datetime", name="chk_appointment_duration"),
        sa.Index("idx_appointments_patient_dt", "patient_id", "appointment_datetime"),
        sa.Index("idx_appointments_doctor_dt", "doctor_id", "appointment_datetime"),
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="appointments"
    )
    doctor: Mapped["Doctor"] = relationship(
        "Doctor",
        back_populates="appointments"
    )
    availability: Mapped[Optional["Availability"]] = relationship(
        "Availability",
        back_populates="appointment"
    )

