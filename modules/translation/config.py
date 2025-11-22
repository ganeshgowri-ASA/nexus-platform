"""
Configuration for the translation module
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class TranslationConfig(BaseSettings):
    """Translation module configuration"""

    # Database
    database_url: str = os.getenv(
        "TRANSLATION_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/nexus_translation"
    )

    # Translation APIs
    google_api_key: Optional[str] = os.getenv("GOOGLE_TRANSLATE_API_KEY")
    google_project_id: Optional[str] = os.getenv("GOOGLE_PROJECT_ID")
    deepl_api_key: Optional[str] = os.getenv("DEEPL_API_KEY")

    # Default provider
    default_provider: str = os.getenv("DEFAULT_TRANSLATION_PROVIDER", "google")

    # Celery
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # API Settings
    api_host: str = os.getenv("TRANSLATION_API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("TRANSLATION_API_PORT", "8000"))
    api_reload: bool = os.getenv("TRANSLATION_API_RELOAD", "true").lower() == "true"

    # Streamlit UI
    ui_port: int = int(os.getenv("TRANSLATION_UI_PORT", "8501"))

    # File upload settings
    upload_dir: str = os.getenv("TRANSLATION_UPLOAD_DIR", "./uploads")
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

    # Cache settings
    enable_cache: bool = os.getenv("ENABLE_TRANSLATION_CACHE", "true").lower() == "true"
    cache_ttl: int = int(os.getenv("TRANSLATION_CACHE_TTL", "3600"))

    # Quality scoring
    enable_quality_scoring: bool = os.getenv("ENABLE_QUALITY_SCORING", "true").lower() == "true"

    # Rate limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global config instance
config = TranslationConfig()
