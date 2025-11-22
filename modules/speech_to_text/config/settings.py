"""Configuration settings for speech-to-text module."""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_name: str = "NEXUS Speech-to-Text"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/nexus_speech"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis (for Celery)
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # File Storage
    upload_dir: str = "./uploads/audio"
    max_upload_size: int = 500 * 1024 * 1024  # 500MB
    allowed_audio_formats: list = [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma"]

    # Whisper Settings
    whisper_model: str = "base"  # tiny, base, small, medium, large
    whisper_device: str = "cpu"  # cpu or cuda
    whisper_compute_type: str = "int8"  # int8, float16, float32

    # Google Cloud Speech-to-Text
    google_credentials_path: Optional[str] = None
    google_project_id: Optional[str] = None

    # AWS Transcribe
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    aws_s3_bucket: Optional[str] = None

    # Transcription Settings
    default_language: str = "en"
    enable_auto_detect_language: bool = True
    default_provider: str = "whisper"  # whisper, google, aws

    # Speaker Diarization
    enable_diarization: bool = True
    max_speakers: int = 10
    min_speakers: int = 1

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: list = ["*"]

    # Streamlit UI
    streamlit_port: int = 8501

    # Processing
    chunk_length_seconds: int = 30  # For streaming
    enable_word_timestamps: bool = True
    confidence_threshold: float = 0.5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
