import json
from pathlib import Path
from typing import List, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Medicall API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+psycopg://medicall_user:medicall_password@localhost:5432/medicall_db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """
        Normalizes cloud provider connection strings (e.g. Render, Supabase, Neon)
        to use the psycopg v3 dialect expected by SQLAlchemy.
        """
        if isinstance(v, str):
            clean_v = v.strip()
            if clean_v.startswith("postgres://"):
                return "postgresql+psycopg://" + clean_v[len("postgres://"):]
            if clean_v.startswith("postgresql://") and not clean_v.startswith("postgresql+"):
                return "postgresql+psycopg://" + clean_v[len("postgresql://"):]
            return clean_v
        return v

    # Security & JWT
    JWT_SECRET_KEY: str = "default-dev-secret-key-must-be-replaced-in-production-env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """
        Hardens JWT security in production by rejecting known insecure development secrets
        and enforcing a minimum secret length of 32 characters.
        """
        env_clean = (self.ENVIRONMENT or "").strip().lower()
        if env_clean == "production":
            insecure_defaults = [
                "default-dev-secret-key-must-be-replaced-in-production-env",
                "change-this-to-a-super-secret-random-32-byte-string-in-production",
                "secret",
                "secretkey",
                "changeme",
                "password",
                "test",
                "dev",
                "development",
                "123456",
                "admin",
                "medicall",
            ]
            key_val = (self.JWT_SECRET_KEY or "").strip()
            if not key_val or key_val.lower() in insecure_defaults:
                raise ValueError(
                    "Production security violation: JWT_SECRET_KEY must not use known default or insecure development secrets."
                )
            if len(key_val) < 32:
                raise ValueError(
                    "Production security violation: JWT_SECRET_KEY must be at least 32 characters long in production."
                )
        return self

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Emergency Hotlines (Default India: 112)
    DEFAULT_COUNTRY_CODE: str = "IN"
    EMERGENCY_PHONE_NUMBER: str = "112"

    # Clinic Timezone Standard (Patient Facing: Asia/Kolkata / IST)
    CLINIC_TIMEZONE: str = "Asia/Kolkata"

    # Gemini AI Configuration
    GEMINI_API_KEY: Union[str, None] = None
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GEMINI_FALLBACK_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_MAX_RETRIES: int = 3
    GEMINI_TIMEOUT_SECONDS: float = 20.0

    _base_dir: Path = Path(__file__).resolve().parent.parent.parent

    model_config = SettingsConfigDict(
        env_file=(str(_base_dir / ".env"), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

