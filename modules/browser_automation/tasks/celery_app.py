"""Celery application configuration"""
from celery import Celery
from celery.schedules import crontab
from modules.browser_automation.config import settings

celery_app = Celery(
    "browser_automation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["modules.browser_automation.tasks.workflow_tasks"]
)

celery_app.conf.update(
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'check-scheduled-workflows': {
        'task': 'modules.browser_automation.tasks.workflow_tasks.check_scheduled_workflows',
        'schedule': 60.0,  # Check every minute
    },
}
