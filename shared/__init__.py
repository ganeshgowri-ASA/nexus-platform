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
