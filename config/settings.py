"""
NEXUS Platform Configuration Settings

Centralized configuration using Pydantic Settings with environment variable support.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings and configuration."""

    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    UPLOADS_DIR = DATA_DIR / "uploads"
    EXPORTS_DIR = DATA_DIR / "exports"
    TEMP_DIR = DATA_DIR / "temp"
    LOGS_DIR = BASE_DIR / "logs"

    # Application Configuration
    APP_NAME = "NEXUS Platform"
    APP_VERSION = "1.0.0"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "nexus-secret-key-change-in-production")

    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/nexus.db")

    # AI Configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    AI_MODEL_GPT = os.getenv("AI_MODEL_GPT", "gpt-4-turbo-preview")

    # Email Configuration
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM = os.getenv("SMTP_FROM", "noreply@nexus-platform.com")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

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

    # Application Features
    ENABLE_AI_FEATURES = os.getenv("ENABLE_AI_FEATURES", "true").lower() == "true"
    ENABLE_EXPORT = os.getenv("ENABLE_EXPORT", "true").lower() == "true"
    ENABLE_FILE_SHARING = os.getenv("ENABLE_FILE_SHARING", "true").lower() == "true"

    # Redis Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_URL = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

    # Celery Configuration
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

    def __init__(self):
        """Create necessary directories on initialization."""
        self.DATA_DIR.mkdir(exist_ok=True)
        self.UPLOADS_DIR.mkdir(exist_ok=True)
        self.EXPORTS_DIR.mkdir(exist_ok=True)
        self.TEMP_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)


# Create singleton instance
settings = Settings()
