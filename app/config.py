"""
NEXUS Platform Configuration
Centralized settings management using Pydantic
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import os
from pathlib import Path


class DatabaseConfig(BaseModel):
    """Database configuration settings"""
    url: str = Field(default="sqlite:///nexus.db", description="Database connection URL")
    echo: bool = Field(default=False, description="Echo SQL queries")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max overflow connections")


class AnthropicConfig(BaseModel):
    """Anthropic Claude API configuration"""
    api_key: str = Field(default="", description="Anthropic API key")
    model: str = Field(default="claude-3-5-sonnet-20241022", description="Claude model to use")
    max_tokens: int = Field(default=4096, description="Maximum tokens per request")
    temperature: float = Field(default=0.7, description="Model temperature")

    @validator("api_key")
    def validate_api_key(cls, v: str) -> str:
        """Validate API key is not empty in production"""
        if not v and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("Anthropic API key is required in production")
        return v


class UIConfig(BaseModel):
    """UI/UX configuration settings"""
    theme: str = Field(default="dark", description="UI theme (dark/light)")
    primary_color: str = Field(default="#6366f1", description="Primary brand color")
    secondary_color: str = Field(default="#8b5cf6", description="Secondary brand color")
    sidebar_state: str = Field(default="expanded", description="Sidebar initial state")
    layout: str = Field(default="wide", description="Page layout")


class LoggingConfig(BaseModel):
    """Logging configuration settings"""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    file_path: Optional[str] = Field(default="logs/nexus.log", description="Log file path")
    max_bytes: int = Field(default=10485760, description="Max log file size (10MB)")
    backup_count: int = Field(default=5, description="Number of backup log files")


class SecurityConfig(BaseModel):
    """Security configuration settings"""
    secret_key: str = Field(default="change-me-in-production", description="Secret key for encryption")
    allowed_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    session_timeout: int = Field(default=3600, description="Session timeout in seconds")


class Settings(BaseSettings):
    """
    Main application settings
    Loads from environment variables and .env file
    """

    # Application settings
    app_name: str = Field(default="NEXUS Platform", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development/staging/production)")
    debug: bool = Field(default=True, description="Debug mode")

    # Base paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")

    # Component configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    anthropic: AnthropicConfig = Field(default_factory=AnthropicConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # Feature flags
    enable_analytics: bool = Field(default=True, description="Enable analytics module")
    enable_ai_features: bool = Field(default=True, description="Enable AI-powered features")
    enable_collaboration: bool = Field(default=True, description="Enable collaboration features")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False
        extra = "allow"

    @validator("data_dir", "base_dir")
    def create_directories(cls, v: Path) -> Path:
        """Ensure directories exist"""
        v.mkdir(parents=True, exist_ok=True)
        return v

    def get_database_url(self) -> str:
        """Get formatted database URL"""
        return self.database.url

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"

    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()
