import uuid
from datetime import date, datetime, time, timedelta
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.availability import Availability, AvailabilityStatus
from app.models.doctor import Doctor
from app.models.doctor_schedule import DoctorSchedule
from app.schemas.availability import AvailabilityCreate


class AvailabilityService:
    @staticmethod
    def get_doctor_availability(
        db: Session,
        doctor_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        slot_status: Optional[AvailabilityStatus] = AvailabilityStatus.AVAILABLE
    ) -> List[Availability]:
        query = db.query(Availability).filter(Availability.doctor_id == doctor_id)
        if start_date:
            query = query.filter(Availability.slot_date >= start_date)
        if end_date:
            query = query.filter(Availability.slot_date <= end_date)
        if slot_status:
            query = query.filter(Availability.status == slot_status)
        
        return query.order_by(Availability.slot_date.asc(), Availability.start_time.asc()).all()

    @staticmethod
    def create_slot(
        db: Session,
        doctor_id: uuid.UUID,
        data: AvailabilityCreate
    ) -> Availability:
        # Verify doctor exists
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")

        if data.end_time <= data.start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slot end time must be after start time."
            )

        # Check for overlapping slots for the same doctor on the same date
        overlap = db.query(Availability).filter(
            Availability.doctor_id == doctor_id,
            Availability.slot_date == data.slot_date,
            Availability.start_time < data.end_time,
            Availability.end_time > data.start_time
        ).first()

        if overlap:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Availability slot overlaps with an existing slot for this doctor on this date."
            )

        slot = Availability(
            doctor_id=doctor_id,
            slot_date=data.slot_date,
            start_time=data.start_time,
            end_time=data.end_time,
            status=data.status
        )
        db.add(slot)
        db.commit()
        db.refresh(slot)
        return slot

    @staticmethod
    def generate_slots_from_schedules(
        db: Session,
        doctor_id: uuid.UUID,
        start_date: date,
        end_date: date
    ) -> List[Availability]:
        if end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date cannot be earlier than start date."
            )

        schedules = db.query(DoctorSchedule).filter(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.is_active.is_(True)
        ).all()

        if not schedules:
            return []

        generated_slots: List[Availability] = []
        curr_date = start_date

        while curr_date <= end_date:
            # Python weekday(): Monday is 0, Sunday is 6
            day_of_week = curr_date.weekday()
            day_schedules = [s for s in schedules if s.day_of_week == day_of_week]

            for sched in day_schedules:
                # Convert time to datetime on curr_date for interval math
                curr_dt = datetime.combine(curr_date, sched.start_time)
                end_dt = datetime.combine(curr_date, sched.end_time)
                duration = timedelta(minutes=sched.slot_duration_minutes)

                while curr_dt + duration <= end_dt:
                    slot_start = curr_dt.time()
                    slot_end = (curr_dt + duration).time()

                    # Check if slot already exists
                    existing = db.query(Availability).filter(
                        Availability.doctor_id == doctor_id,
                        Availability.slot_date == curr_date,
                        Availability.start_time == slot_start
                    ).first()

                    if not existing:
                        new_slot = Availability(
                            doctor_id=doctor_id,
                            slot_date=curr_date,
                            start_time=slot_start,
                            end_time=slot_end,
                            status=AvailabilityStatus.AVAILABLE
                        )
                        db.add(new_slot)
                        generated_slots.append(new_slot)

                    curr_dt += duration

            curr_date += timedelta(days=1)

        db.commit()
        for s in generated_slots:
            db.refresh(s)

        return generated_slots

