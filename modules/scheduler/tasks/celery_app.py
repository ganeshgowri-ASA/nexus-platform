"""Celery application configuration"""
from celery import Celery
from celery.schedules import crontab
from modules.scheduler.config import settings

# Create Celery app
celery_app = Celery(
    "nexus_scheduler",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['modules.scheduler.tasks.job_tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone=settings.DEFAULT_TIMEZONE,
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.TASK_TIMEOUT,
    task_soft_time_limit=settings.TASK_TIMEOUT - 60,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    result_expires=86400,  # 24 hours
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
)

# Beat schedule (for periodic tasks)
celery_app.conf.beat_schedule = {
    'check-scheduled-jobs': {
        'task': 'modules.scheduler.tasks.job_tasks.check_scheduled_jobs',
        'schedule': 60.0,  # Every minute
    },
    'cleanup-old-executions': {
        'task': 'modules.scheduler.tasks.job_tasks.cleanup_old_executions',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
