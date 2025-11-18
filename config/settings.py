"""
Configuration settings for the NEXUS platform.
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    anthropic_api_key: str = ""

    # Application Settings
    app_name: str = "NEXUS"
    app_version: str = "1.0.0"
    debug_mode: bool = False

    # Paths
    base_dir: Path = Path(__file__).parent.parent
    documents_path: Path = base_dir / "documents"
    temp_path: Path = base_dir / "temp"
    templates_path: Path = base_dir / "assets" / "templates"

    # Streamlit Configuration
    streamlit_server_port: int = 8501
    streamlit_server_headless: bool = True
    streamlit_browser_gather_usage_stats: bool = False

    # Document Settings
    enable_collaboration: bool = True
    max_document_size_mb: int = 50

    # Language Tool Settings
    language_tool_enabled: bool = True
    language_tool_language: str = "en-US"

    # Export Settings
    export_pdf_margin: int = 20
    export_pdf_page_size: str = "A4"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        self.documents_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
        self.templates_path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
