import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager executing critical startup validation
    and shutdown routines.
    """
    env_clean = (settings.ENVIRONMENT or "").strip().lower()
    if env_clean == "production":
        insecure_keys = [
            "default-dev-secret-key-must-be-replaced-in-production-env",
            "change-this-to-a-super-secret-random-32-byte-string-in-production",
        ]
        if settings.JWT_SECRET_KEY in insecure_keys or len(settings.JWT_SECRET_KEY) < 32:
            raise RuntimeError("Fatal: Insecure JWT secret detected on production startup.")
        logger.info("Medicall API initialized in PRODUCTION mode with validated security configuration.")
    else:
        logger.info("Medicall API initialized in '%s' mode.", settings.ENVIRONMENT)

    # Automatic initial clinical directory check (seeds verified doctors & slots if empty)
    try:
        from app.db.seed import seed_database
        seed_database()
    except Exception as exc:
        logger.warning("Automatic seed check: %s", exc)

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Voice Healthcare Assistance and Doctor Appointment Management Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to Medicall API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }

