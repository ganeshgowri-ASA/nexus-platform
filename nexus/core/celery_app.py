"""
Celery Application Configuration

Configures Celery for asynchronous task processing.
"""

from celery import Celery
from celery.schedules import crontab
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)

# Create Celery app
celery_app = Celery(
    "nexus",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=[settings.CELERY_ACCEPT_CONTENT],
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-translations": {
        "task": "nexus.modules.translation.tasks.cleanup_old_translations",
        "schedule": crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
    "update-translation-statistics": {
        "task": "nexus.modules.translation.tasks.update_translation_statistics",
        "schedule": crontab(minute=0),  # Run every hour
    },
    "cleanup-translation-cache": {
        "task": "nexus.modules.translation.tasks.cleanup_translation_cache",
        "schedule": crontab(hour=3, minute=0),  # Run at 3 AM daily
    },
}

# Auto-discover tasks from all modules
celery_app.autodiscover_tasks(
    [
        "nexus.modules.translation",
        "nexus.modules.auth",
        "nexus.modules.file_storage",
    ]
)

logger.info("Celery application configured successfully")
