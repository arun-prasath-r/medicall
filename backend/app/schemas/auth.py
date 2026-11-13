import uuid
from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.user import UserRole
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole = UserRole.PATIENT
    phone_number: Optional[str] = None
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)

    # Patient specific fields
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    allergies: Optional[str] = None
    medical_notes: Optional[str] = None

    # Doctor specific fields
    license_number: Optional[str] = None
    specialty: Optional[str] = None
    qualifications: Optional[str] = None
    experience_years: Optional[int] = 0
    bio: Optional[str] = None
    consultation_fee: Optional[Decimal] = Decimal("0.00")
    clinic_address: Optional[str] = None


class RegisterResponse(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    role: UserRole
    profile_id: uuid.UUID
    is_verified: bool
    message: str

    model_config = ConfigDict(from_attributes=True)

