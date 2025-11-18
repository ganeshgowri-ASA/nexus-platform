"""
Configuration for Webhooks Module
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Webhook module settings"""

    # Database
    DATABASE_URL: str = "postgresql://nexus:nexus@localhost:5432/nexus_webhooks"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Webhook Settings
    WEBHOOK_TIMEOUT: int = 30  # seconds
    MAX_RETRY_ATTEMPTS: int = 5
    RETRY_BACKOFF_FACTOR: float = 2.0  # exponential backoff
    INITIAL_RETRY_DELAY: int = 60  # seconds

    # Security
    WEBHOOK_SECRET_KEY: str = "change-this-secret-key-in-production"
    SIGNATURE_HEADER: str = "X-Webhook-Signature"

    # Logging
    LOG_RETENTION_DAYS: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
