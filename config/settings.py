"""
Configuration settings for NEXUS Platform.

This module manages all application configuration using Pydantic BaseSettings,
which automatically loads values from environment variables.
"""
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        app_name: Application name
        debug: Debug mode flag
        environment: Environment (development, staging, production)
        secret_key: Secret key for JWT and encryption
        allowed_origins: CORS allowed origins
        database_url: PostgreSQL connection string
        redis_url: Redis connection string
        anthropic_api_key: Anthropic/Claude API key
        openai_api_key: OpenAI API key (optional)
        smtp_host: SMTP server host
        smtp_port: SMTP server port
        smtp_user: SMTP username
        smtp_password: SMTP password
        smtp_from_email: Default from email address
        sendgrid_api_key: SendGrid API key (optional)
        twilio_account_sid: Twilio account SID (optional)
        twilio_auth_token: Twilio auth token (optional)
        twilio_phone_number: Twilio phone number (optional)
        jwt_algorithm: JWT signing algorithm
        access_token_expire_minutes: JWT access token expiration
        refresh_token_expire_days: JWT refresh token expiration
        sentry_dsn: Sentry DSN for error tracking (optional)
    """

    # Application Settings
    app_name: str = Field(default="NEXUS Platform", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment")
    secret_key: str = Field(..., description="Secret key for encryption")
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501"],
        description="CORS allowed origins"
    )

    # Database Settings
    database_url: str = Field(..., description="PostgreSQL connection URL")
    database_pool_size: int = Field(default=5, description="Database connection pool size")
    database_max_overflow: int = Field(default=10, description="Max database overflow connections")

    # Redis Settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # AI/LLM Settings
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    llm_default_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Default LLM model"
    )
    llm_max_tokens: int = Field(default=4096, description="Max tokens for LLM responses")
    llm_temperature: float = Field(default=0.7, description="LLM temperature")

    # Email Settings
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP host")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_user: str = Field(..., description="SMTP username")
    smtp_password: str = Field(..., description="SMTP password")
    smtp_from_email: str = Field(..., description="Default from email")
    smtp_from_name: str = Field(default="NEXUS Platform", description="Default from name")
    sendgrid_api_key: Optional[str] = Field(default=None, description="SendGrid API key")

    # SMS Settings (Twilio)
    twilio_account_sid: Optional[str] = Field(default=None, description="Twilio account SID")
    twilio_auth_token: Optional[str] = Field(default=None, description="Twilio auth token")
    twilio_phone_number: Optional[str] = Field(default=None, description="Twilio phone number")

    # JWT Settings
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration in days"
    )

    # Celery Settings
    celery_broker_url: Optional[str] = Field(default=None, description="Celery broker URL")
    celery_result_backend: Optional[str] = Field(
        default=None,
        description="Celery result backend"
    )

    # Monitoring Settings
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")
    log_level: str = Field(default="INFO", description="Logging level")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, description="API rate limit per minute")

    # Campaign Settings
    campaign_batch_size: int = Field(
        default=100,
        description="Batch size for campaign email sending"
    )
    campaign_send_rate_per_second: int = Field(
        default=10,
        description="Max emails to send per second"
    )

    @validator("celery_broker_url", pre=True, always=True)
    def set_celery_broker(cls, v: Optional[str], values: dict) -> str:
        """Set Celery broker URL from Redis URL if not provided."""
        return v or values.get("redis_url", "redis://localhost:6379/0")

    @validator("celery_result_backend", pre=True, always=True)
    def set_celery_backend(cls, v: Optional[str], values: dict) -> str:
        """Set Celery result backend from Redis URL if not provided."""
        return v or values.get("redis_url", "redis://localhost:6379/0")

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"


# Global settings instance
settings = Settings()
