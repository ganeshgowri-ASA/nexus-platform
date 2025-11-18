"""
Celery Application

Celery configuration for async task processing.
"""

import logging
from typing import Optional

from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)


class CeleryConfig:
    """Celery configuration."""

    def __init__(
        self,
        broker_url: str = "redis://localhost:6379/0",
        result_backend: str = "redis://localhost:6379/0",
        task_serializer: str = "json",
        result_serializer: str = "json",
        accept_content: list = None,
        timezone: str = "UTC",
        enable_utc: bool = True,
        task_track_started: bool = True,
        task_time_limit: int = 3600,
        task_soft_time_limit: int = 3000,
        worker_prefetch_multiplier: int = 4,
        worker_max_tasks_per_child: int = 1000,
    ):
        """Initialize Celery configuration."""
        self.broker_url = broker_url
        self.result_backend = result_backend
        self.task_serializer = task_serializer
        self.result_serializer = result_serializer
        self.accept_content = accept_content or ["json"]
        self.timezone = timezone
        self.enable_utc = enable_utc
        self.task_track_started = task_track_started
        self.task_time_limit = task_time_limit
        self.task_soft_time_limit = task_soft_time_limit
        self.worker_prefetch_multiplier = worker_prefetch_multiplier
        self.worker_max_tasks_per_child = worker_max_tasks_per_child


def create_celery_app(config: CeleryConfig) -> Celery:
    """
    Create and configure Celery application.

    Args:
        config: Celery configuration

    Returns:
        Configured Celery application
    """
    app = Celery("nexus_analytics")

    # Configure from config object
    app.conf.update(
        broker_url=config.broker_url,
        result_backend=config.result_backend,
        task_serializer=config.task_serializer,
        result_serializer=config.result_serializer,
        accept_content=config.accept_content,
        timezone=config.timezone,
        enable_utc=config.enable_utc,
        task_track_started=config.task_track_started,
        task_time_limit=config.task_time_limit,
        task_soft_time_limit=config.task_soft_time_limit,
        worker_prefetch_multiplier=config.worker_prefetch_multiplier,
        worker_max_tasks_per_child=config.worker_max_tasks_per_child,
    )

    # Configure beat schedule
    app.conf.beat_schedule = {
        "process-events-every-minute": {
            "task": "modules.analytics.processing.tasks.process_events_task",
            "schedule": 60.0,  # Every minute
        },
        "aggregate-metrics-hourly": {
            "task": "modules.analytics.processing.tasks.aggregate_metrics_task",
            "schedule": crontab(minute=0),  # Every hour
        },
        "cleanup-expired-exports": {
            "task": "modules.analytics.processing.tasks.cleanup_exports_task",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        },
    }

    logger.info("Celery application created")
    return app


# Global Celery instance
_celery_app: Optional[Celery] = None


def init_celery(config: CeleryConfig) -> Celery:
    """Initialize global Celery instance."""
    global _celery_app
    _celery_app = create_celery_app(config)
    return _celery_app


def get_celery() -> Celery:
    """Get global Celery instance."""
    if _celery_app is None:
        raise RuntimeError("Celery not initialized")
    return _celery_app
