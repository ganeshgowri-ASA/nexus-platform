from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """API Gateway configuration settings"""

    # Application
    APP_NAME: str = "NEXUS API Gateway"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # Database
    DATABASE_URL: str = "postgresql://nexus:nexus@localhost:5432/nexus_gateway"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # JWT Authentication
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Rate Limiting
    DEFAULT_RATE_LIMIT: int = 100  # requests per minute
    DEFAULT_RATE_LIMIT_WINDOW: int = 60  # seconds

    # Caching
    DEFAULT_CACHE_TTL: int = 300  # seconds
    CACHE_ENABLED: bool = True

    # Timeouts
    DEFAULT_TIMEOUT: float = 30.0  # seconds
    BACKEND_CONNECT_TIMEOUT: float = 5.0
    BACKEND_READ_TIMEOUT: float = 30.0

    # Load Balancing
    LOAD_BALANCE_STRATEGY: str = "round_robin"  # round_robin, least_connections, ip_hash

    # Monitoring
    METRICS_ENABLED: bool = True
    METRICS_RETENTION_DAYS: int = 30

    # CORS
    CORS_ORIGINS: list = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]

    # Admin UI
    ADMIN_UI_ENABLED: bool = True
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"  # Change in production!

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
