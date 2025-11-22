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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
