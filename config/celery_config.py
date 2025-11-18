"""
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
        },
    },
)


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
