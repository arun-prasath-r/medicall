import uuid
from datetime import datetime, time
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DoctorBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    specialty: str = Field(min_length=1, max_length=100)
    qualifications: str = Field(min_length=1, max_length=255)
    experience_years: int = Field(ge=0, default=0)
    bio: Optional[str] = None
    consultation_fee: Decimal = Field(ge=Decimal("0.00"), default=Decimal("0.00"))
    clinic_address: Optional[str] = None
    is_accepting_patients: bool = True


class DoctorUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    specialty: Optional[str] = Field(None, min_length=1, max_length=100)
    qualifications: Optional[str] = Field(None, min_length=1, max_length=255)
    experience_years: Optional[int] = Field(None, ge=0)
    bio: Optional[str] = None
    consultation_fee: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    clinic_address: Optional[str] = None
    is_accepting_patients: Optional[bool] = None


class DoctorResponse(DoctorBase):
    id: uuid.UUID
    user_id: uuid.UUID
    license_number: str
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DoctorScheduleCreate(BaseModel):
    day_of_week: int = Field(ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: time
    end_time: time
    slot_duration_minutes: int = Field(gt=0, default=30)
    is_active: bool = True


class DoctorScheduleResponse(DoctorScheduleCreate):
    id: uuid.UUID
    doctor_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

