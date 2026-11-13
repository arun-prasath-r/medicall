import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.doctor import Doctor
from app.models.doctor_schedule import DoctorSchedule
from app.schemas.doctor import DoctorScheduleCreate, DoctorUpdate


class DoctorService:
    @staticmethod
    def list_doctors(
        db: Session,
        specialty: Optional[str] = None,
        max_fee: Optional[Decimal] = None,
        is_accepting_patients: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Doctor]:
        query = db.query(Doctor)
        if specialty:
            query = query.filter(func.lower(Doctor.specialty) == specialty.lower())
        if max_fee is not None:
            query = query.filter(Doctor.consultation_fee <= max_fee)
        if is_accepting_patients is not None:
            query = query.filter(Doctor.is_accepting_patients == is_accepting_patients)
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_doctor_by_id(db: Session, doctor_id: uuid.UUID) -> Doctor:
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found."
            )
        return doctor

    @staticmethod
    def get_specialties(db: Session) -> List[str]:
        results = db.query(Doctor.specialty).distinct().filter(Doctor.specialty.isnot(None)).all()
        return sorted([r[0] for r in results])

    @staticmethod
    def add_schedule(
        db: Session,
        doctor_id: uuid.UUID,
        data: DoctorScheduleCreate
    ) -> DoctorSchedule:
        if data.end_time <= data.start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schedule end time must be after start time."
            )
        
        schedule = DoctorSchedule(
            doctor_id=doctor_id,
            day_of_week=data.day_of_week,
            start_time=data.start_time,
            end_time=data.end_time,
            slot_duration_minutes=data.slot_duration_minutes,
            is_active=data.is_active
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def get_doctor_schedules(db: Session, doctor_id: uuid.UUID) -> List[DoctorSchedule]:
        return db.query(DoctorSchedule).filter(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.is_active.is_(True)
        ).all()

