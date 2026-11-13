import uuid
from datetime import datetime, time, timezone
from typing import TYPE_CHECKING
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.doctor import Doctor


class DoctorSchedule(Base):
    __tablename__ = "doctor_schedules"

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
    day_of_week: Mapped[int] = mapped_column(
        sa.SmallInteger,
        nullable=False
    )
    start_time: Mapped[time] = mapped_column(
        sa.Time,
        nullable=False
    )
    end_time: Mapped[time] = mapped_column(
        sa.Time,
        nullable=False
    )
    slot_duration_minutes: Mapped[int] = mapped_column(
        sa.Integer,
        default=30,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
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
        sa.CheckConstraint("day_of_week BETWEEN 0 AND 6", name="chk_schedule_day_of_week"),
        sa.CheckConstraint("end_time > start_time", name="chk_schedule_time_window"),
        sa.CheckConstraint("slot_duration_minutes > 0", name="chk_schedule_slot_duration"),
    )

    # Relationships
    doctor: Mapped["Doctor"] = relationship(
        "Doctor",
        back_populates="schedules"
    )

