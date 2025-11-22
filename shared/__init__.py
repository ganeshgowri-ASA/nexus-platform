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
