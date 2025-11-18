"""Configuration settings for NEXUS Platform."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "NEXUS Platform"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # Database
    DATABASE_URL: str = "postgresql://nexus_user:nexus_password@localhost:5432/nexus_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Claude AI
    CLAUDE_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"

    # Batch Processing
    MAX_BATCH_SIZE: int = 10000
    MAX_RETRY_ATTEMPTS: int = 3
    BATCH_CHUNK_SIZE: int = 100
    PARALLEL_WORKERS: int = 4

    # File Upload
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_EXTENSIONS: str = "csv,xlsx,xls,json"

    # Notifications
    ENABLE_EMAIL_NOTIFICATIONS: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def allowed_extensions_list(self) -> list[str]:
        """Get list of allowed file extensions."""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]


settings = Settings()
