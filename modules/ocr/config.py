"""
OCR Module Configuration

Centralized configuration for the OCR module with environment variable support.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class OCRConfig(BaseSettings):
    """OCR Module Configuration Settings"""

    # Database Configuration
    database_url: str = Field(
        default="postgresql://nexus:nexus@localhost:5432/nexus_ocr",
        env="OCR_DATABASE_URL"
    )

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="OCR_REDIS_URL"
    )

    # Celery Configuration
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        env="OCR_CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        env="OCR_CELERY_RESULT_BACKEND"
    )

    # File Storage
    storage_path: Path = Field(
        default=Path("/tmp/nexus_ocr_storage"),
        env="OCR_STORAGE_PATH"
    )
    upload_path: Path = Field(
        default=Path("/tmp/nexus_ocr_uploads"),
        env="OCR_UPLOAD_PATH"
    )
    max_file_size: int = Field(
        default=50 * 1024 * 1024,  # 50MB
        env="OCR_MAX_FILE_SIZE"
    )

    # Tesseract Configuration
    tesseract_path: Optional[str] = Field(
        default="/usr/bin/tesseract",
        env="TESSERACT_PATH"
    )
    tesseract_data_path: Optional[str] = Field(
        default="/usr/share/tesseract-ocr/4.00/tessdata",
        env="TESSDATA_PREFIX"
    )

    # Google Cloud Vision API
    google_cloud_credentials: Optional[str] = Field(
        default=None,
        env="GOOGLE_APPLICATION_CREDENTIALS"
    )
    google_cloud_project: Optional[str] = Field(
        default=None,
        env="GOOGLE_CLOUD_PROJECT"
    )

    # Azure Computer Vision
    azure_cv_endpoint: Optional[str] = Field(
        default=None,
        env="AZURE_CV_ENDPOINT"
    )
    azure_cv_key: Optional[str] = Field(
        default=None,
        env="AZURE_CV_KEY"
    )

    # AWS Textract
    aws_access_key_id: Optional[str] = Field(
        default=None,
        env="AWS_ACCESS_KEY_ID"
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None,
        env="AWS_SECRET_ACCESS_KEY"
    )
    aws_region: str = Field(
        default="us-east-1",
        env="AWS_REGION"
    )

    # OpenAI GPT-4 Vision
    openai_api_key: Optional[str] = Field(
        default=None,
        env="OPENAI_API_KEY"
    )
    openai_model: str = Field(
        default="gpt-4-vision-preview",
        env="OPENAI_MODEL"
    )

    # Anthropic Claude Vision
    anthropic_api_key: Optional[str] = Field(
        default=None,
        env="ANTHROPIC_API_KEY"
    )
    anthropic_model: str = Field(
        default="claude-3-opus-20240229",
        env="ANTHROPIC_MODEL"
    )

    # OCR Processing Settings
    default_language: str = Field(
        default="eng",
        env="OCR_DEFAULT_LANGUAGE"
    )
    supported_languages: str = Field(
        default="eng,fra,deu,spa,ita,por,rus,ara,chi_sim,jpn,kor",
        env="OCR_SUPPORTED_LANGUAGES"
    )
    default_dpi: int = Field(
        default=300,
        env="OCR_DEFAULT_DPI"
    )
    confidence_threshold: float = Field(
        default=0.7,
        env="OCR_CONFIDENCE_THRESHOLD"
    )

    # Batch Processing
    batch_size: int = Field(
        default=10,
        env="OCR_BATCH_SIZE"
    )
    max_workers: int = Field(
        default=4,
        env="OCR_MAX_WORKERS"
    )

    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        env="OCR_API_HOST"
    )
    api_port: int = Field(
        default=8000,
        env="OCR_API_PORT"
    )
    api_workers: int = Field(
        default=4,
        env="OCR_API_WORKERS"
    )

    # Security
    secret_key: str = Field(
        default="nexus-ocr-secret-key-change-in-production",
        env="OCR_SECRET_KEY"
    )
    algorithm: str = Field(
        default="HS256",
        env="OCR_ALGORITHM"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        env="OCR_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        env="OCR_LOG_LEVEL"
    )
    log_file: Optional[Path] = Field(
        default=None,
        env="OCR_LOG_FILE"
    )

    # Performance
    enable_gpu: bool = Field(
        default=False,
        env="OCR_ENABLE_GPU"
    )
    cache_ttl: int = Field(
        default=3600,  # 1 hour
        env="OCR_CACHE_TTL"
    )

    # WebSocket
    websocket_url: str = Field(
        default="ws://localhost:8000/ws",
        env="OCR_WEBSOCKET_URL"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.upload_path.mkdir(parents=True, exist_ok=True)

    @property
    def supported_languages_list(self) -> list[str]:
        """Get list of supported languages"""
        return [lang.strip() for lang in self.supported_languages.split(",")]

    def get_engine_config(self, engine: str) -> Dict[str, Any]:
        """Get configuration for specific OCR engine"""
        configs = {
            "tesseract": {
                "path": self.tesseract_path,
                "data_path": self.tesseract_data_path,
            },
            "google_vision": {
                "credentials": self.google_cloud_credentials,
                "project": self.google_cloud_project,
            },
            "azure": {
                "endpoint": self.azure_cv_endpoint,
                "key": self.azure_cv_key,
            },
            "aws": {
                "access_key_id": self.aws_access_key_id,
                "secret_access_key": self.aws_secret_access_key,
                "region": self.aws_region,
            },
            "openai": {
                "api_key": self.openai_api_key,
                "model": self.openai_model,
            },
            "anthropic": {
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model,
            },
        }
        return configs.get(engine, {})


# Global configuration instance
config = OCRConfig()
