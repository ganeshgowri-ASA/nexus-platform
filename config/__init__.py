<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
"""Configuration package for Nexus Platform"""
from config.settings import settings
from config.celery_config import celery_app

__all__ = ['settings', 'celery_app']
=======
"""
Configuration module
"""
>>>>>>> origin/claude/multi-channel-notifications-01WeNhyLeSWZWAjx7hyDqB6q
=======
from .settings import settings

__all__ = ['settings']
>>>>>>> origin/claude/productivity-suite-ai-01Uq8q3V9EdvDAuMPqDoBxZh
=======
"""Configuration module for NEXUS platform."""
=======
"""
NEXUS Platform Configuration Package

This package contains all configuration modules for the NEXUS platform.
"""
>>>>>>> origin/claude/nexus-translation-module-011pENKCpeToEVPri4dLYT7D

from .settings import settings

__all__ = ["settings"]
<<<<<<< HEAD
>>>>>>> origin/claude/build-nexus-pipeline-module-01QTVSb9CH4TjcrrT8nhjeJp
=======
"""Configuration module for NEXUS platform."""
>>>>>>> origin/claude/excel-spreadsheet-editor-01ERQuTgtV3Kb8CMNgURhB2E
=======
"""Configuration package."""

from .config import settings

__all__ = ["settings"]
>>>>>>> origin/claude/contracts-management-module-01FmzTmE3DeZrdwEsMYTdLB9
=======
"""Configuration module for NEXUS platform."""

from .settings import settings
from .database import get_db, init_db
from .redis_config import redis_client
from .celery_config import celery_app
from .logging_config import setup_logging, get_logger

__all__ = [
    "settings",
    "get_db",
    "init_db",
    "redis_client",
    "celery_app",
    "setup_logging",
    "get_logger",
]
>>>>>>> origin/claude/build-advertising-lead-generation-01Skr8pwxfdGAtz4wHoobrUL
=======
>>>>>>> origin/claude/nexus-translation-module-011pENKCpeToEVPri4dLYT7D
