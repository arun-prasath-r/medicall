import uuid
from datetime import date, datetime, time, timezone
import enum
from typing import TYPE_CHECKING, Optional
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.doctor import Doctor
    from app.models.appointment import Appointment


class AvailabilityStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BOOKED = "BOOKED"
    BLOCKED = "BLOCKED"


class Availability(Base):
    __tablename__ = "availability"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    slot_date: Mapped[date] = mapped_column(
        sa.Date,
        nullable=False,
        index=True
    )
    start_time: Mapped[time] = mapped_column(
        sa.Time,
        nullable=False
    )
    end_time: Mapped[time] = mapped_column(
        sa.Time,
        nullable=False
    )
    status: Mapped[AvailabilityStatus] = mapped_column(
        sa.Enum(AvailabilityStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=AvailabilityStatus.AVAILABLE,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.func.now(),
        nullable=False
    )

    __table_args__ = (
        sa.CheckConstraint("end_time > start_time", name="chk_availability_time_window"),
        sa.UniqueConstraint("doctor_id", "slot_date", "start_time", name="uq_doctor_date_slot"),
        sa.Index("idx_availability_search", "doctor_id", "slot_date", "status"),
        sa.Index("idx_availability_date_status", "slot_date", "status"),
    )

    # Relationships
    doctor: Mapped["Doctor"] = relationship(
        "Doctor",
        back_populates="availability_slots"
    )
    appointment: Mapped[Optional["Appointment"]] = relationship(
        "Appointment",
        back_populates="availability",
        uselist=False
    )

