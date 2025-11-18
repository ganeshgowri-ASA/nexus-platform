"""Application configuration and settings management"""
from typing import List, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application Settings
    APP_ENV: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "NEXUS Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "change-this-in-production"

    # Database Settings
    DATABASE_URL: str = "postgresql+asyncpg://nexus_user:nexus_pass@localhost:5432/nexus_db"

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8501", "http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []

    # File Upload Settings
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB

    # OCR Settings
    OCR_ENGINE: str = "tesseract"  # tesseract, google_vision, aws_textract
    OCR_CONFIDENCE_THRESHOLD: float = 0.7
    TESSERACT_CMD: Optional[str] = "/usr/bin/tesseract"

    # Translation Settings
    TRANSLATION_SERVICE: str = "google"  # google, anthropic
    DEFAULT_SOURCE_LANGUAGE: str = "auto"
    DEFAULT_TARGET_LANGUAGE: str = "en"
    MAX_TRANSLATION_LENGTH: int = 5000

    # API Keys
    GOOGLE_CLOUD_API_KEY: Optional[str] = None
    GOOGLE_TRANSLATE_API_KEY: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Celery Settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create upload directory if it doesn't exist
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


settings = Settings()
