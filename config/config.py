"""Configuration management for NEXUS platform."""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # App
    APP_NAME: str = "NEXUS Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Database
    DATABASE_URL: str = "postgresql://nexus:nexus@localhost:5432/nexus"
    SQL_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 3600

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # AI/LLM
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # E-Signature
    DOCUSIGN_API_KEY: Optional[str] = None
    DOCUSIGN_ACCOUNT_ID: Optional[str] = None
    ADOBE_SIGN_API_KEY: Optional[str] = None

    # Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "noreply@nexus.com"

    # Security
    SECRET_KEY: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
