<<<<<<< HEAD
"""Configuration management for NEXUS platform."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # Database
    POSTGRES_USER: str = "nexus"
    POSTGRES_PASSWORD: str = "nexus_password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "nexus_db"
    DATABASE_URL: str = "postgresql://nexus:nexus_password@localhost:5432/nexus_db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # API
    API_SECRET_KEY: str = "your-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # OAuth
    OAUTH_ENCRYPTION_KEY: str = "your-oauth-encryption-key-32-chars"
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    SLACK_CLIENT_ID: str = ""
    SLACK_CLIENT_SECRET: str = ""

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True
=======
"""
NEXUS Platform - Configuration Management

Centralized configuration using Pydantic Settings for type-safe
environment variable management.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    url: str = Field(
        default="postgresql://nexus:nexus@localhost:5432/nexus_analytics",
        description="PostgreSQL database URL",
    )
    pool_size: int = Field(default=20, ge=1, le=100)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_timeout: int = Field(default=30, ge=1)
    pool_recycle: int = Field(default=3600, ge=60)
    echo: bool = Field(default=False, description="Echo SQL statements")

    model_config = SettingsConfigDict(env_prefix="DATABASE_")


class RedisSettings(BaseSettings):
    """Redis cache configuration settings."""

    url: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    max_connections: int = Field(default=50, ge=1)
    socket_timeout: int = Field(default=5, ge=1)
    socket_connect_timeout: int = Field(default=5, ge=1)
    decode_responses: bool = Field(default=True)

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class CelerySettings(BaseSettings):
    """Celery task queue configuration settings."""

    broker_url: str = Field(
        default="redis://localhost:6379/1", description="Celery broker URL"
    )
    result_backend: str = Field(
        default="redis://localhost:6379/2", description="Celery result backend"
    )
    task_always_eager: bool = Field(default=False)
    task_serializer: str = Field(default="json")
    result_serializer: str = Field(default="json")
    timezone: str = Field(default="UTC")
    enable_utc: bool = Field(default=True)

    model_config = SettingsConfigDict(env_prefix="CELERY_")


class InfluxDBSettings(BaseSettings):
    """InfluxDB time-series database configuration."""

    url: str = Field(default="http://localhost:8086", description="InfluxDB URL")
    token: str = Field(default="", description="InfluxDB authentication token")
    org: str = Field(default="nexus", description="InfluxDB organization")
    bucket: str = Field(default="analytics", description="InfluxDB bucket")
    timeout: int = Field(default=10000, description="Request timeout in milliseconds")

    model_config = SettingsConfigDict(env_prefix="INFLUXDB_")


class AnalyticsSettings(BaseSettings):
    """Analytics module configuration settings."""

    enabled: bool = Field(default=True, description="Enable analytics tracking")
    batch_size: int = Field(default=1000, ge=1, le=10000)
    flush_interval: int = Field(
        default=60, ge=1, description="Flush interval in seconds"
    )
    retention_days: int = Field(default=90, ge=1, le=3650)
    max_events_per_minute: int = Field(default=10000, ge=100)
    enable_real_time: bool = Field(default=True, description="Enable real-time processing")
    session_timeout: int = Field(
        default=1800, ge=60, description="Session timeout in seconds"
    )

    model_config = SettingsConfigDict(env_prefix="ANALYTICS_")


class AISettings(BaseSettings):
    """AI integration configuration settings."""

    claude_api_key: str = Field(default="", description="Claude API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    model: str = Field(
        default="claude-3-5-sonnet-20241022", description="Default AI model"
    )
    max_tokens: int = Field(default=4096, ge=1, le=200000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    enable_predictive_insights: bool = Field(default=True)

    model_config = SettingsConfigDict(env_prefix="")

    @field_validator("claude_api_key", "openai_api_key")
    @classmethod
    def validate_api_keys(cls, v: str, info: dict) -> str:
        """Validate API keys are set in production."""
        field_name = info.field_name
        env = os.getenv("ENVIRONMENT", "development")
        if env == "production" and not v:
            raise ValueError(f"{field_name} must be set in production environment")
        return v


class APISettings(BaseSettings):
    """FastAPI configuration settings."""

    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=4, ge=1, le=32)
    reload: bool = Field(default=False, description="Enable auto-reload")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501"]
    )
    rate_limit: int = Field(default=100, ge=1, description="Rate limit per minute")

    model_config = SettingsConfigDict(env_prefix="API_")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


