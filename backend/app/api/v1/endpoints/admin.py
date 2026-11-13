import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.doctor import Doctor
from app.models.user import User, UserRole
from app.schemas.doctor import DoctorResponse

router = APIRouter(prefix="/admin", tags=["Admin Operations"])


class DoctorVerifyResponse(BaseModel):
    doctor_id: uuid.UUID
    doctor_name: str
    is_verified: bool
    message: str


@router.get(
    "/doctors/pending",
    response_model=List[DoctorResponse],
    summary="List doctors awaiting verification (Admin only)"
)
def list_pending_doctors(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    doctors = db.query(Doctor).join(User, Doctor.user_id == User.id).filter(
        User.is_verified == False
    ).all()
    return doctors


@router.get(
    "/doctors",
    response_model=List[DoctorResponse],
    summary="List all doctors with verification status (Admin only)"
)
def list_all_doctors_admin(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    return db.query(Doctor).join(User, Doctor.user_id == User.id).all()


@router.patch(
    "/doctors/{doctor_id}/verify",
    response_model=DoctorVerifyResponse,
    summary="Verify/Approve a doctor's medical license credentials (Admin only)"
)
def verify_doctor(
    doctor_id: uuid.UUID,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found."
        )

    if doctor.user:
        doctor.user.is_verified = True
        db.commit()
        db.refresh(doctor)

    return DoctorVerifyResponse(
        doctor_id=doctor.id,
        doctor_name=f"Dr. {doctor.first_name} {doctor.last_name}",
        is_verified=True,
        message="Doctor account has been successfully verified."
    )

