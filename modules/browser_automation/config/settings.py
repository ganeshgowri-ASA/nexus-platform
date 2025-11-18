"""Configuration settings for Browser Automation Module"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    APP_NAME: str = "NEXUS Browser Automation"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://nexus:nexus@localhost:5432/nexus_browser_automation",
        description="PostgreSQL database URL"
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 3600

    # Browser Automation
    BROWSER_TYPE: str = "chromium"  # chromium, firefox, webkit
    HEADLESS_MODE: bool = True
    BROWSER_TIMEOUT: int = 30000
    SCREENSHOT_QUALITY: int = 90
    MAX_CONCURRENT_BROWSERS: int = 5

    # Storage
    STORAGE_PATH: str = "./modules/browser_automation/storage"
    SCREENSHOT_PATH: str = "./modules/browser_automation/storage/screenshots"
    PDF_PATH: str = "./modules/browser_automation/storage/pdfs"
    LOG_PATH: str = "./modules/browser_automation/storage/logs"

    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Monitoring
    ENABLE_METRICS: bool = True
    SENTRY_DSN: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
