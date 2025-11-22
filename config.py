"""
Configuration management for NEXUS platform.
"""
<<<<<<< HEAD
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, RedisDsn


class Settings(BaseSettings):
    """Application settings."""
=======
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
<<<<<<< HEAD
        extra="ignore",
    )

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql://user:password@localhost:5432/nexus_db",
        description="PostgreSQL database URL",
    )
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching and task queue",
    )

    # API Keys
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")

    # Social Media
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_access_token: Optional[str] = None
    twitter_access_secret: Optional[str] = None

=======
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
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi
    facebook_app_id: Optional[str] = None
    facebook_app_secret: Optional[str] = None
    facebook_access_token: Optional[str] = None

<<<<<<< HEAD
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None

    # Email
    sendgrid_api_key: Optional[str] = None
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None

    # Application
    secret_key: str = Field(default="your-secret-key-change-in-production")
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")

    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/0")

    # Media
    media_root: str = Field(default="/app/media")
    max_upload_size: int = Field(default=10485760)  # 10MB

    # WebSocket
    websocket_port: int = Field(default=8001)

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501"]
    )


settings = Settings()
=======
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
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi
