"""Celery application configuration"""

from celery import Celery
from modules.webhooks.config import get_settings

settings = get_settings()

celery_app = Celery(
    "webhooks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["modules.webhooks.tasks.delivery_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes
    task_soft_time_limit=540,  # 9 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "retry-failed-webhooks": {
        "task": "modules.webhooks.tasks.delivery_tasks.retry_failed_webhooks",
        "schedule": 60.0,  # Every 60 seconds
    },
    "cleanup-old-deliveries": {
        "task": "modules.webhooks.tasks.delivery_tasks.cleanup_old_deliveries",
        "schedule": 86400.0,  # Every 24 hours
    },
}
