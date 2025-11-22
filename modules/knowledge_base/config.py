"""
Configuration for Knowledge Base System

Centralized configuration with environment variable support.
"""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "NEXUS Knowledge Base"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/nexus_kb"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 3600  # seconds

    # Elasticsearch
    ELASTICSEARCH_HOST: str = "localhost:9200"
    ELASTICSEARCH_INDEX: str = "kb_content"
    ELASTICSEARCH_ENABLED: bool = True

    # Vector Database (Pinecone/Weaviate)
    VECTOR_DB_TYPE: str = "pinecone"  # or "weaviate"
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    PINECONE_INDEX: str = "kb-embeddings"

    # LLM / AI
    LLM_PROVIDER: str = "anthropic"  # or "openai"
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Translation
    TRANSLATION_SERVICE: str = "google"  # or "deepl"
    GOOGLE_TRANSLATE_API_KEY: Optional[str] = None
    DEEPL_API_KEY: Optional[str] = None

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Storage
    UPLOAD_FOLDER: str = "/tmp/kb_uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {"pdf", "docx", "jpg", "png", "mp4"}

    # Security
    SECRET_KEY: str = "change-this-in-production"
    API_KEY_HEADER: str = "X-API-Key"
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8501"]

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Search
    SEARCH_MIN_SCORE: float = 0.5
    SEMANTIC_SEARCH_ENABLED: bool = True

    # Features
    CHATBOT_ENABLED: bool = True
    AUTO_TRANSLATION_ENABLED: bool = True
    VIDEO_TRANSCRIPTION_ENABLED: bool = True
    AUTO_FAQ_GENERATION_ENABLED: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
