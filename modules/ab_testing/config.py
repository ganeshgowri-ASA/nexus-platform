"""Configuration management for A/B testing module."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    database_url: PostgresDsn = Field(
        default="postgresql://nexus:password@localhost:5432/nexus_db",
        description="PostgreSQL database URL",
    )
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=20, ge=0, le=100)

    # Redis Configuration
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    redis_max_connections: int = Field(default=50, ge=1, le=1000)

    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_reload: bool = Field(default=True)
    api_workers: int = Field(default=4, ge=1, le=16)

    # Security
    secret_key: str = Field(
        default="change-this-in-production",
        min_length=32,
        description="Secret key for JWT encoding",
    )
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)

    # A/B Testing Configuration
    ab_test_default_confidence_level: float = Field(
        default=0.95,
        ge=0.8,
        le=0.99,
        description="Default confidence level for statistical tests",
    )
    ab_test_min_sample_size: int = Field(
        default=100,
        ge=10,
        description="Minimum sample size per variant",
    )
    ab_test_auto_winner_enabled: bool = Field(
        default=True,
        description="Enable automatic winner detection",
    )
    ab_test_auto_winner_threshold: float = Field(
        default=0.95,
        ge=0.8,
        le=0.99,
        description="Confidence threshold for auto winner selection",
    )

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # Environment
    environment: str = Field(default="development")

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> str:
        """Validate and convert database URL."""
        if v is None:
            return "postgresql://nexus:password@localhost:5432/nexus_db"
        return str(v)

    @field_validator("redis_url", mode="before")
    @classmethod
    def validate_redis_url(cls, v: Optional[str]) -> str:
        """Validate and convert Redis URL."""
        if v is None:
            return "redis://localhost:6379/0"
        return str(v)

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()
