"""
Configuration management for NEXUS platform.

This module handles all application settings using Pydantic Settings,
loading from environment variables and .env files.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = Field(default="NEXUS Platform", description="Application name")
    APP_VERSION: str = Field(default="0.1.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 prefix")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://nexus_user:nexus_password@localhost:5432/nexus_db",
        description="Database connection URL",
    )
    DB_ECHO: bool = Field(default=False, description="Echo SQL queries")
    DB_POOL_SIZE: int = Field(default=10, description="Database pool size")
    DB_MAX_OVERFLOW: int = Field(default=20, description="Database max overflow")
    TEST_DATABASE_URL: str = Field(
        default="sqlite:///./test.db", description="Test database URL"
    )

    # Security
    SECRET_KEY: str = Field(
        default="change-this-in-production-use-strong-secret-key-minimum-32-chars",
        description="Secret key for JWT",
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="Access token expiration in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="Refresh token expiration in days"
    )

    # Password requirements
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Minimum password length")
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(
        default=True, description="Require uppercase in password"
    )
    PASSWORD_REQUIRE_LOWERCASE: bool = Field(
        default=True, description="Require lowercase in password"
    )
    PASSWORD_REQUIRE_NUMBERS: bool = Field(
        default=True, description="Require numbers in password"
    )
    PASSWORD_REQUIRE_SPECIAL: bool = Field(
        default=True, description="Require special chars in password"
    )

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_CACHE_TTL: int = Field(default=3600, description="Redis cache TTL in seconds")

    # Celery
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/2", description="Celery broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/3", description="Celery result backend"
    )

    # Storage
    STORAGE_BACKEND: str = Field(default="local", description="Storage backend type")
    STORAGE_PATH: str = Field(default="./storage", description="Storage path")
    MAX_UPLOAD_SIZE: int = Field(default=104857600, description="Max upload size (100MB)")
    CHUNK_SIZE: int = Field(default=5242880, description="Upload chunk size (5MB)")

    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, description="AWS access key")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, description="AWS secret key")
    AWS_S3_BUCKET_NAME: Optional[str] = Field(default=None, description="S3 bucket name")
    AWS_S3_REGION: str = Field(default="us-east-1", description="S3 region")
    AWS_S3_ENDPOINT_URL: Optional[str] = Field(
        default=None, description="S3 endpoint URL"
    )

    # Azure Blob Storage
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = Field(
        default=None, description="Azure connection string"
    )
    AZURE_STORAGE_CONTAINER: Optional[str] = Field(
        default=None, description="Azure container"
    )

    # Google Cloud Storage
    GCS_BUCKET_NAME: Optional[str] = Field(default=None, description="GCS bucket name")
    GCS_PROJECT_ID: Optional[str] = Field(default=None, description="GCS project ID")
    GCS_CREDENTIALS_PATH: Optional[str] = Field(
        default=None, description="GCS credentials path"
    )

    # AI/LLM
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API key")
    ANTHROPIC_MODEL: str = Field(
        default="claude-3-5-sonnet-20241022", description="Anthropic model"
    )
    ANTHROPIC_MAX_TOKENS: int = Field(default=4096, description="Max tokens for AI")
    ANTHROPIC_TEMPERATURE: float = Field(default=0.7, description="AI temperature")

    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-4-turbo-preview", description="OpenAI model")

    # AI Features
    AI_SUMMARIZATION_ENABLED: bool = Field(
        default=True, description="Enable AI summarization"
    )
    AI_CLASSIFICATION_ENABLED: bool = Field(
        default=True, description="Enable AI classification"
    )
    AI_ENTITY_EXTRACTION_ENABLED: bool = Field(
        default=True, description="Enable AI entity extraction"
    )

    # Search
    SEARCH_BACKEND: str = Field(default="postgresql", description="Search backend")
    ELASTICSEARCH_HOST: str = Field(default="localhost", description="ES host")
    ELASTICSEARCH_PORT: int = Field(default=9200, description="ES port")
    ELASTICSEARCH_INDEX_PREFIX: str = Field(default="nexus_", description="ES index prefix")
    SEARCH_MAX_RESULTS: int = Field(default=100, description="Max search results")

    # Document processing
    OCR_ENABLED: bool = Field(default=True, description="Enable OCR")
    OCR_LANGUAGE: str = Field(default="eng", description="OCR language")
    TESSERACT_PATH: str = Field(default="/usr/bin/tesseract", description="Tesseract path")

    IMAGE_MAX_SIZE: int = Field(default=4096, description="Max image size")
    IMAGE_THUMBNAIL_SIZE: int = Field(default=256, description="Thumbnail size")
    IMAGE_QUALITY: int = Field(default=85, description="Image quality")

    PDF_MAX_PAGES: int = Field(default=1000, description="Max PDF pages")
    PDF_DPI: int = Field(default=300, description="PDF DPI")

    # Email
    SMTP_HOST: str = Field(default="smtp.gmail.com", description="SMTP host")
    SMTP_PORT: int = Field(default=587, description="SMTP port")
    SMTP_USERNAME: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")
    SMTP_FROM_EMAIL: str = Field(
        default="noreply@nexus-platform.com", description="From email"
    )
    SMTP_USE_TLS: bool = Field(default=True, description="Use TLS")

    # Document management
    VERSION_CONTROL_ENABLED: bool = Field(
        default=True, description="Enable version control"
    )
    VERSION_MAX_HISTORY: int = Field(default=100, description="Max version history")
    LOCK_TIMEOUT: int = Field(default=3600, description="Lock timeout in seconds")
    DEFAULT_SHARE_EXPIRATION_DAYS: int = Field(
        default=30, description="Default share expiration"
    )
    RETENTION_ENABLED: bool = Field(default=True, description="Enable retention policies")
    AUDIT_LOG_RETENTION_DAYS: int = Field(
        default=2555, description="Audit log retention (7 years)"
    )
    DEDUPLICATION_ENABLED: bool = Field(
        default=True, description="Enable deduplication"
    )

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:8501", "http://localhost:3000"],
        description="CORS origins",
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    LOG_FORMAT: str = Field(default="json", description="Log format")
    LOG_FILE_PATH: str = Field(default="./logs/nexus.log", description="Log file path")
    LOG_FILE_MAX_SIZE: int = Field(default=10485760, description="Log file max size")
    LOG_FILE_BACKUP_COUNT: int = Field(default=5, description="Log file backup count")

    # Frontend
    BACKEND_API_URL: str = Field(
        default="http://localhost:8000", description="Backend API URL"
    )
    STREAMLIT_SERVER_PORT: int = Field(default=8501, description="Streamlit port")

    # WebSocket
    WEBSOCKET_ENABLED: bool = Field(default=True, description="Enable WebSocket")
    WEBSOCKET_HOST: str = Field(default="localhost", description="WebSocket host")
    WEBSOCKET_PORT: int = Field(default=8001, description="WebSocket port")

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60, description="Rate limit per minute"
    )

    # Testing
    TESTING: bool = Field(default=False, description="Testing mode")

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

    @property
    def database_url_async(self) -> str:
        """Get async database URL for PostgreSQL."""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        return self.DATABASE_URL


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()
