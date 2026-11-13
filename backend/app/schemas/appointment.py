import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    doctor_id: uuid.UUID
    availability_id: uuid.UUID
    chief_complaint: str = Field(min_length=3)
    triage_summary: Optional[str] = None


class AppointmentReschedule(BaseModel):
    new_availability_id: uuid.UUID


class AppointmentCancel(BaseModel):
    cancellation_reason: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: uuid.UUID
    appointment_reference: str
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    availability_id: Optional[uuid.UUID] = None
    appointment_datetime: datetime
    end_datetime: datetime
    status: AppointmentStatus
    chief_complaint: str
    triage_summary: Optional[str] = None
    cancellation_reason: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_specialty: Optional[str] = None
    patient_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("appointment_datetime", "end_datetime", "created_at", "updated_at", when_used="json")
    def serialize_utc_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat()

    model_config = ConfigDict(from_attributes=True)

