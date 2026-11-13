from fastapi import APIRouter
from app.api.v1.endpoints import auth, patients, doctors, availability, appointments, admin
from app.ai.router import router as ai_router

api_router = APIRouter()


@api_router.get("/health", tags=["Health"], summary="System health check")
def health_check():
    return {
        "status": "healthy",
        "service": "medicall-backend",
        "version": "1.0.0"
    }


api_router.include_router(auth.router)
api_router.include_router(patients.router)
api_router.include_router(doctors.router)
api_router.include_router(availability.router)
api_router.include_router(appointments.router)
api_router.include_router(admin.router)
api_router.include_router(ai_router)

