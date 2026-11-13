from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, RegisterResponse, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Patient or Doctor account"
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    return AuthService.register_user(db, data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and obtain JWT access token"
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    return AuthService.authenticate_user(db, data.email, data.password)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Retrieve profile of authenticated user"
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user

