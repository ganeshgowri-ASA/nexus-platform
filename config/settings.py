"""
Application settings and configuration management.

This module handles all configuration settings for the NEXUS platform,
including database, Redis, Celery, API keys, and environment-specific settings.
"""

import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    # Application
    app_name: str = "NEXUS Platform"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, validation_alias="DEBUG")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        validation_alias="SECRET_KEY"
    )
    api_key_header: str = "X-API-Key"
    allowed_hosts: list[str] = Field(default=["*"], validation_alias="ALLOWED_HOSTS")

    # Database
    database_url: str = Field(
        default="postgresql://nexus:nexus@localhost:5432/nexus",
        validation_alias="DATABASE_URL"
    )
    db_echo: bool = Field(default=False, validation_alias="DB_ECHO")
    db_pool_size: int = Field(default=5, validation_alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, validation_alias="DB_MAX_OVERFLOW")

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL"
    )
    redis_cache_ttl: int = Field(default=3600, validation_alias="REDIS_CACHE_TTL")

    # Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        validation_alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        validation_alias="CELERY_RESULT_BACKEND"
    )

    # AI/LLM Configuration
    anthropic_api_key: Optional[str] = Field(
        default=None,
        validation_alias="ANTHROPIC_API_KEY"
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        validation_alias="OPENAI_API_KEY"
    )
    llm_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        validation_alias="LLM_MODEL"
    )

    # Advertising Platform APIs
    google_ads_client_id: Optional[str] = Field(
        default=None,
        validation_alias="GOOGLE_ADS_CLIENT_ID"
    )
    google_ads_client_secret: Optional[str] = Field(
        default=None,
        validation_alias="GOOGLE_ADS_CLIENT_SECRET"
    )
    google_ads_developer_token: Optional[str] = Field(
        default=None,
        validation_alias="GOOGLE_ADS_DEVELOPER_TOKEN"
    )
    google_ads_refresh_token: Optional[str] = Field(
        default=None,
        validation_alias="GOOGLE_ADS_REFRESH_TOKEN"
    )

    facebook_app_id: Optional[str] = Field(
        default=None,
        validation_alias="FACEBOOK_APP_ID"
    )
    facebook_app_secret: Optional[str] = Field(
        default=None,
        validation_alias="FACEBOOK_APP_SECRET"
    )
    facebook_access_token: Optional[str] = Field(
        default=None,
        validation_alias="FACEBOOK_ACCESS_TOKEN"
    )

    linkedin_client_id: Optional[str] = Field(
        default=None,
        validation_alias="LINKEDIN_CLIENT_ID"
    )
    linkedin_client_secret: Optional[str] = Field(
        default=None,
        validation_alias="LINKEDIN_CLIENT_SECRET"
    )
    linkedin_access_token: Optional[str] = Field(
        default=None,
        validation_alias="LINKEDIN_ACCESS_TOKEN"
    )

    twitter_api_key: Optional[str] = Field(
        default=None,
        validation_alias="TWITTER_API_KEY"
    )
    twitter_api_secret: Optional[str] = Field(
        default=None,
        validation_alias="TWITTER_API_SECRET"
    )
    twitter_access_token: Optional[str] = Field(
        default=None,
        validation_alias="TWITTER_ACCESS_TOKEN"
    )

    tiktok_app_id: Optional[str] = Field(
        default=None,
        validation_alias="TIKTOK_APP_ID"
    )
    tiktok_app_secret: Optional[str] = Field(
        default=None,
        validation_alias="TIKTOK_APP_SECRET"
    )
    tiktok_access_token: Optional[str] = Field(
        default=None,
        validation_alias="TIKTOK_ACCESS_TOKEN"
    )

    # Lead Enrichment APIs
    clearbit_api_key: Optional[str] = Field(
        default=None,
        validation_alias="CLEARBIT_API_KEY"
    )
    hunter_api_key: Optional[str] = Field(
        default=None,
        validation_alias="HUNTER_API_KEY"
    )
    zoominfo_api_key: Optional[str] = Field(
        default=None,
        validation_alias="ZOOMINFO_API_KEY"
    )

    # Email Configuration
    smtp_host: str = Field(default="smtp.gmail.com", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, validation_alias="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, validation_alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(
        default="noreply@nexus.com",
        validation_alias="SMTP_FROM_EMAIL"
    )

    # File Storage
    upload_dir: str = Field(
        default="uploads",
        validation_alias="UPLOAD_DIR"
    )
    max_file_size: int = Field(
        default=10485760,  # 10MB
        validation_alias="MAX_FILE_SIZE"
    )
    allowed_file_types: list[str] = Field(
        default=["image/jpeg", "image/png", "image/gif", "video/mp4", "application/pdf"],
        validation_alias="ALLOWED_FILE_TYPES"
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=60,
        validation_alias="RATE_LIMIT_PER_MINUTE"
    )
    rate_limit_per_hour: int = Field(
        default=1000,
        validation_alias="RATE_LIMIT_PER_HOUR"
    )

    # Pagination
    default_page_size: int = Field(
        default=20,
        validation_alias="DEFAULT_PAGE_SIZE"
    )
    max_page_size: int = Field(
        default=100,
        validation_alias="MAX_PAGE_SIZE"
    )

    # Logging
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        validation_alias="LOG_FORMAT"
    )

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501"],
        validation_alias="CORS_ORIGINS"
    )

    @field_validator("allowed_hosts", "allowed_file_types", "cors_origins", mode="before")
    @classmethod
    def parse_list_from_string(cls, v):
        """Parse comma-separated string into list."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v


# Global settings instance
settings = Settings()
