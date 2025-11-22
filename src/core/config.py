"""Configuration management for NEXUS Platform."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application settings
    app_env: str = "development"
    app_debug: bool = True
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "sqlite:///./nexus.db"

    # Email SMTP settings
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_smtp_username: Optional[str] = None
    email_smtp_password: Optional[str] = None
    email_smtp_use_tls: bool = True

    # Email IMAP settings
    email_imap_host: str = "imap.gmail.com"
    email_imap_port: int = 993
    email_imap_username: Optional[str] = None
    email_imap_password: Optional[str] = None
    email_imap_use_ssl: bool = True

    # Email settings
    email_default_sender: Optional[str] = None
    email_max_attachment_size_mb: int = 25
    email_sync_interval_minutes: int = 5
    email_batch_size: int = 50

    # Spam filter
    spam_filter_threshold: float = 0.7
    spam_keywords: str = "spam,lottery,winner,congratulations,click here"

    # Tracking
    email_tracking_enabled: bool = True

    @property
    def spam_keywords_list(self) -> list[str]:
        """Get spam keywords as a list."""
        return [kw.strip() for kw in self.spam_keywords.split(",")]


# Global settings instance
settings = Settings()
