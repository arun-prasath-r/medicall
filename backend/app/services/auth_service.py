import uuid
from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.schemas.auth import RegisterRequest, RegisterResponse, TokenResponse
from app.schemas.user import UserResponse


class AuthService:
    @staticmethod
    def register_user(db: Session, data: RegisterRequest) -> RegisterResponse:
        # Check existing user
        existing_user = db.query(User).filter(User.email == data.email.lower()).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already registered."
            )

        if data.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator accounts cannot be self-registered."
            )

        hashed_pwd = hash_password(data.password)

        if data.role == UserRole.PATIENT:
            if not data.date_of_birth:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Date of birth is required for patient registration."
                )

            new_user = User(
                email=data.email.lower(),
                hashed_password=hashed_pwd,
                role=UserRole.PATIENT,
                phone_number=data.phone_number,
                is_active=True,
                is_verified=True
            )
            db.add(new_user)
            db.flush()

            patient_profile = Patient(
                user_id=new_user.id,
                first_name=data.first_name,
                last_name=data.last_name,
                date_of_birth=data.date_of_birth,
                gender=data.gender,
                blood_group=data.blood_group,
                emergency_contact_name=data.emergency_contact_name,
                emergency_contact_phone=data.emergency_contact_phone,
                allergies=data.allergies,
                medical_notes=data.medical_notes
            )
            db.add(patient_profile)
            db.commit()
            db.refresh(new_user)
            db.refresh(patient_profile)

            return RegisterResponse(
                user_id=new_user.id,
                email=new_user.email,
                role=new_user.role,
                profile_id=patient_profile.id,
                is_verified=new_user.is_verified,
                message="Patient registration successful."
            )

        elif data.role == UserRole.DOCTOR:
            if not data.license_number or not data.specialty or not data.qualifications:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="License number, specialty, and qualifications are required for doctor registration."
                )

            existing_license = db.query(Doctor).filter(Doctor.license_number == data.license_number).first()
            if existing_license:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A doctor with this medical license number is already registered."
                )

            new_user = User(
                email=data.email.lower(),
                hashed_password=hashed_pwd,
                role=UserRole.DOCTOR,
                phone_number=data.phone_number,
                is_active=True,
                is_verified=False  # Requires credential review
            )
            db.add(new_user)
            db.flush()

            doctor_profile = Doctor(
                user_id=new_user.id,
                first_name=data.first_name,
                last_name=data.last_name,
                license_number=data.license_number,
                specialty=data.specialty,
                qualifications=data.qualifications,
                experience_years=data.experience_years or 0,
                bio=data.bio,
                consultation_fee=data.consultation_fee or 0,
                clinic_address=data.clinic_address,
                is_accepting_patients=True
            )
            db.add(doctor_profile)
            db.commit()
            db.refresh(new_user)
            db.refresh(doctor_profile)

            return RegisterResponse(
                user_id=new_user.id,
                email=new_user.email,
                role=new_user.role,
                profile_id=doctor_profile.id,
                is_verified=new_user.is_verified,
                message="Doctor registration successful. Pending credential verification."
            )

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported user role.")

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> TokenResponse:
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated."
            )

        profile_id = None
        if user.role == UserRole.PATIENT and user.patient:
            profile_id = str(user.patient.id)
        elif user.role == UserRole.DOCTOR and user.doctor:
            profile_id = str(user.doctor.id)

        token_data = {
            "sub": str(user.id),
            "role": user.role.value,
            "email": user.email,
            "profile_id": profile_id
        }
        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )

