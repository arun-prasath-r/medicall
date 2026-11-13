from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_patient
from app.db.session import get_db
from app.models.patient import Patient
from app.schemas.patient import PatientConsentRequest, PatientResponse, PatientUpdate

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get(
    "/me",
    response_model=PatientResponse,
    summary="Get authenticated patient profile"
)
def get_patient_profile(
    current_patient: Patient = Depends(get_current_patient)
):
    return current_patient


@router.put(
    "/me",
    response_model=PatientResponse,
    summary="Update authenticated patient profile"
)
def update_patient_profile(
    data: PatientUpdate,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_patient, field, value)

    db.commit()
    db.refresh(current_patient)
    return current_patient


@router.post(
    "/consent",
    response_model=PatientResponse,
    summary="Record informed consent for AI voice triage"
)
def record_consent(
    consent_data: PatientConsentRequest,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    if not (
        consent_data.agreed_to_terms
        and consent_data.agreed_to_voice_processing
        and consent_data.agreed_to_non_diagnostic_scope
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All three consent conditions must be explicitly accepted."
        )

    current_patient.consent_given_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_patient)
    return current_patient

