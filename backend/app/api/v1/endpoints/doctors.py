import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_doctor, require_role
from app.db.session import get_db
from app.models.doctor import Doctor
from app.models.user import User, UserRole
from app.schemas.doctor import DoctorResponse, DoctorScheduleCreate, DoctorScheduleResponse
from app.services.doctor_service import DoctorService

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get(
    "",
    response_model=List[DoctorResponse],
    summary="List and filter doctors"
)
def list_doctors(
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    max_fee: Optional[Decimal] = Query(None, description="Maximum consultation fee"),
    is_accepting_patients: Optional[bool] = Query(None, description="Filter by acceptance status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return DoctorService.list_doctors(
        db=db,
        specialty=specialty,
        max_fee=max_fee,
        is_accepting_patients=is_accepting_patients,
        skip=skip,
        limit=limit
    )


@router.get(
    "/specialties",
    response_model=List[str],
    summary="List all distinct doctor specialties"
)
def get_specialties(
    db: Session = Depends(get_db)
):
    return DoctorService.get_specialties(db)


@router.get(
    "/{doctor_id}",
    response_model=DoctorResponse,
    summary="Get doctor profile by ID"
)
def get_doctor(
    doctor_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return DoctorService.get_doctor_by_id(db, doctor_id)


@router.post(
    "/{doctor_id}/schedules",
    response_model=DoctorScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Configure recurring schedule for a doctor"
)
def add_schedule(
    doctor_id: uuid.UUID,
    data: DoctorScheduleCreate,
    current_user: User = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    # Verify doctor modifies their own schedule unless admin
    if current_user.role == UserRole.DOCTOR and current_user.doctor.id != doctor_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctors may only configure their own schedules."
        )
    return DoctorService.add_schedule(db, doctor_id, data)


@router.get(
    "/{doctor_id}/schedules",
    response_model=List[DoctorScheduleResponse],
    summary="Get recurring schedule templates for a doctor"
)
def get_schedules(
    doctor_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return DoctorService.get_doctor_schedules(db, doctor_id)

