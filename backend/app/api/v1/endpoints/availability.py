import uuid
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.availability import AvailabilityStatus
from app.models.user import User, UserRole
from app.schemas.availability import AvailabilityCreate, AvailabilityResponse, GenerateSlotsRequest
from app.services.availability_service import AvailabilityService

router = APIRouter(prefix="/doctors/{doctor_id}/availability", tags=["Doctor Availability"])


@router.get(
    "",
    response_model=List[AvailabilityResponse],
    summary="Get available consultation slots for a doctor"
)
def get_doctor_availability(
    doctor_id: uuid.UUID,
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    status: Optional[AvailabilityStatus] = Query(AvailabilityStatus.AVAILABLE, description="Filter by status"),
    db: Session = Depends(get_db)
):
    return AvailabilityService.get_doctor_availability(
        db=db,
        doctor_id=doctor_id,
        start_date=start_date,
        end_date=end_date,
        slot_status=status
    )


@router.post(
    "",
    response_model=AvailabilityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a discrete availability slot (Doctor/Admin)"
)
def create_slot(
    doctor_id: uuid.UUID,
    data: AvailabilityCreate,
    current_user: User = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    if current_user.role == UserRole.DOCTOR and current_user.doctor.id != doctor_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctors may only add slots to their own calendar."
        )
    return AvailabilityService.create_slot(db, doctor_id, data)


@router.post(
    "/generate",
    response_model=List[AvailabilityResponse],
    summary="Generate discrete availability slots from recurring schedule templates"
)
def generate_slots(
    doctor_id: uuid.UUID,
    data: GenerateSlotsRequest,
    current_user: User = Depends(require_role([UserRole.DOCTOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    if current_user.role == UserRole.DOCTOR and current_user.doctor.id != doctor_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctors may only generate slots for their own calendar."
        )
    return AvailabilityService.generate_slots_from_schedules(
        db=db,
        doctor_id=doctor_id,
        start_date=data.start_date,
        end_date=data.end_date
    )

