import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_patient, get_current_user
from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.appointment import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentReschedule,
    AppointmentResponse,
)
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["Appointments"])


def _to_response(appt: Appointment) -> AppointmentResponse:
    resp = AppointmentResponse.model_validate(appt)
    if appt.doctor:
        resp.doctor_name = f"Dr. {appt.doctor.first_name} {appt.doctor.last_name}"
        resp.doctor_specialty = appt.doctor.specialty
    if appt.patient:
        resp.patient_name = f"{appt.patient.first_name} {appt.patient.last_name}"
    return resp


@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a doctor consultation appointment"
)
def book_appointment(
    data: AppointmentCreate,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    appointment = AppointmentService.book_appointment(db, current_patient, data)
    return _to_response(appointment)


@router.get(
    "/me",
    response_model=List[AppointmentResponse],
    summary="List appointments for authenticated user (Patient or Doctor)"
)
def get_my_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == UserRole.PATIENT:
        if not current_user.patient:
            return []
        appts = AppointmentService.get_patient_appointments(db, current_user.patient.id)
    elif current_user.role == UserRole.DOCTOR:
        if not current_user.doctor:
            return []
        appts = AppointmentService.get_doctor_appointments(db, current_user.doctor.id)
    else:
        # Admin view - return all recent
        appts = db.query(Appointment).order_by(Appointment.appointment_datetime.desc()).limit(100).all()

    return [_to_response(a) for a in appts]


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Get appointment details by ID"
)
def get_appointment(
    appointment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    appointment = AppointmentService.get_appointment_by_id(db, appointment_id, current_user)
    return _to_response(appointment)


@router.patch(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
    summary="Cancel a scheduled appointment"
)
def cancel_appointment(
    appointment_id: uuid.UUID,
    data: Optional[AppointmentCancel] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reason = data.cancellation_reason if data else None
    appointment = AppointmentService.cancel_appointment(db, appointment_id, current_user, reason)
    return _to_response(appointment)


@router.patch(
    "/{appointment_id}/reschedule",
    response_model=AppointmentResponse,
    summary="Reschedule an appointment to a new slot"
)
def reschedule_appointment(
    appointment_id: uuid.UUID,
    data: AppointmentReschedule,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    appointment = AppointmentService.reschedule_appointment(
        db, appointment_id, data.new_availability_id, current_user
    )
    return _to_response(appointment)

