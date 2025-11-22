"""
Configuration settings for Image Recognition module
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Settings
    API_V1_PREFIX: str = "/api/v1/image-recognition"
    PROJECT_NAME: str = "NEXUS Image Recognition"

    # Database
    DATABASE_URL: str = "postgresql://nexus_user:nexus_pass@localhost:5432/nexus_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Computer Vision APIs
    GOOGLE_VISION_API_KEY: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    # AI/LLM
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # File Storage
    UPLOAD_DIR: str = "./uploads/images"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

    # Model Settings
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.5
    MAX_OBJECTS_PER_IMAGE: int = 100

    # Performance
    MAX_WORKERS: int = 4
    TASK_TIMEOUT_SECONDS: int = 300

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
