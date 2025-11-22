"""
NEXUS Analytics Module

Production-ready analytics module with comprehensive tracking,
analysis, and visualization capabilities.

Features:
- Real-time event tracking
- User behavior analysis
- Funnel and cohort analysis
- Predictive analytics
- Custom dashboards
- Data export
- Session replay
- Heatmaps
- A/B testing
- Attribution modeling
"""

from modules.analytics.core.tracker import EventTracker
from modules.analytics.core.aggregator import MetricsAggregator
from modules.analytics.core.processor import EventProcessor
from modules.analytics.models.event import Event, EventCreate
from modules.analytics.models.metric import Metric, MetricCreate

__version__ = "1.0.0"

__all__ = [
    "EventTracker",
    "MetricsAggregator",
    "EventProcessor",
    "Event",
    "EventCreate",
    "Metric",
    "MetricCreate",
]
