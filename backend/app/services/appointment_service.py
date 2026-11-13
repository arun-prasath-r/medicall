import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.datetime_utils import slot_to_utc_datetime
from app.models.appointment import Appointment, AppointmentStatus
from app.models.availability import Availability, AvailabilityStatus
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.appointment import AppointmentCreate


class AppointmentService:
    @staticmethod
    def book_appointment(
        db: Session,
        patient: Patient,
        data: AppointmentCreate
    ) -> Appointment:
        # Enforce row-level lock on the availability slot to prevent double-booking
        slot = db.query(Availability).filter(
            Availability.id == data.availability_id
        ).with_for_update().first()

        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Availability slot not found."
            )

        if slot.status != AvailabilityStatus.AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The requested appointment slot has already been reserved or is unavailable."
            )

        # Ensure appointment doctor matches the slot doctor
        if slot.doctor_id != data.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The requested doctor does not match the availability slot's assigned doctor."
            )

        # Verify doctor is verified and accepting patients
        if not slot.doctor or not slot.doctor.user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Consultations cannot be booked with an unverified doctor."
            )

        if not slot.doctor.is_accepting_patients:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This doctor is not currently accepting new patients."
            )

        # Mark slot as booked
        slot.status = AvailabilityStatus.BOOKED

        # Construct timezone-aware appointment timestamps normalized to UTC
        # Converts slot date & time (in Asia/Kolkata / IST) to UTC for database storage
        start_dt = slot_to_utc_datetime(slot.slot_date, slot.start_time)
        end_dt = slot_to_utc_datetime(slot.slot_date, slot.end_time)

        # Generate unique human-readable reference code
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        ref_code = f"MED-{now_str}-{uuid.uuid4().hex[:6].upper()}"

        appointment = Appointment(
            appointment_reference=ref_code,
            patient_id=patient.id,
            doctor_id=data.doctor_id,
            availability_id=slot.id,
            appointment_datetime=start_dt,
            end_datetime=end_dt,
            status=AppointmentStatus.SCHEDULED,
            chief_complaint=data.chief_complaint,
            triage_summary=data.triage_summary
        )

        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def get_patient_appointments(
        db: Session,
        patient_id: uuid.UUID
    ) -> List[Appointment]:
        return db.query(Appointment).filter(
            Appointment.patient_id == patient_id
        ).order_by(Appointment.appointment_datetime.desc()).all()

    @staticmethod
    def get_doctor_appointments(
        db: Session,
        doctor_id: uuid.UUID
    ) -> List[Appointment]:
        return db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id
        ).order_by(Appointment.appointment_datetime.desc()).all()

    @staticmethod
    def get_appointment_by_id(
        db: Session,
        appointment_id: uuid.UUID,
        current_user: User
    ) -> Appointment:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found."
            )

        # Enforce patient data isolation and role boundaries
        if current_user.role == UserRole.PATIENT:
            if not current_user.patient or appointment.patient_id != current_user.patient.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this appointment record."
                )
        elif current_user.role == UserRole.DOCTOR:
            if not current_user.doctor or appointment.doctor_id != current_user.doctor.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this appointment record."
                )

        return appointment

    @staticmethod
    def cancel_appointment(
        db: Session,
        appointment_id: uuid.UUID,
        current_user: User,
        cancellation_reason: Optional[str] = None
    ) -> Appointment:
        appointment = AppointmentService.get_appointment_by_id(db, appointment_id, current_user)

        if appointment.status in [
            AppointmentStatus.CANCELLED_PATIENT,
            AppointmentStatus.CANCELLED_DOCTOR,
            AppointmentStatus.COMPLETED
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel an appointment that is already {appointment.status.value}."
            )

        # Determine cancellation status based on caller role
        if current_user.role == UserRole.PATIENT:
            appointment.status = AppointmentStatus.CANCELLED_PATIENT
        else:
            appointment.status = AppointmentStatus.CANCELLED_DOCTOR

        appointment.cancellation_reason = cancellation_reason

        # Release and restore the availability slot to AVAILABLE
        if appointment.availability_id:
            slot = db.query(Availability).filter(
                Availability.id == appointment.availability_id
            ).with_for_update().first()
            if slot:
                slot.status = AvailabilityStatus.AVAILABLE
            # Unlink availability_id from cancelled appointment to free unique constraint
            appointment.availability_id = None

        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def reschedule_appointment(
        db: Session,
        appointment_id: uuid.UUID,
        new_availability_id: uuid.UUID,
        current_user: User
    ) -> Appointment:
        appointment = AppointmentService.get_appointment_by_id(db, appointment_id, current_user)

        if appointment.status not in [AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active appointments (scheduled or rescheduled) can be rescheduled."
            )

        if appointment.availability_id == new_availability_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment is already scheduled for this slot. Please select a different time."
            )

        # Lock the new availability slot
        new_slot = db.query(Availability).filter(
            Availability.id == new_availability_id
        ).with_for_update().first()

        if not new_slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target availability slot not found."
            )

        if new_slot.status != AvailabilityStatus.AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The requested new slot has already been reserved or is unavailable."
            )

        if new_slot.doctor_id != appointment.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reschedule with a different doctor through this action."
            )

        # Free the previous availability slot
        if appointment.availability_id:
            old_slot = db.query(Availability).filter(
                Availability.id == appointment.availability_id
            ).with_for_update().first()
            if old_slot:
                old_slot.status = AvailabilityStatus.AVAILABLE

        # Reserve the new slot
        new_slot.status = AvailabilityStatus.BOOKED

        # Construct timezone-aware appointment timestamps normalized to UTC
        start_dt = slot_to_utc_datetime(new_slot.slot_date, new_slot.start_time)
        end_dt = slot_to_utc_datetime(new_slot.slot_date, new_slot.end_time)

        appointment.availability_id = new_slot.id
        appointment.appointment_datetime = start_dt
        appointment.end_datetime = end_dt
        appointment.status = AppointmentStatus.RESCHEDULED

        db.commit()
        db.refresh(appointment)
        return appointment

