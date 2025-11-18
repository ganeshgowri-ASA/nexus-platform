"""
Celery application configuration.
"""
from celery import Celery
from celery.schedules import crontab

from config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "nexus",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "tasks.lead_generation_tasks",
        "tasks.advertising_tasks"
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
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    # Lead enrichment
    "enrich-pending-leads": {
        "task": "tasks.lead_generation_tasks.enrich_pending_leads",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
    # Lead scoring
    "score-unscored-leads": {
        "task": "tasks.lead_generation_tasks.score_unscored_leads",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    # Campaign sync
    "sync-campaign-metrics": {
        "task": "tasks.advertising_tasks.sync_all_campaign_metrics",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
    # Automated rules
    "process-automated-rules": {
        "task": "tasks.advertising_tasks.process_automated_rules",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
}

if __name__ == "__main__":
    celery_app.start()
