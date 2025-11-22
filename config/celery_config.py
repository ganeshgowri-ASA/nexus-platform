"""
<<<<<<< HEAD
Celery Configuration for Nexus Platform
"""
from celery import Celery
from config.settings import settings

# Initialize Celery app
celery_app = Celery(
    "nexus_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'app.tasks.email_tasks',
        'app.tasks.file_tasks',
        'app.tasks.ai_tasks',
        'app.tasks.report_tasks',
    ]
)

# Celery Configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task execution settings
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,

    # Task routing - Different queues for different task types
    task_routes={
        'app.tasks.email_tasks.*': {'queue': settings.TASK_QUEUE_EMAIL},
        'app.tasks.file_tasks.*': {'queue': settings.TASK_QUEUE_FILE_PROCESSING},
        'app.tasks.ai_tasks.*': {'queue': settings.TASK_QUEUE_AI},
        'app.tasks.report_tasks.*': {'queue': settings.TASK_QUEUE_REPORTS},
    },

    # Task priority settings
    task_default_priority=5,

    # Beat scheduler settings (for periodic tasks)
    beat_schedule={
        'cleanup-temp-files': {
            'task': 'app.tasks.file_tasks.cleanup_temp_files',
            'schedule': 3600.0,  # Every hour
        },
        'cleanup-old-results': {
            'task': 'app.tasks.maintenance_tasks.cleanup_old_results',
            'schedule': 86400.0,  # Every day
=======
Celery configuration for async task processing.

This module provides Celery configuration and task management
for background jobs in the NEXUS platform.
"""

from celery import Celery
from celery.schedules import crontab

from .settings import settings
from .logging_config import get_logger

logger = get_logger(__name__)

# Initialize Celery app
celery_app = Celery(
    "nexus",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=270,  # 4.5 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
    # Task routes
    task_routes={
        "modules.lead_generation.tasks.*": {"queue": "lead_generation"},
        "modules.advertising.tasks.*": {"queue": "advertising"},
    },
    # Beat schedule for periodic tasks
    beat_schedule={
        "sync-ad-performance-hourly": {
            "task": "modules.advertising.tasks.sync_ad_performance",
            "schedule": crontab(minute=0),  # Every hour
        },
        "check-budget-alerts-hourly": {
            "task": "modules.advertising.tasks.check_budget_alerts",
            "schedule": crontab(minute=15),  # Every hour at :15
        },
        "enrich-leads-daily": {
            "task": "modules.lead_generation.tasks.enrich_pending_leads",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        "calculate-lead-scores-daily": {
            "task": "modules.lead_generation.tasks.calculate_lead_scores",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
        },
        "send-nurture-emails-hourly": {
            "task": "modules.lead_generation.tasks.send_nurture_emails",
            "schedule": crontab(minute=30),  # Every hour at :30
>>>>>>> origin/claude/build-advertising-lead-generation-01Skr8pwxfdGAtz4wHoobrUL
        },
    },
)

<<<<<<< HEAD
# Optional: Task annotations for specific task configurations
celery_app.conf.task_annotations = {
    'app.tasks.ai_tasks.*': {
        'rate_limit': '10/m',  # 10 AI tasks per minute
        'time_limit': 600,  # 10 minutes for AI tasks
    },
    'app.tasks.file_tasks.process_large_file': {
        'time_limit': 1800,  # 30 minutes for large files
    },
}
=======

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    logger.info(f"Request: {self.request!r}")
    return {"status": "ok", "message": "Celery is working!"}


# Task result handlers
@celery_app.task(bind=True, max_retries=3)
def retry_failed_task(self, task_id: str):
    """Retry a failed task."""
    try:
        from celery.result import AsyncResult
        result = AsyncResult(task_id, app=celery_app)
        if result.failed():
            logger.info(f"Retrying failed task: {task_id}")
            result.retry()
    except Exception as exc:
        logger.error(f"Failed to retry task {task_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


logger.info("Celery app configured successfully")
>>>>>>> origin/claude/build-advertising-lead-generation-01Skr8pwxfdGAtz4wHoobrUL
