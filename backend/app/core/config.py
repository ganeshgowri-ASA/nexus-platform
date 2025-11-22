<<<<<<< HEAD
"""
NEXUS Platform - Core Configuration
"""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import validator


class Settings(BaseSettings):
    """Application settings and configuration."""

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NEXUS Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database Configuration
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    SQL_ECHO: bool = False

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    # Security Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:8501", "http://localhost:3000"]

    # AI/LLM Configuration
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: Optional[str] = None

    # Attribution Module Configuration
    ATTRIBUTION_CACHE_TTL: int = 3600  # 1 hour in seconds
    ATTRIBUTION_MAX_TOUCHPOINTS: int = 100
    ATTRIBUTION_WINDOW_DAYS: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )

    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL database URL."""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def REDIS_URL(self) -> str:
        """Construct Redis URL."""
        if self.REDIS_PASSWORD:
            return (
                f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:"
                f"{self.REDIS_PORT}/{self.REDIS_DB}"
            )
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


# Global settings instance
=======
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


>>>>>>> origin/claude/ocr-translation-modules-01Kv1eeHRaW9ea224g8V59NS
settings = Settings()
