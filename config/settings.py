<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
"""
<<<<<<< HEAD
Nexus Platform Configuration Settings
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application Settings
    APP_NAME: str = "Nexus Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 30 * 60  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = 25 * 60  # 25 minutes

    # Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@nexus-platform.com"
    SMTP_USE_TLS: bool = True

    # AI Configuration
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    AI_MODEL_CLAUDE: str = "claude-3-5-sonnet-20241022"
    AI_MODEL_GPT: str = "gpt-4-turbo-preview"

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./nexus.db"

    # File Upload Settings
    MAX_FILE_SIZE_MB: int = 100
    UPLOAD_DIR: Path = Path("./uploads")
    TEMP_DIR: Path = Path("./temp")
    LOGS_DIR: Path = Path("./logs")

    # Task Queue Settings
    TASK_QUEUE_EMAIL: str = "email_queue"
    TASK_QUEUE_FILE_PROCESSING: str = "file_processing_queue"
    TASK_QUEUE_AI: str = "ai_queue"
    TASK_QUEUE_REPORTS: str = "reports_queue"
    TASK_QUEUE_DEFAULT: str = "default_queue"

    class Config:
        env_file = ".env"
        case_sensitive = True
=======
Application settings and configuration
"""
import os
from typing import Dict, Any


class Settings:
    """Application settings"""

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nexus.db")

    # Email configuration
    EMAIL_CONFIG: Dict[str, Any] = {
        "backend": os.getenv("EMAIL_BACKEND", "smtp"),  # smtp, sendgrid, ses
        "smtp_host": os.getenv("SMTP_HOST", "localhost"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_user": os.getenv("SMTP_USER", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "smtp_use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        "from_email": os.getenv("EMAIL_FROM", "noreply@nexus.com"),
        "from_name": os.getenv("EMAIL_FROM_NAME", "NEXUS Platform"),
        "sendgrid_api_key": os.getenv("SENDGRID_API_KEY", ""),
        "aws_region": os.getenv("AWS_REGION", "us-east-1"),
    }

    # SMS configuration
    SMS_CONFIG: Dict[str, Any] = {
        "backend": os.getenv("SMS_BACKEND", "twilio"),  # twilio, sns
        "twilio_account_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
        "twilio_auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
        "twilio_from_number": os.getenv("TWILIO_FROM_NUMBER", ""),
        "aws_region": os.getenv("AWS_REGION", "us-east-1"),
        "sns_sender_id": os.getenv("SNS_SENDER_ID", "NEXUS"),
    }

    # Push notification configuration
    PUSH_CONFIG: Dict[str, Any] = {
        "backend": os.getenv("PUSH_BACKEND", "fcm"),  # fcm, apns
        "fcm_server_key": os.getenv("FCM_SERVER_KEY", ""),
        "fcm_credentials_path": os.getenv("FCM_CREDENTIALS_PATH", ""),
        "fcm_project_id": os.getenv("FCM_PROJECT_ID", ""),
        "apns_certificate_path": os.getenv("APNS_CERTIFICATE_PATH", ""),
        "apns_key_id": os.getenv("APNS_KEY_ID", ""),
        "apns_team_id": os.getenv("APNS_TEAM_ID", ""),
    }

    # In-app notification configuration
    IN_APP_CONFIG: Dict[str, Any] = {
        "ttl_days": int(os.getenv("IN_APP_TTL_DAYS", "30")),
        "max_notifications_per_user": int(os.getenv("IN_APP_MAX_PER_USER", "100")),
    }

    # Notification service configuration
    NOTIFICATION_CONFIG: Dict[str, Any] = {
        "email": EMAIL_CONFIG,
        "sms": SMS_CONFIG,
        "push": PUSH_CONFIG,
        "in_app": IN_APP_CONFIG,
    }

    # Scheduler configuration
    SCHEDULER_CHECK_INTERVAL = int(os.getenv("SCHEDULER_CHECK_INTERVAL", "60"))

    # Unsubscribe token configuration
    UNSUBSCRIBE_TOKEN_EXPIRY_DAYS = int(os.getenv("UNSUBSCRIBE_TOKEN_EXPIRY_DAYS", "90"))

    # Application settings
    APP_NAME = "NEXUS Platform"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
>>>>>>> origin/claude/multi-channel-notifications-01WeNhyLeSWZWAjx7hyDqB6q


# Create settings instance
settings = Settings()
<<<<<<< HEAD

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
=======
>>>>>>> origin/claude/multi-channel-notifications-01WeNhyLeSWZWAjx7hyDqB6q
=======
import os
from pathlib import Path
=======
"""Configuration settings for NEXUS platform."""
import os
from typing import Optional
>>>>>>> origin/claude/excel-spreadsheet-editor-01ERQuTgtV3Kb8CMNgURhB2E
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

<<<<<<< HEAD
class Settings:
    """Application settings and configuration"""

    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    UPLOADS_DIR = DATA_DIR / "uploads"
    EXPORTS_DIR = DATA_DIR / "exports"

    # AI Configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/nexus.db")

    # Application Configuration
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = ENVIRONMENT == "development"
    SECRET_KEY = os.getenv("SECRET_KEY", "nexus-secret-key-change-in-production")

    # WebRTC Configuration
    WEBRTC_ICE_SERVERS = [
        {"urls": ["stun:stun.l.google.com:19302"]},
        {"urls": ["stun:stun1.l.google.com:19302"]},
    ]

    # File Upload Limits
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
    ALLOWED_EXTENSIONS = {
        'images': {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg'},
        'documents': {'.pdf', '.doc', '.docx', '.txt', '.md'},
        'presentations': {'.ppt', '.pptx'},
        'spreadsheets': {'.xls', '.xlsx', '.csv'},
        'archives': {'.zip', '.tar', '.gz'},
    }

    # Email Configuration
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

    # Application Features
    ENABLE_AI_FEATURES = os.getenv("ENABLE_AI_FEATURES", "true").lower() == "true"
    ENABLE_EXPORT = os.getenv("ENABLE_EXPORT", "true").lower() == "true"
    ENABLE_FILE_SHARING = os.getenv("ENABLE_FILE_SHARING", "true").lower() == "true"

    def __init__(self):
        """Create necessary directories on initialization"""
        self.DATA_DIR.mkdir(exist_ok=True)
        self.UPLOADS_DIR.mkdir(exist_ok=True)
        self.EXPORTS_DIR.mkdir(exist_ok=True)

# Create singleton instance
settings = Settings()
>>>>>>> origin/claude/productivity-suite-ai-01Uq8q3V9EdvDAuMPqDoBxZh
=======
"""Global settings for NEXUS platform."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Global application settings."""

    # Application
    APP_NAME: str = "NEXUS Platform"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # API Keys
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/nexus"
    )
    SQLALCHEMY_ECHO: bool = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    # Airflow
    AIRFLOW_HOME: str = os.getenv("AIRFLOW_HOME", "./airflow")
    AIRFLOW_API_URL: str = os.getenv("AIRFLOW_API_URL", "http://localhost:8080/api/v1")
    AIRFLOW_USERNAME: str = os.getenv("AIRFLOW_USERNAME", "admin")
    AIRFLOW_PASSWORD: str = os.getenv("AIRFLOW_PASSWORD", "admin")

    # Streamlit
    STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    STREAMLIT_SERVER_HEADLESS: bool = os.getenv("STREAMLIT_SERVER_HEADLESS", "True").lower() == "true"

    # FastAPI
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")


settings = Settings()
>>>>>>> origin/claude/build-nexus-pipeline-module-01QTVSb9CH4TjcrrT8nhjeJp
=======
"""
Configuration settings for the NEXUS platform.
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    anthropic_api_key: str = ""

    # Application Settings
    app_name: str = "NEXUS"
    app_version: str = "1.0.0"
    debug_mode: bool = False

    # Paths
    base_dir: Path = Path(__file__).parent.parent
    documents_path: Path = base_dir / "documents"
    temp_path: Path = base_dir / "temp"
    templates_path: Path = base_dir / "assets" / "templates"

    # Streamlit Configuration
    streamlit_server_port: int = 8501
    streamlit_server_headless: bool = True
    streamlit_browser_gather_usage_stats: bool = False

    # Document Settings
    enable_collaboration: bool = True
    max_document_size_mb: int = 50

    # Language Tool Settings
    language_tool_enabled: bool = True
    language_tool_language: str = "en-US"

    # Export Settings
    export_pdf_margin: int = 20
    export_pdf_page_size: str = "A4"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        self.documents_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
        self.templates_path.mkdir(parents=True, exist_ok=True)
=======
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
>>>>>>> origin/claude/marketing-automation-module-01QZjZLNDEejmtRGTMvcovNS
=======
"""
Application settings and configuration management.

This module handles all configuration settings for the NEXUS platform,
including database, Redis, Celery, API keys, and environment-specific settings.
"""

import os
from typing import Optional
=======
"""
NEXUS Platform Settings

Centralized configuration management using Pydantic Settings.
All settings are loaded from environment variables with sensible defaults.
"""

from typing import List, Optional
>>>>>>> origin/claude/nexus-translation-module-011pENKCpeToEVPri4dLYT7D
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
<<<<<<< HEAD
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
>>>>>>> origin/claude/build-advertising-lead-generation-01Skr8pwxfdGAtz4wHoobrUL
=======
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
>>>>>>> origin/claude/nexus-translation-module-011pENKCpeToEVPri4dLYT7D


# Global settings instance
settings = Settings()
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> origin/claude/word-editor-module-01PPyUEeNUgZmU4swtfxgoCB
=======

class Settings:
    """Application settings."""

    # Database
    DATABASE_URL: str = os.getenv(
        'DATABASE_URL',
        'postgresql://nexus_user:nexus_pass@localhost:5432/nexus'
    )

    # AI/LLM
    ANTHROPIC_API_KEY: str = os.getenv('ANTHROPIC_API_KEY', '')
    DEFAULT_MODEL: str = 'claude-sonnet-4-5-20250929'

    # Authentication
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', 'change-this-secret-key-in-production')
    JWT_ALGORITHM: str = 'HS256'
    JWT_EXPIRATION_DAYS: int = 7

    # Storage
    STORAGE_TYPE: str = os.getenv('STORAGE_TYPE', 'local')  # 'local' or 's3'
    STORAGE_PATH: str = os.getenv('STORAGE_PATH', './storage')
    S3_BUCKET_NAME: Optional[str] = os.getenv('S3_BUCKET_NAME')
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv('AWS_SECRET_ACCESS_KEY')

    # Application
    APP_NAME: str = 'NEXUS Platform'
    APP_VERSION: str = '1.0.0'
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')

    # Streamlit
    PAGE_TITLE: str = '🚀 NEXUS Platform'
    PAGE_ICON: str = '🚀'
    LAYOUT: str = 'wide'


settings = Settings()
>>>>>>> origin/claude/excel-spreadsheet-editor-01ERQuTgtV3Kb8CMNgURhB2E
=======
>>>>>>> origin/claude/marketing-automation-module-01QZjZLNDEejmtRGTMvcovNS
=======
>>>>>>> origin/claude/build-advertising-lead-generation-01Skr8pwxfdGAtz4wHoobrUL
=======
>>>>>>> origin/claude/nexus-translation-module-011pENKCpeToEVPri4dLYT7D
