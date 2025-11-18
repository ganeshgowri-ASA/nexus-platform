"""
Configuration management for NEXUS platform.
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "NEXUS Platform"
    environment: str = "development"
    secret_key: str
    log_level: str = "INFO"

    # Database
    database_url: str
    database_sync_url: str

    # Redis
    redis_url: str

    # Celery
    celery_broker_url: str
    celery_result_backend: str

    # Google Ads
    google_ads_developer_token: Optional[str] = None
    google_ads_client_id: Optional[str] = None
    google_ads_client_secret: Optional[str] = None
    google_ads_refresh_token: Optional[str] = None
    google_ads_login_customer_id: Optional[str] = None

    # Facebook Ads
    facebook_app_id: Optional[str] = None
    facebook_app_secret: Optional[str] = None
    facebook_access_token: Optional[str] = None

    # LinkedIn Ads
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None
    linkedin_access_token: Optional[str] = None

    # Lead Enrichment APIs
    clearbit_api_key: Optional[str] = None
    hunter_api_key: Optional[str] = None
    zerobounce_api_key: Optional[str] = None

    # AI/LLM
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Sentry
    sentry_dsn: Optional[str] = None


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
