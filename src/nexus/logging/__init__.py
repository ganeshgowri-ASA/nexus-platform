"""Centralized logging system for NEXUS platform.

This module provides:
- Structured logging with structlog
- Log rotation and aggregation
- ELK stack ready JSON formatting
- Request logging middleware
- Error tracking
- Audit logging
- Log search API
"""

from nexus.logging.config import (
    setup_logging,
    get_logger,
    LogLevel,
)
from nexus.logging.audit import AuditLogger
from nexus.logging.error_tracker import ErrorTracker

__all__ = [
    "setup_logging",
    "get_logger",
    "LogLevel",
    "AuditLogger",
    "ErrorTracker",
]
