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


<<<<<<< HEAD
class WikiConfig(BaseModel):
    """Wiki system configuration settings"""
    enabled: bool = Field(default=True, description="Enable wiki module")

    # Storage settings
    storage_path: str = Field(default="data/wiki/attachments", description="Path for wiki attachments")
    max_attachment_size: int = Field(default=104857600, description="Max attachment size in bytes (100MB)")
    max_image_size: int = Field(default=10485760, description="Max image size in bytes (10MB)")
    allowed_file_types: List[str] = Field(
        default=["jpg", "jpeg", "png", "gif", "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "md", "zip"],
        description="Allowed file types for attachments"
    )

    # Content settings
    default_content_format: str = Field(default="markdown", description="Default content format")
    enable_wysiwyg_editor: bool = Field(default=True, description="Enable WYSIWYG editor")
    enable_markdown_editor: bool = Field(default=True, description="Enable markdown editor")
    max_page_size: int = Field(default=1048576, description="Max page content size in bytes (1MB)")

    # Versioning settings
    enable_versioning: bool = Field(default=True, description="Enable version control")
    max_versions_per_page: int = Field(default=100, description="Maximum versions to keep per page")
    version_retention_days: int = Field(default=365, description="Days to retain old versions")

    # Search settings
    enable_full_text_search: bool = Field(default=True, description="Enable full-text search")
    enable_semantic_search: bool = Field(default=True, description="Enable AI-powered semantic search")
    search_results_per_page: int = Field(default=20, description="Search results per page")

    # Collaboration settings
    enable_comments: bool = Field(default=True, description="Enable comments and discussions")
    enable_real_time_editing: bool = Field(default=True, description="Enable real-time collaborative editing")
    enable_notifications: bool = Field(default=True, description="Enable notifications")
    websocket_ping_interval: int = Field(default=30, description="WebSocket ping interval in seconds")

    # AI features
    enable_ai_assistant: bool = Field(default=True, description="Enable AI assistant features")
    enable_auto_linking: bool = Field(default=True, description="Enable automatic link suggestions")
    enable_auto_tagging: bool = Field(default=True, description="Enable automatic tag suggestions")
    enable_content_summarization: bool = Field(default=True, description="Enable content summarization")

    # Permissions
    default_page_permissions: str = Field(default="read", description="Default permissions for new pages")
    enable_granular_permissions: bool = Field(default=True, description="Enable page-level permissions")
    enable_namespace_permissions: bool = Field(default=True, description="Enable namespace-level permissions")

    # Analytics
    enable_analytics: bool = Field(default=True, description="Enable analytics tracking")
    track_page_views: bool = Field(default=True, description="Track page views")
    analytics_retention_days: int = Field(default=90, description="Days to retain analytics data")

    # Export/Import
    enable_export: bool = Field(default=True, description="Enable page export")
    enable_import: bool = Field(default=True, description="Enable page import")
    export_formats: List[str] = Field(default=["pdf", "html", "markdown", "docx"], description="Supported export formats")
    import_sources: List[str] = Field(default=["confluence", "mediawiki", "notion", "markdown"], description="Supported import sources")

    # Integrations
    enable_slack_integration: bool = Field(default=False, description="Enable Slack integration")
    enable_teams_integration: bool = Field(default=False, description="Enable Microsoft Teams integration")
    enable_github_integration: bool = Field(default=False, description="Enable GitHub integration")
    enable_jira_integration: bool = Field(default=False, description="Enable JIRA integration")

    # Cache settings
    enable_caching: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=60, description="API requests per minute per user")


=======
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW
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
<<<<<<< HEAD
    wiki: WikiConfig = Field(default_factory=WikiConfig)
=======
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW

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
