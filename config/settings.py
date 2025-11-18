"""
NEXUS Platform Settings

Centralized configuration management using Pydantic Settings.
All settings are loaded from environment variables with sensible defaults.
"""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ========================================================================
    # Application Settings
    # ========================================================================
    APP_NAME: str = "NEXUS Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = Field(..., description="Secret key for encryption")
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Get allowed hosts as a list."""
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]

    # ========================================================================
    # Database Configuration
    # ========================================================================
    DATABASE_URL: str = Field(
        default="postgresql://nexus_user:password@localhost:5432/nexus_db",
        description="PostgreSQL database URL",
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    # ========================================================================
    # Redis Configuration
    # ========================================================================
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_DB: int = 0
    REDIS_CELERY_DB: int = 1
    REDIS_MAX_CONNECTIONS: int = 50

    # ========================================================================
    # Celery Configuration
    # ========================================================================
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: str = "json"
    CELERY_TIMEZONE: str = "UTC"

    # ========================================================================
    # Authentication & Security
    # ========================================================================
    JWT_SECRET_KEY: str = Field(
        default="change-this-secret-key", description="JWT secret key"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8
    BCRYPT_ROUNDS: int = 12

    # ========================================================================
    # AI & LLM Configuration
    # ========================================================================
    # Claude (Anthropic)
    ANTHROPIC_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    CLAUDE_MAX_TOKENS: int = 4096
    CLAUDE_TEMPERATURE: float = 0.7

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.7

    # ========================================================================
    # Translation Services Configuration
    # ========================================================================
    DEFAULT_TRANSLATION_ENGINE: str = "deepl"

    # Google Translate
    GOOGLE_TRANSLATE_API_KEY: Optional[str] = None
    GOOGLE_TRANSLATE_PROJECT_ID: Optional[str] = None

    # DeepL
    DEEPL_API_KEY: Optional[str] = None
    DEEPL_API_URL: str = "https://api-free.deepl.com/v2"

    # Azure Translator
    AZURE_TRANSLATOR_KEY: Optional[str] = None
    AZURE_TRANSLATOR_REGION: str = "eastus"
    AZURE_TRANSLATOR_ENDPOINT: str = (
        "https://api.cognitive.microsofttranslator.com"
    )

    # AWS Translate
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_TRANSLATE_ENDPOINT: str = "https://translate.us-east-1.amazonaws.com"

    # Translation Settings
    TRANSLATION_CACHE_TTL: int = 86400
    TRANSLATION_MAX_BATCH_SIZE: int = 100
    TRANSLATION_TIMEOUT_SECONDS: int = 30
    ENABLE_AUTO_LANGUAGE_DETECTION: bool = True
    ENABLE_TRANSLATION_MEMORY: bool = True
    ENABLE_GLOSSARY: bool = True
    TRANSLATION_QUALITY_THRESHOLD: float = 0.7

    # ========================================================================
    # File Storage Configuration
    # ========================================================================
    STORAGE_PROVIDER: str = "local"
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_UPLOAD_EXTENSIONS: str = ".pdf,.docx,.xlsx,.pptx,.txt,.html,.json,.xml"

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get allowed extensions as a list."""
        return [ext.strip() for ext in self.ALLOWED_UPLOAD_EXTENSIONS.split(",")]

    # AWS S3
    S3_BUCKET_NAME: str = "nexus-documents"
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None

    # Azure Blob Storage
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_STORAGE_CONTAINER: str = "nexus-documents"

    # Google Cloud Storage
    GCS_BUCKET_NAME: str = "nexus-documents"
    GCS_PROJECT_ID: Optional[str] = None
    GCS_CREDENTIALS_PATH: Optional[str] = None

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "nexus-documents"
    MINIO_SECURE: bool = False

    # ========================================================================
    # Email Configuration
    # ========================================================================
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@nexus-platform.com"
    SMTP_FROM_NAME: str = "NEXUS Platform"
    SMTP_USE_TLS: bool = True

    # ========================================================================
    # WebSocket Configuration
    # ========================================================================
    WEBSOCKET_HOST: str = "0.0.0.0"
    WEBSOCKET_PORT: int = 8001
    WEBSOCKET_MAX_CONNECTIONS: int = 1000
    WEBSOCKET_PING_INTERVAL: int = 30
    WEBSOCKET_PING_TIMEOUT: int = 10

    # ========================================================================
    # API Configuration
    # ========================================================================
    API_V1_PREFIX: str = "/api/v1"
    API_DOCS_URL: str = "/docs"
    API_REDOC_URL: str = "/redoc"
    API_RATE_LIMIT_PER_MINUTE: int = 60
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8501"

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # ========================================================================
    # Monitoring & Analytics
    # ========================================================================
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "production"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090

    ENABLE_ANALYTICS: bool = True
    ANALYTICS_RETENTION_DAYS: int = 90

    # ========================================================================
    # Feature Flags
    # ========================================================================
    ENABLE_TRANSLATION_MODULE: bool = True
    ENABLE_DOCUMENT_PROCESSING: bool = True
    ENABLE_AI_TRANSLATION: bool = True
    ENABLE_BATCH_TRANSLATION: bool = True
    ENABLE_STREAMING_TRANSLATION: bool = True
    ENABLE_QUALITY_ASSESSMENT: bool = True
    ENABLE_TRANSLATION_MEMORY: bool = True
    ENABLE_GLOSSARY_MANAGEMENT: bool = True
    ENABLE_AUTO_DETECTION: bool = True
    ENABLE_BACK_TRANSLATION: bool = True
    ENABLE_CONTEXT_ANALYSIS: bool = True

    # ========================================================================
    # Development Settings
    # ========================================================================
    RELOAD: bool = False
    LOG_FORMAT: str = "json"
    LOG_OUTPUT: str = "stdout"

    # Testing
    TEST_DATABASE_URL: str = (
        "postgresql://nexus_test:password@localhost:5432/nexus_test_db"
    )

    @field_validator("TRANSLATION_QUALITY_THRESHOLD")
    @classmethod
    def validate_quality_threshold(cls, v: float) -> float:
        """Validate quality threshold is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Quality threshold must be between 0 and 1")
        return v

    @field_validator("PASSWORD_MIN_LENGTH")
    @classmethod
    def validate_password_length(cls, v: int) -> int:
        """Validate password minimum length."""
        if v < 8:
            raise ValueError("Password minimum length must be at least 8")
        return v


# Global settings instance
settings = Settings()
