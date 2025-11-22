"""
Frontend configuration for NEXUS Platform.

This module manages frontend settings and environment variables.
"""

import os
from typing import Optional


class FrontendConfig:
    """Frontend configuration settings."""

    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    API_V1_PREFIX: str = "/api/v1"

    # App Configuration
    APP_TITLE: str = "NEXUS Platform"
    APP_ICON: str = "🔷"
    LAYOUT: str = "wide"

    # Theme
    PRIMARY_COLOR: str = "#0066CC"
    BACKGROUND_COLOR: str = "#FFFFFF"
    SECONDARY_BACKGROUND_COLOR: str = "#F0F2F6"

    # Session
    SESSION_TIMEOUT_MINUTES: int = 60

    # File Upload
    MAX_FILE_SIZE_MB: int = 10

    @property
    def api_url(self) -> str:
        """Get full API URL."""
        return f"{self.API_BASE_URL}{self.API_V1_PREFIX}"


config = FrontendConfig()
