<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
"""Shared utilities and configurations for NEXUS platform."""
=======
"""Shared utilities and infrastructure for NEXUS platform."""

__version__ = "1.0.0"
>>>>>>> origin/claude/contracts-management-module-01FmzTmE3DeZrdwEsMYTdLB9
=======
"""
NEXUS Platform - Shared Utilities

This package contains shared utilities, configuration, and constants
used across all NEXUS platform modules.
"""

from shared.config import get_settings, Settings
from shared.logger import get_logger, setup_logging
from shared.constants import (
    EventType,
    MetricType,
    AggregationPeriod,
    ExportFormat,
    AnalyticsStatus,
)

__all__ = [
    "get_settings",
    "Settings",
    "get_logger",
    "setup_logging",
    "EventType",
    "MetricType",
    "AggregationPeriod",
    "ExportFormat",
    "AnalyticsStatus",
]

__version__ = "1.0.0"
>>>>>>> origin/claude/nexus-analytics-module-01FAKqqMpzB1WpxsYvosEHzE
=======
"""Shared utilities and types for NEXUS platform."""

from .types import (
    PaginationParams,
    PaginatedResponse,
    FilterParams,
    SortParams,
)
from .utils import (
    generate_uuid,
    generate_slug,
    validate_email,
    validate_phone,
    sanitize_input,
)
from .exceptions import (
    NexusException,
    ValidationError,
    NotFoundError,
    PermissionError,
    RateLimitError,
)

__all__ = [
    "PaginationParams",
    "PaginatedResponse",
    "FilterParams",
    "SortParams",
    "generate_uuid",
    "generate_slug",
    "validate_email",
    "validate_phone",
    "sanitize_input",
    "NexusException",
    "ValidationError",
    "NotFoundError",
    "PermissionError",
    "RateLimitError",
]
>>>>>>> origin/claude/build-advertising-lead-generation-01Skr8pwxfdGAtz4wHoobrUL
