"""Celery application configuration."""

from celery import Celery
from core.config import settings

# Create Celery app
celery_app = Celery(
    "nexus_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "modules.batch_processing.tasks",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
)

# Task routes (optional - for different queues)
celery_app.conf.task_routes = {
    "modules.batch_processing.tasks.*": {"queue": "batch_processing"},
}

if __name__ == "__main__":
    celery_app.start()
