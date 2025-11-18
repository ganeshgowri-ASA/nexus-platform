"""Configuration settings for NEXUS platform."""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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
