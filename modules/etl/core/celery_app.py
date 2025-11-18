"""Celery application configuration for ETL module."""
from celery import Celery
from shared.config import get_settings

settings = get_settings()

celery_app = Celery(
    "etl_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["modules.etl.core.tasks"],
)

# Celery configuration
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
    task_routes={
        "modules.etl.core.tasks.*": {"queue": "etl_queue"},
    },
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "check-scheduled-pipelines": {
        "task": "modules.etl.core.tasks.check_scheduled_pipelines",
        "schedule": 60.0,  # Every minute
    },
}
