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


class UserRole(str, enum.Enum):
    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        sa.String(255),
        unique=True,
        nullable=False,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        sa.Enum(UserRole, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.PATIENT,
        index=True
    )
    phone_number: Mapped[Optional[str]] = mapped_column(
        sa.String(32),
        nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        default=True,
        nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        sa.Boolean,
        default=False,
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

    # 1-to-0..1 Relationships
    patient: Mapped[Optional["Patient"]] = relationship(
        "Patient",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    doctor: Mapped[Optional["Doctor"]] = relationship(
        "Doctor",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    @property
    def first_name(self) -> Optional[str]:
        if self.patient:
            return self.patient.first_name
        if self.doctor:
            return self.doctor.first_name
        return None

    @property
    def last_name(self) -> Optional[str]:
        if self.patient:
            return self.patient.last_name
        if self.doctor:
            return self.doctor.last_name
        return None

    @property
    def profile_id(self) -> Optional[uuid.UUID]:
        if self.patient:
            return self.patient.id
        if self.doctor:
            return self.doctor.id
        return None

