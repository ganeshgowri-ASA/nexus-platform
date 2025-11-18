"""
Celery application configuration for async task processing.

This module sets up Celery for background tasks like email sending,
report generation, and campaign automation.
"""

from celery import Celery
from celery.schedules import crontab

from app.config import settings


# Create Celery instance
celery_app = Celery(
    "nexus",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)


# Configure Celery
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    "calculate-campaign-performance": {
        "task": "app.modules.campaign_manager.tasks.calculate_all_campaign_performance",
        "schedule": crontab(
            minute=0,
            hour=f"*/{settings.PERFORMANCE_CALCULATION_INTERVAL_HOURS}"
        ),
    },
    "send-campaign-reports": {
        "task": "app.modules.campaign_manager.tasks.send_scheduled_reports",
        "schedule": crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    "cleanup-expired-campaigns": {
        "task": "app.modules.campaign_manager.tasks.cleanup_expired_campaigns",
        "schedule": crontab(hour=0, minute=0),  # Daily at midnight
    },
}


# Auto-discover tasks from all modules
celery_app.autodiscover_tasks([
    "app.modules.campaign_manager",
    "app.tasks",
])
