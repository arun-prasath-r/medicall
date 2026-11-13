from app.schemas.user import UserBase, UserCreate, UserResponse
from app.schemas.auth import LoginRequest, TokenResponse, RegisterRequest, RegisterResponse
from app.schemas.patient import PatientBase, PatientUpdate, PatientResponse, PatientConsentRequest
from app.schemas.doctor import (
    DoctorBase,
    DoctorUpdate,
    DoctorResponse,
    DoctorScheduleCreate,
    DoctorScheduleResponse,
)
from app.schemas.availability import (
    AvailabilityBase,
    AvailabilityCreate,
    AvailabilityResponse,
    GenerateSlotsRequest,
)
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentReschedule,
    AppointmentCancel,
    AppointmentResponse,
)

__all__ = [
    "UserBase",
    "UserCreate",
    "UserResponse",
    "LoginRequest",
    "TokenResponse",
    "RegisterRequest",
    "RegisterResponse",
    "PatientBase",
    "PatientUpdate",
    "PatientResponse",
    "PatientConsentRequest",
    "DoctorBase",
    "DoctorUpdate",
    "DoctorResponse",
    "DoctorScheduleCreate",
    "DoctorScheduleResponse",
    "AvailabilityBase",
    "AvailabilityCreate",
    "AvailabilityResponse",
    "GenerateSlotsRequest",
    "AppointmentCreate",
    "AppointmentReschedule",
    "AppointmentCancel",
    "AppointmentResponse",
]

