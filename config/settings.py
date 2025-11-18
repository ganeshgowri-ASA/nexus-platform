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
