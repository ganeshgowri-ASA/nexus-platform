"""
Analytics Models

Pydantic models for analytics data structures.
"""

from modules.analytics.models.event import Event, EventCreate, EventUpdate
from modules.analytics.models.metric import Metric, MetricCreate, MetricUpdate
from modules.analytics.models.session import Session, SessionCreate, SessionUpdate
from modules.analytics.models.user import User, UserCreate, UserUpdate
from modules.analytics.models.funnel import Funnel, FunnelStep, FunnelCreate
from modules.analytics.models.cohort import Cohort, CohortCreate, CohortAnalysis
from modules.analytics.models.goal import Goal, GoalCreate, GoalConversion
from modules.analytics.models.ab_test import ABTest, ABTestCreate, ABTestVariantStats

__all__ = [
    "Event",
    "EventCreate",
    "EventUpdate",
    "Metric",
    "MetricCreate",
    "MetricUpdate",
    "Session",
    "SessionCreate",
    "SessionUpdate",
    "User",
    "UserCreate",
    "UserUpdate",
    "Funnel",
    "FunnelStep",
    "FunnelCreate",
    "Cohort",
    "CohortCreate",
    "CohortAnalysis",
    "Goal",
    "GoalCreate",
    "GoalConversion",
    "ABTest",
    "ABTestCreate",
    "ABTestVariantStats",
]
