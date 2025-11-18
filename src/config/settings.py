"""
NEXUS Platform Configuration Settings
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://nexus:nexus_dev_password@localhost:5432/nexus_platform"
    )

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # API Settings
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    API_BASE_URL: str = Field(default="http://localhost:8000")
    API_VERSION: str = Field(default="v1")

    # Streamlit
    STREAMLIT_SERVER_PORT: int = Field(default=8501)
    STREAMLIT_SERVER_ADDRESS: str = Field(default="0.0.0.0")

    # Security
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    JWT_SECRET_KEY: str = Field(default="your-jwt-secret-key-change-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # Claude AI
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)

    # RPA Settings
    RPA_SCREENSHOT_DIR: str = Field(default="./data/screenshots")
    RPA_RECORDING_DIR: str = Field(default="./data/recordings")
    RPA_MAX_EXECUTION_TIME: int = Field(default=3600)  # 1 hour
    RPA_RETRY_ATTEMPTS: int = Field(default=3)
    RPA_RETRY_DELAY: int = Field(default=5)  # seconds

    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0")

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: str = Field(default="./logs/nexus.log")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:8501", "http://localhost:3000"]
    )

    # File Upload
    MAX_UPLOAD_SIZE: int = Field(default=10485760)  # 10MB
    UPLOAD_DIR: str = Field(default="./data/uploads")

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        settings.RPA_SCREENSHOT_DIR,
        settings.RPA_RECORDING_DIR,
        settings.UPLOAD_DIR,
        os.path.dirname(settings.LOG_FILE),
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


# Ensure directories exist on module import
ensure_directories()
