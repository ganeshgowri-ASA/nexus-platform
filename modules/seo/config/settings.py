"""
Application settings and configuration management.

This module handles all configuration settings for the SEO tools module,
including database, Redis, Celery, API keys, and feature flags.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be configured via environment variables or .env file.
    Provides type validation and default values for all configuration options.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/nexus_seo",
        description="PostgreSQL database connection URL",
    )
    database_pool_size: int = Field(default=20, ge=1, le=100)
    database_max_overflow: int = Field(default=10, ge=0, le=50)

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching",
    )
    redis_cache_ttl: int = Field(default=3600, ge=60, description="Cache TTL in seconds")

    # Celery Configuration
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL",
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL",
    )

    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1024, le=65535)
    api_reload: bool = Field(default=False)
    api_workers: int = Field(default=4, ge=1, le=32)

    # Security
    secret_key: str = Field(
        default="change-this-secret-key-in-production",
        min_length=32,
        description="Secret key for JWT tokens",
    )
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)

    # AI/LLM Configuration
    anthropic_api_key: Optional[str] = Field(default=None)
    openai_api_key: Optional[str] = Field(default=None)
    ai_model: str = Field(default="claude-sonnet-4.5")

    # Google Search Console API
    google_client_id: Optional[str] = Field(default=None)
    google_client_secret: Optional[str] = Field(default=None)
    google_redirect_uri: str = Field(
        default="http://localhost:8000/auth/google/callback"
    )

    # Third-party SEO APIs
    semrush_api_key: Optional[str] = Field(default=None)
    ahrefs_api_key: Optional[str] = Field(default=None)
    moz_access_id: Optional[str] = Field(default=None)
    moz_secret_key: Optional[str] = Field(default=None)
    screaming_frog_api_key: Optional[str] = Field(default=None)

    # Streamlit Configuration
    streamlit_server_port: int = Field(default=8501, ge=1024, le=65535)
    streamlit_server_address: str = Field(default="0.0.0.0")

    # Logging Configuration
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    log_file: str = Field(default="logs/seo.log")

    # SEO Configuration
    default_user_agent: str = Field(
        default="Mozilla/5.0 (compatible; NEXUS-SEO-Bot/1.0)"
    )
    max_crawl_depth: int = Field(default=3, ge=1, le=10)
    max_pages_per_crawl: int = Field(default=1000, ge=1, le=100000)
    crawl_delay: float = Field(default=1.0, ge=0.1, le=10.0)

    # Performance
    max_concurrent_requests: int = Field(default=10, ge=1, le=100)
    request_timeout: int = Field(default=30, ge=5, le=300)
    cache_enabled: bool = Field(default=True)

    # Feature Flags
    enable_ai_recommendations: bool = Field(default=True)
    enable_auto_reporting: bool = Field(default=True)
    enable_real_time_tracking: bool = Field(default=True)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format is either 'json' or 'text'."""
        valid_formats = ["json", "text"]
        v_lower = v.lower()
        if v_lower not in valid_formats:
            raise ValueError(f"log_format must be one of {valid_formats}")
        return v_lower

    class Config:
        """Pydantic configuration."""

        validate_assignment = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings instance

    Note:
        Settings are cached to avoid reading environment variables multiple times.
    """
    return Settings()
