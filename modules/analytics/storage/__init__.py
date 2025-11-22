"""
Analytics Storage Layer

Database and caching abstractions for analytics data.
"""

from modules.analytics.storage.database import (
    get_db,
    get_async_db,
    init_database,
    close_database,
)
from modules.analytics.storage.cache import RedisCache, get_cache
from modules.analytics.storage.models import (
    EventModel,
    MetricModel,
    SessionModel,
    UserModel,
    FunnelModel,
    CohortModel,
    GoalModel,
    ABTestModel,
)

__all__ = [
    "get_db",
    "get_async_db",
    "init_database",
    "close_database",
    "RedisCache",
    "get_cache",
    "EventModel",
    "MetricModel",
    "SessionModel",
    "UserModel",
    "FunnelModel",
    "CohortModel",
    "GoalModel",
    "ABTestModel",
]
