"""
Patient appointment inspection and mutation tools for Gemini AI.

Strictly reuses existing AppointmentService, DoctorService, and AvailabilityService.
Enforces Patient Ownership isolation: patient ID is ALWAYS derived from JWT current_user.
Enforces Explicit Confirmation guard for all write actions (book, cancel, reschedule).
"""

import logging
import uuid
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_to_clinic_datetime
from app.models.appointment import Appointment, AppointmentStatus
from app.models.availability import Availability, AvailabilityStatus
from app.models.doctor import Doctor
from app.models.user import User, UserRole
from app.schemas.appointment import AppointmentCreate
from app.services.appointment_service import AppointmentService
from app.ai.tools.confirmation import (
    ConfirmationError,
    generate_confirmation_token,
    verify_confirmation_token,
)

logger = logging.getLogger(__name__)


def _require_patient_user(current_user: User):
    """Guarantees that the authenticated user is a patient with a valid profile."""
    if not current_user:
        raise ValueError("Authentication required.")
    if current_user.role != UserRole.PATIENT or not current_user.patient:
        raise ValueError(
            "This operation requires an authenticated patient profile. "
            "The current account is not registered as a patient."
        )
    return current_user.patient


def execute_get_my_appointments(
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """
    Retrieve all appointments for the authenticated patient.
    Strictly isolated: Gemini or client cannot access appointments belonging to other patients.
    """
    try:
        patient = _require_patient_user(current_user)
        appointments = AppointmentService.get_patient_appointments(db, patient.id)

        formatted_list = []
        for appt in appointments:
            clinic_dt = utc_to_clinic_datetime(appt.appointment_datetime)
            doctor_name = "Unknown Doctor"
            specialty = "General"
            fee = 0.0
            if appt.doctor:
                doctor_name = f"Dr. {appt.doctor.first_name} {appt.doctor.last_name}"
                specialty = appt.doctor.specialty
                fee = float(appt.doctor.consultation_fee)

            formatted_list.append({
                "appointment_id": str(appt.id),
                "reference_code": appt.appointment_reference,
                "doctor_id": str(appt.doctor_id),
                "doctor_name": doctor_name,
                "specialty": specialty,
                "consultation_fee": fee,
                "status": appt.status.value,
                "appointment_date": clinic_dt.strftime("%Y-%m-%d"),
                "appointment_time": clinic_dt.strftime("%I:%M %p"),
                "appointment_datetime_iso": clinic_dt.isoformat(),
                "chief_complaint": appt.chief_complaint,
            })

        return {
            "success": True,
            "total_appointments": len(formatted_list),
            "appointments": formatted_list,
            "message": f"Found {len(formatted_list)} appointment(s) in your medical record."
        }

    except ValueError as ve:
        return {"success": False, "error": str(ve)}
    except Exception as e:
        logger.error("Error in execute_get_my_appointments: %s", str(e))
        return {"success": False, "error": "Could not retrieve appointment history."}


def execute_book_appointment(
    db: Session,
    current_user: User,
    doctor_id: str,
    availability_id: str,
    chief_complaint: str,
    confirmation_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Book an appointment.
    If confirmation_token is absent: returns a proposal requiring patient consent.
    If confirmation_token is present: verifies cryptographic validity and single-use consumption first, then executes booking.
    """
    try:
        patient = _require_patient_user(current_user)

        try:
            doc_uuid = uuid.UUID(doctor_id.strip())
            slot_uuid = uuid.UUID(availability_id.strip())
        except (ValueError, AttributeError):
            return {
                "success": False,
                "error": "Invalid doctor_id or availability_id UUID format."
            }

        # 1. If confirmation token is present: Validate cryptographic validity & single-use nonce FIRST
        if confirmation_token and confirmation_token.strip():
            try:
                verified_params = verify_confirmation_token(
                    token=confirmation_token,
                    expected_action="book_appointment",
                    current_patient_id=patient.id,
                    db=db
                )
            except ConfirmationError as ce:
                return {
                    "success": False,
                    "error": f"Confirmation validation failed: {str(ce)}"
                }

            # Re-verify params match intended booking
            if (verified_params.get("doctor_id") != str(doc_uuid) or
                verified_params.get("availability_id") != str(slot_uuid)):
                return {
                    "success": False,
                    "error": "Confirmation token parameters do not match requested doctor or slot."
                }

            # Execute booking through existing transactional service
            booking_data = AppointmentCreate(
                doctor_id=doc_uuid,
                availability_id=slot_uuid,
                chief_complaint=verified_params.get("chief_complaint", chief_complaint),
                triage_summary="Booked via Medicall AI Clinical Assistant with verified patient confirmation."
            )

            appointment = AppointmentService.book_appointment(db, patient, booking_data)
            clinic_dt = utc_to_clinic_datetime(appointment.appointment_datetime)

            doctor_name = "your doctor"
            specialty = "General"
            if appointment.doctor:
                doctor_name = f"Dr. {appointment.doctor.first_name} {appointment.doctor.last_name}"
                specialty = appointment.doctor.specialty

            return {
                "success": True,
                "appointment_id": str(appointment.id),
                "reference_code": appointment.appointment_reference,
                "status": appointment.status.value,
                "doctor_name": doctor_name,
                "specialty": specialty,
                "appointment_date": clinic_dt.strftime("%A, %B %d, %Y"),
                "appointment_time": clinic_dt.strftime("%I:%M %p"),
                "message": (
                    f"Appointment successfully confirmed and booked! Reference: {appointment.appointment_reference}. "
                    f"Date: {clinic_dt.strftime('%B %d, %Y')} at {clinic_dt.strftime('%I:%M %p')} with {doctor_name}."
                )
            }

        # 2. If NO confirmation token, validate target slot & doctor and return proposal
        slot = db.query(Availability).filter(Availability.id == slot_uuid).first()
        if not slot:
            return {"success": False, "error": "Availability slot not found."}

        if slot.status != AvailabilityStatus.AVAILABLE:
            return {
                "success": False,
                "error": f"The selected appointment slot is {slot.status.value} and cannot be booked."
            }

        if slot.doctor_id != doc_uuid:
            return {
                "success": False,
                "error": "The selected slot does not match the designated doctor."
            }

        doctor = db.query(Doctor).filter(Doctor.id == doc_uuid).first()
        if not doctor or not doctor.user or not doctor.user.is_verified:
            return {"success": False, "error": "Doctor is not verified or does not exist."}

        if not doctor.is_accepting_patients:
            return {"success": False, "error": "Doctor is not currently accepting new patients."}

        doctor_full_name = f"Dr. {doctor.first_name} {doctor.last_name}"
        slot_date_str = slot.slot_date.strftime("%A, %B %d, %Y")
        slot_time_str = f"{slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}"

        token = generate_confirmation_token(
            action="book_appointment",
            patient_id=patient.id,
            params={
                "doctor_id": str(doc_uuid),
                "availability_id": str(slot_uuid),
                "chief_complaint": chief_complaint.strip(),
            }
        )
        return {
            "requires_confirmation": True,
            "action": "book_appointment",
            "confirmation_token": token,
            "doctor_name": doctor_full_name,
            "specialty": doctor.specialty,
            "consultation_fee": float(doctor.consultation_fee),
            "slot_date": slot_date_str,
            "slot_time": slot_time_str,
            "chief_complaint": chief_complaint.strip(),
            "summary": (
                f"Booking with {doctor_full_name} ({doctor.specialty}) on {slot_date_str} at {slot_time_str}. "
                f"Consultation fee: ${doctor.consultation_fee:.2f}."
            ),
            "instruction": (
                "Please present this exact summary to the patient and ask: "
                "'Would you like me to confirm and book this appointment for you?'"
            )
        }

    except HTTPException as he:
        return {"success": False, "error": he.detail}
    except ValueError as ve:
        return {"success": False, "error": str(ve)}
    except Exception as e:
        logger.error("Error booking appointment via AI tool: %s", str(e))
        return {"success": False, "error": "An unexpected error occurred while booking the appointment."}


def execute_cancel_appointment(
    db: Session,
    current_user: User,
    appointment_id: str,
    reason: Optional[str] = None,
    confirmation_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cancel an appointment.
    If confirmation_token is absent: returns a proposal requiring patient consent.
    If confirmation_token is present: verifies cryptographic validity and single-use consumption first, then executes cancellation.
    """
    try:
        patient = _require_patient_user(current_user)

        try:
            appt_uuid = uuid.UUID(appointment_id.strip())
        except (ValueError, AttributeError):
            return {"success": False, "error": "Invalid appointment_id UUID format."}

        # 1. Confirmation token present: Validate cryptographic validity & single-use nonce FIRST
        if confirmation_token and confirmation_token.strip():
            try:
                verified_params = verify_confirmation_token(
                    token=confirmation_token,
                    expected_action="cancel_appointment",
                    current_patient_id=patient.id,
                    db=db
                )
            except ConfirmationError as ce:
                return {"success": False, "error": f"Confirmation validation failed: {str(ce)}"}

            if verified_params.get("appointment_id") != str(appt_uuid):
                return {"success": False, "error": "Confirmation token does not match requested appointment."}

            cancelled_appt = AppointmentService.cancel_appointment(
                db=db,
                appointment_id=appt_uuid,
                current_user=current_user,
                cancellation_reason=verified_params.get("reason", reason)
            )

            return {
                "success": True,
                "appointment_id": str(cancelled_appt.id),
                "reference_code": cancelled_appt.appointment_reference,
                "status": cancelled_appt.status.value,
                "message": f"Appointment {cancelled_appt.appointment_reference} has been successfully cancelled. The time slot has been released."
            }

        # 2. If NO confirmation token, inspect appointment and return proposal
        appointment = db.query(Appointment).filter(Appointment.id == appt_uuid).first()
        if not appointment:
            return {"success": False, "error": "Appointment not found."}

        if appointment.patient_id != patient.id:
            return {"success": False, "error": "Access denied: This appointment belongs to another patient."}

        if appointment.status in [
            AppointmentStatus.CANCELLED_PATIENT,
            AppointmentStatus.CANCELLED_DOCTOR,
            AppointmentStatus.COMPLETED
        ]:
            return {
                "success": False,
                "error": f"Cannot cancel an appointment that is already {appointment.status.value}."
            }

        doctor_name = "your doctor"
        if appointment.doctor:
            doctor_name = f"Dr. {appointment.doctor.first_name} {appointment.doctor.last_name}"

        clinic_dt = utc_to_clinic_datetime(appointment.appointment_datetime)
        dt_str = clinic_dt.strftime("%A, %B %d, %Y at %I:%M %p")

        token = generate_confirmation_token(
            action="cancel_appointment",
            patient_id=patient.id,
            params={
                "appointment_id": str(appt_uuid),
                "reason": (reason or "").strip()
            }
        )
        return {
            "requires_confirmation": True,
            "action": "cancel_appointment",
            "confirmation_token": token,
            "appointment_id": str(appt_uuid),
            "reference_code": appointment.appointment_reference,
            "doctor_name": doctor_name,
            "appointment_datetime": dt_str,
            "reason": reason,
            "summary": f"Cancel appointment {appointment.appointment_reference} with {doctor_name} scheduled for {dt_str}.",
            "instruction": (
                "Please ask the patient explicitly: "
                f"'Are you sure you want to cancel your appointment ({appointment.appointment_reference}) with {doctor_name} on {dt_str}?'"
            )
        }

    except HTTPException as he:
        return {"success": False, "error": he.detail}
    except ValueError as ve:
        return {"success": False, "error": str(ve)}
    except Exception as e:
        logger.error("Error in execute_cancel_appointment: %s", str(e))
        return {"success": False, "error": "Could not cancel appointment."}


def execute_reschedule_appointment(
    db: Session,
    current_user: User,
    appointment_id: str,
    new_availability_id: str,
    confirmation_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Reschedule an appointment to a new available slot with the same doctor.
    If confirmation_token is absent: returns a proposal requiring patient consent.
    If confirmation_token is present: verifies cryptographic validity and single-use consumption first, then executes rescheduling.
    """
    try:
        patient = _require_patient_user(current_user)

        try:
            appt_uuid = uuid.UUID(appointment_id.strip())
            new_slot_uuid = uuid.UUID(new_availability_id.strip())
        except (ValueError, AttributeError):
            return {"success": False, "error": "Invalid appointment_id or new_availability_id UUID format."}

        # 1. Confirmation token present: Validate cryptographic validity & single-use nonce FIRST
        if confirmation_token and confirmation_token.strip():
            try:
                verified_params = verify_confirmation_token(
                    token=confirmation_token,
                    expected_action="reschedule_appointment",
                    current_patient_id=patient.id,
                    db=db
                )
            except ConfirmationError as ce:
                return {"success": False, "error": f"Confirmation validation failed: {str(ce)}"}

            if (verified_params.get("appointment_id") != str(appt_uuid) or
                verified_params.get("new_availability_id") != str(new_slot_uuid)):
                return {"success": False, "error": "Confirmation token parameters do not match requested reschedule."}

            rescheduled_appt = AppointmentService.reschedule_appointment(
                db=db,
                appointment_id=appt_uuid,
                new_availability_id=new_slot_uuid,
                current_user=current_user
            )

            new_clinic_dt = utc_to_clinic_datetime(rescheduled_appt.appointment_datetime)

            return {
                "success": True,
                "appointment_id": str(rescheduled_appt.id),
                "reference_code": rescheduled_appt.appointment_reference,
                "status": rescheduled_appt.status.value,
                "new_appointment_date": new_clinic_dt.strftime("%A, %B %d, %Y"),
                "new_appointment_time": new_clinic_dt.strftime("%I:%M %p"),
                "message": (
                    f"Appointment {rescheduled_appt.appointment_reference} has been successfully rescheduled to "
                    f"{new_clinic_dt.strftime('%B %d, %Y')} at {new_clinic_dt.strftime('%I:%M %p')}."
                )
            }

        # 2. If NO confirmation token, inspect appointment & target slot and return proposal
        appointment = db.query(Appointment).filter(Appointment.id == appt_uuid).first()
        if not appointment:
            return {"success": False, "error": "Appointment not found."}

        if appointment.patient_id != patient.id:
            return {"success": False, "error": "Access denied: This appointment belongs to another patient."}

        if appointment.status not in [AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED]:
            return {
                "success": False,
                "error": f"Only active appointments can be rescheduled. Current status: {appointment.status.value}."
            }

        new_slot = db.query(Availability).filter(Availability.id == new_slot_uuid).first()
        if not new_slot:
            return {"success": False, "error": "Target availability slot not found."}

        if new_slot.status != AvailabilityStatus.AVAILABLE:
            return {
                "success": False,
                "error": f"The selected new slot is {new_slot.status.value} and cannot be reserved."
            }

        if new_slot.doctor_id != appointment.doctor_id:
            return {
                "success": False,
                "error": "Cannot reschedule with a different doctor through this action."
            }

        doctor_name = f"Dr. {appointment.doctor.first_name} {appointment.doctor.last_name}" if appointment.doctor else "your doctor"
        old_clinic_dt = utc_to_clinic_datetime(appointment.appointment_datetime)
        old_dt_str = old_clinic_dt.strftime("%A, %B %d, %Y at %I:%M %p")
        new_dt_str = f"{new_slot.slot_date.strftime('%A, %B %d, %Y')} from {new_slot.start_time.strftime('%I:%M %p')} to {new_slot.end_time.strftime('%I:%M %p')}"

        token = generate_confirmation_token(
            action="reschedule_appointment",
            patient_id=patient.id,
            params={
                "appointment_id": str(appt_uuid),
                "new_availability_id": str(new_slot_uuid)
            }
        )
        return {
            "requires_confirmation": True,
            "action": "reschedule_appointment",
            "confirmation_token": token,
            "appointment_id": str(appt_uuid),
            "reference_code": appointment.appointment_reference,
            "doctor_name": doctor_name,
            "current_time": old_dt_str,
            "new_time": new_dt_str,
            "summary": f"Reschedule appointment {appointment.appointment_reference} with {doctor_name} from {old_dt_str} to {new_dt_str}.",
            "instruction": (
                "Please ask the patient explicitly: "
                f"'Would you like me to reschedule your appointment with {doctor_name} to {new_dt_str}?'"
            )
        }

    except HTTPException as he:
        return {"success": False, "error": he.detail}
    except ValueError as ve:
        return {"success": False, "error": str(ve)}
    except Exception as e:
        logger.error("Error in execute_reschedule_appointment: %s", str(e))
        return {"success": False, "error": "Could not reschedule appointment."}

