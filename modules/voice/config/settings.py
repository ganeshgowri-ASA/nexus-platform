"""Application settings and configuration."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "NEXUS Voice Assistant"
    app_version: str = "1.0.0"
    debug: bool = False

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/nexus_voice"

    # Speech-to-Text
    stt_provider: str = "google"  # 'google' or 'aws'
    google_credentials_path: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    aws_s3_bucket: Optional[str] = None

    # Text-to-Speech
    tts_provider: str = "google"  # 'google' or 'aws'
    default_tts_voice: str = "en-US-Neural2-A"
    default_language: str = "en-US"

    # NLP/LLM
    llm_provider: str = "anthropic"  # 'anthropic' or 'openai'
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Audio Processing
    temp_audio_dir: str = "/tmp/nexus_voice"
    max_audio_duration_seconds: int = 300  # 5 minutes
    audio_sample_rate: int = 16000

    # Session
    max_session_history: int = 10
    session_timeout_minutes: int = 30

    # Security
    api_key_header: str = "X-API-Key"
    allowed_origins: list = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
