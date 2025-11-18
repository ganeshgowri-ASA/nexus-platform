"""
Social Media Module - Configuration.

Centralized configuration management for the social media module.
"""

import os
from typing import Optional
from pydantic import BaseSettings


class SocialMediaConfig(BaseSettings):
    """Social media module configuration."""

    # Database
    DATABASE_URL: str = os.getenv(
        "SOCIAL_MEDIA_DB_URL",
        "postgresql://user:pass@localhost/nexus_social"
    )

    # Redis
    REDIS_URL: str = os.getenv("SOCIAL_MEDIA_REDIS_URL", "redis://localhost:6379/0")

    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # Platform API Keys (store in environment variables)
    FACEBOOK_APP_ID: Optional[str] = os.getenv("FACEBOOK_APP_ID")
    FACEBOOK_APP_SECRET: Optional[str] = os.getenv("FACEBOOK_APP_SECRET")
    TWITTER_API_KEY: Optional[str] = os.getenv("TWITTER_API_KEY")
    TWITTER_API_SECRET: Optional[str] = os.getenv("TWITTER_API_SECRET")
    INSTAGRAM_APP_ID: Optional[str] = os.getenv("INSTAGRAM_APP_ID")
    INSTAGRAM_APP_SECRET: Optional[str] = os.getenv("INSTAGRAM_APP_SECRET")
    LINKEDIN_CLIENT_ID: Optional[str] = os.getenv("LINKEDIN_CLIENT_ID")
    LINKEDIN_CLIENT_SECRET: Optional[str] = os.getenv("LINKEDIN_CLIENT_SECRET")

    # AI/LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "anthropic")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    # Link Management
    SHORT_LINK_DOMAIN: str = os.getenv("SHORT_LINK_DOMAIN", "short.link")

    # Media Storage
    MEDIA_STORAGE_PATH: str = os.getenv("MEDIA_STORAGE_PATH", "/var/media/social")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    # Monitoring
    ENABLE_MONITORING: bool = os.getenv("ENABLE_MONITORING", "true").lower() == "true"
    MONITORING_INTERVAL_MINUTES: int = int(os.getenv("MONITORING_INTERVAL_MINUTES", "15"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        case_sensitive = True


config = SocialMediaConfig()
