import uuid
from datetime import date, datetime, time
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.availability import AvailabilityStatus


class AvailabilityBase(BaseModel):
    slot_date: date
    start_time: time
    end_time: time
    status: AvailabilityStatus = AvailabilityStatus.AVAILABLE


class AvailabilityCreate(AvailabilityBase):
    pass


class AvailabilityResponse(AvailabilityBase):
    id: uuid.UUID
    doctor_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GenerateSlotsRequest(BaseModel):
    start_date: date
    end_date: date