class StreamlitSettings(BaseSettings):
    """Streamlit UI configuration settings."""

    server_port: int = Field(default=8501, ge=1, le=65535)
    server_address: str = Field(default="0.0.0.0")
    server_headless: bool = Field(default=True)
    browser_gather_usage_stats: bool = Field(default=False)

    model_config = SettingsConfigDict(env_prefix="STREAMLIT_")


class FeatureFlags(BaseSettings):
    """Feature flags configuration."""

    session_replay: bool = Field(default=True, description="Enable session replay")
    heatmaps: bool = Field(default=True, description="Enable heatmaps")
    ab_testing: bool = Field(default=True, description="Enable A/B testing")
    predictive_analytics: bool = Field(
        default=True, description="Enable predictive analytics"
    )
    custom_dashboards: bool = Field(default=True, description="Enable custom dashboards")
    data_export: bool = Field(default=True, description="Enable data export")

    model_config = SettingsConfigDict(env_prefix="FEATURE_")


class ExportSettings(BaseSettings):
    """Data export configuration settings."""

    max_rows: int = Field(default=1000000, ge=1)
    formats: List[str] = Field(default=["csv", "json", "excel", "pdf"])
    timeout: int = Field(default=300, ge=1, description="Export timeout in seconds")

    model_config = SettingsConfigDict(env_prefix="EXPORT_")

    @field_validator("formats", mode="before")
    @classmethod
    def parse_formats(cls, v: str | List[str]) -> List[str]:
        """Parse export formats from string or list."""
        if isinstance(v, str):
            return [fmt.strip().lower() for fmt in v.split(",")]
        return v


class SecuritySettings(BaseSettings):
    """Security configuration settings."""

    secret_key: str = Field(
        default="change-me-in-production", description="Application secret key"
    )
    jwt_secret_key: str = Field(
        default="jwt-secret-key", description="JWT secret key"
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=24, ge=1)
    cors_allowed_origins: str = Field(default="*")
    allowed_hosts: str = Field(default="localhost,127.0.0.1")

    model_config = SettingsConfigDict(env_prefix="")


class Settings(BaseSettings):
    """Main application settings."""

    environment: str = Field(
        default="development",
        description="Application environment",
        pattern="^(development|staging|production)$",
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
    )

    # Nested settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    influxdb: InfluxDBSettings = Field(default_factory=InfluxDBSettings)
    analytics: AnalyticsSettings = Field(default_factory=AnalyticsSettings)
    ai: AISettings = Field(default_factory=AISettings)
    api: APISettings = Field(default_factory=APISettings)
    streamlit: StreamlitSettings = Field(default_factory=StreamlitSettings)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    export: ExportSettings = Field(default_factory=ExportSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    def validate_production_config(self) -> None:
        """Validate production-specific configuration."""
        if self.is_production:
            if self.security.secret_key == "change-me-in-production":
                raise ValueError("SECRET_KEY must be changed in production")
            if not self.ai.claude_api_key and not self.ai.openai_api_key:
                raise ValueError("At least one AI API key must be set in production")
>>>>>>> origin/claude/nexus-analytics-module-01FAKqqMpzB1WpxsYvosEHzE


@lru_cache()
def get_settings() -> Settings:
<<<<<<< HEAD
    """Get cached settings instance."""
    return Settings()
=======
    """
    Get cached application settings.

    Returns:
        Settings: Application settings instance

    Example:
        >>> settings = get_settings()
        >>> print(settings.database.url)
        postgresql://nexus:nexus@localhost:5432/nexus_analytics
    """
    settings = Settings()

    # Validate production configuration
    if settings.is_production:
        settings.validate_production_config()

    return settings


# Convenience function to reload settings (useful for testing)
def reload_settings() -> Settings:
    """
    Reload settings by clearing the cache.

    Returns:
        Settings: Fresh settings instance
    """
    get_settings.cache_clear()
    return get_settings()
>>>>>>> origin/claude/nexus-analytics-module-01FAKqqMpzB1WpxsYvosEHzE
