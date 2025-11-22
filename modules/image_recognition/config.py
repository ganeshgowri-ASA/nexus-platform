"""
Configuration for Image Recognition Module

Centralized configuration management for the image recognition module.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseSettings, Field, validator


class ImageRecognitionConfig(BaseSettings):
    """Configuration for image recognition module."""

    # Module Information
    MODULE_NAME: str = "image_recognition"
    MODULE_VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost:5432/nexus",
        env="DATABASE_URL"
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    REDIS_CACHE_TTL: int = Field(default=3600, env="REDIS_CACHE_TTL")  # 1 hour

    # Celery
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        env="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0",
        env="CELERY_RESULT_BACKEND"
    )
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 3600  # 1 hour max

    # API Keys
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")

    # Storage
    STORAGE_TYPE: str = Field(default="local", env="STORAGE_TYPE")  # local, s3, azure
    STORAGE_PATH: str = Field(
        default="/tmp/nexus/image_recognition",
        env="STORAGE_PATH"
    )
    S3_BUCKET: Optional[str] = Field(default=None, env="S3_BUCKET")
    S3_REGION: Optional[str] = Field(default="us-east-1", env="S3_REGION")
    AZURE_CONTAINER: Optional[str] = Field(default=None, env="AZURE_CONTAINER")
    MAX_UPLOAD_SIZE_MB: int = Field(default=100, env="MAX_UPLOAD_SIZE_MB")

    # Model Configuration
    DEFAULT_CLASSIFICATION_MODEL: str = "resnet50"
    DEFAULT_DETECTION_MODEL: str = "yolo"
    DEFAULT_SEGMENTATION_MODEL: str = "deeplab"
    MODEL_CACHE_DIR: str = Field(
        default="/tmp/nexus/models",
        env="MODEL_CACHE_DIR"
    )
    USE_GPU: bool = Field(default=True, env="USE_GPU")
    GPU_MEMORY_FRACTION: float = 0.8

    # Processing Configuration
    DEFAULT_BATCH_SIZE: int = 32
    MAX_BATCH_SIZE: int = 256
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.5
    DEFAULT_IOU_THRESHOLD: float = 0.45
    DEFAULT_TOP_K: int = 5
    MAX_IMAGE_DIMENSION: int = 4096
    MIN_IMAGE_DIMENSION: int = 32

    # Feature Extraction
    FEATURE_VECTOR_DIMENSIONS: int = 2048
    SIMILARITY_THRESHOLD: float = 0.7
    MAX_SIMILARITY_RESULTS: int = 100

    # Quality Assessment
    BLUR_THRESHOLD: float = 100.0
    NOISE_THRESHOLD: float = 20.0
    MIN_BRIGHTNESS: float = 50.0
    MAX_BRIGHTNESS: float = 200.0
    MIN_CONTRAST: float = 30.0

    # Training Configuration
    DEFAULT_EPOCHS: int = 10
    DEFAULT_LEARNING_RATE: float = 0.001
    DEFAULT_VALIDATION_SPLIT: float = 0.2
    EARLY_STOPPING_PATIENCE: int = 5
    REDUCE_LR_PATIENCE: int = 3

    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_WORKERS: int = Field(default=4, env="API_WORKERS")
    API_RELOAD: bool = Field(default=False, env="API_RELOAD")
    CORS_ORIGINS: list = ["*"]
    RATE_LIMIT_PER_MINUTE: int = 60

    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    WS_MAX_CONNECTIONS: int = 1000

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")

    # Security
    JWT_SECRET_KEY: str = Field(
        default="change-this-secret-key-in-production",
        env="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    ENABLE_RATE_LIMITING: bool = True
    ENABLE_AUTHENTICATION: bool = True

    # Performance
    ENABLE_CACHING: bool = True
    ENABLE_COMPRESSION: bool = True
    ENABLE_ASYNC_PROCESSING: bool = True
    MAX_WORKERS: int = Field(default=4, env="MAX_WORKERS")

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    ENABLE_SENTRY: bool = False
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")

    # Export Configuration
    EXPORT_FORMATS: list = ["json", "csv", "excel", "coco", "yolo", "voc"]
    EXPORT_PATH: str = Field(
        default="/tmp/nexus/exports",
        env="EXPORT_PATH"
    )
    EXPORT_RETENTION_DAYS: int = 7

    # Annotation Configuration
    ANNOTATION_TYPES: list = ["bbox", "polygon", "mask", "point"]
    MIN_BBOX_SIZE: int = 10
    MAX_POLYGON_POINTS: int = 1000

    # Job Configuration
    JOB_CLEANUP_DAYS: int = 30
    MAX_CONCURRENT_JOBS: int = 10
    JOB_TIMEOUT_HOURS: int = 24

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @validator("STORAGE_PATH", "MODEL_CACHE_DIR", "EXPORT_PATH")
    def create_directories(cls, v):
        """Create directories if they don't exist."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_model_config(self, model_type: str) -> Dict[str, Any]:
        """Get configuration for specific model type."""
        configs = {
            "vgg16": {
                "input_shape": (224, 224),
                "preprocessing": "vgg",
                "batch_size": 32
            },
            "resnet50": {
                "input_shape": (224, 224),
                "preprocessing": "resnet",
                "batch_size": 32
            },
            "inceptionv3": {
                "input_shape": (299, 299),
                "preprocessing": "inception",
                "batch_size": 32
            },
            "efficientnet": {
                "input_shape": (224, 224),
                "preprocessing": "efficientnet",
                "batch_size": 32
            },
            "yolo": {
                "input_shape": (640, 640),
                "model_size": "s",  # n, s, m, l, x
                "batch_size": 16
            }
        }
        return configs.get(model_type.lower(), {})

    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration."""
        if self.STORAGE_TYPE == "s3":
            return {
                "type": "s3",
                "bucket": self.S3_BUCKET,
                "region": self.S3_REGION
            }
        elif self.STORAGE_TYPE == "azure":
            return {
                "type": "azure",
                "container": self.AZURE_CONTAINER
            }
        else:
            return {
                "type": "local",
                "path": self.STORAGE_PATH
            }

    def get_celery_config(self) -> Dict[str, Any]:
        """Get Celery configuration."""
        return {
            "broker_url": self.CELERY_BROKER_URL,
            "result_backend": self.CELERY_RESULT_BACKEND,
            "task_track_started": self.CELERY_TASK_TRACK_STARTED,
            "task_time_limit": self.CELERY_TASK_TIME_LIMIT,
            "task_serializer": "json",
            "result_serializer": "json",
            "accept_content": ["json"],
            "timezone": "UTC",
            "enable_utc": True
        }

    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        return {
            "host": self.API_HOST,
            "port": self.API_PORT,
            "workers": self.API_WORKERS,
            "reload": self.API_RELOAD,
            "cors_origins": self.CORS_ORIGINS,
            "rate_limit": self.RATE_LIMIT_PER_MINUTE
        }


# Global configuration instance
_config: Optional[ImageRecognitionConfig] = None


def get_config() -> ImageRecognitionConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = ImageRecognitionConfig()
    return _config


def update_config(**kwargs) -> ImageRecognitionConfig:
    """Update configuration with new values."""
    global _config
    _config = ImageRecognitionConfig(**kwargs)
    return _config


# Convenience functions
def get_database_url() -> str:
    """Get database URL."""
    return get_config().DATABASE_URL


def get_redis_url() -> str:
    """Get Redis URL."""
    return get_config().REDIS_URL


def get_storage_path() -> str:
    """Get storage path."""
    return get_config().STORAGE_PATH


def get_model_cache_dir() -> str:
    """Get model cache directory."""
    return get_config().MODEL_CACHE_DIR


def is_gpu_enabled() -> bool:
    """Check if GPU is enabled."""
    return get_config().USE_GPU


def get_default_model(task: str = "classification") -> str:
    """Get default model for task."""
    config = get_config()
    if task == "classification":
        return config.DEFAULT_CLASSIFICATION_MODEL
    elif task == "detection":
        return config.DEFAULT_DETECTION_MODEL
    elif task == "segmentation":
        return config.DEFAULT_SEGMENTATION_MODEL
    else:
        return config.DEFAULT_CLASSIFICATION_MODEL
