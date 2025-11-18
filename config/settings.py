"""
Nexus Platform Configuration Settings
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application Settings
    APP_NAME: str = "Nexus Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 30 * 60  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = 25 * 60  # 25 minutes

    # Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@nexus-platform.com"
    SMTP_USE_TLS: bool = True

    # AI Configuration
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    AI_MODEL_CLAUDE: str = "claude-3-5-sonnet-20241022"
    AI_MODEL_GPT: str = "gpt-4-turbo-preview"

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./nexus.db"

    # File Upload Settings
    MAX_FILE_SIZE_MB: int = 100
    UPLOAD_DIR: Path = Path("./uploads")
    TEMP_DIR: Path = Path("./temp")
    LOGS_DIR: Path = Path("./logs")

    # Task Queue Settings
    TASK_QUEUE_EMAIL: str = "email_queue"
    TASK_QUEUE_FILE_PROCESSING: str = "file_processing_queue"
    TASK_QUEUE_AI: str = "ai_queue"
    TASK_QUEUE_REPORTS: str = "reports_queue"
    TASK_QUEUE_DEFAULT: str = "default_queue"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
