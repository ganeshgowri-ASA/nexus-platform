"""Configuration settings for scheduler module"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://nexus:nexus@localhost:5432/nexus_scheduler"
    DATABASE_URL_SYNC: str = "postgresql://nexus:nexus@localhost:5432/nexus_scheduler"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # Streamlit
    STREAMLIT_SERVER_PORT: int = 8501
    STREAMLIT_SERVER_ADDRESS: str = "0.0.0.0"

    # Notifications
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None

    # Scheduler
    DEFAULT_TIMEZONE: str = "UTC"
    MAX_RETRY_ATTEMPTS: int = 3
    TASK_TIMEOUT: int = 3600
    ENABLE_SCHEDULER: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
