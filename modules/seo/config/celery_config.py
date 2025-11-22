"""
Celery configuration and task queue setup.

Configures Celery for async task processing, scheduling,
and background job execution.
"""

from celery import Celery
from celery.schedules import crontab

from .settings import get_settings

settings = get_settings()

# Create Celery application
celery_app = Celery(
    "nexus_seo",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configure Celery
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
    # Result backend
    result_expires=86400,  # 24 hours
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    # Rank tracking - run every hour
    "track-rankings-hourly": {
        "task": "modules.seo.tasks.rank_tracking.track_all_rankings",
        "schedule": crontab(minute=0),  # Every hour
    },
    # Site audit - run daily at 2 AM
    "site-audit-daily": {
        "task": "modules.seo.tasks.site_audit.run_scheduled_audits",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    # Backlink check - run daily at 3 AM
    "backlink-check-daily": {
        "task": "modules.seo.tasks.backlink_analysis.check_backlinks",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    # Competitor analysis - run daily at 4 AM
    "competitor-analysis-daily": {
        "task": "modules.seo.tasks.competitor_analysis.analyze_competitors",
        "schedule": crontab(hour=4, minute=0),  # Daily at 4 AM
    },
    # Generate reports - run weekly on Monday at 8 AM
    "generate-reports-weekly": {
        "task": "modules.seo.tasks.reporting.generate_weekly_reports",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),  # Monday 8 AM
    },
    # Update keyword data - run daily at 1 AM
    "update-keyword-data": {
        "task": "modules.seo.tasks.keyword_research.update_keyword_metrics",
        "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    # Technical SEO checks - run daily at 5 AM
    "technical-seo-checks": {
        "task": "modules.seo.tasks.technical_seo.run_technical_checks",
        "schedule": crontab(hour=5, minute=0),  # Daily at 5 AM
    },
    # Generate sitemaps - run daily at 6 AM
    "generate-sitemaps": {
        "task": "modules.seo.tasks.sitemap.generate_all_sitemaps",
        "schedule": crontab(hour=6, minute=0),  # Daily at 6 AM
    },
}

# Task routes
celery_app.conf.task_routes = {
    "modules.seo.tasks.rank_tracking.*": {"queue": "rank_tracking"},
    "modules.seo.tasks.site_audit.*": {"queue": "site_audit"},
    "modules.seo.tasks.backlink_analysis.*": {"queue": "backlink"},
    "modules.seo.tasks.competitor_analysis.*": {"queue": "competitor"},
    "modules.seo.tasks.keyword_research.*": {"queue": "keyword"},
    "modules.seo.tasks.reporting.*": {"queue": "reporting"},
    "modules.seo.tasks.technical_seo.*": {"queue": "technical"},
    "modules.seo.tasks.sitemap.*": {"queue": "sitemap"},
    "modules.seo.tasks.content_optimization.*": {"queue": "content"},
    "modules.seo.tasks.ai_recommendations.*": {"queue": "ai"},
}

# Auto-discover tasks
celery_app.autodiscover_tasks([
    "modules.seo.tasks.rank_tracking",
    "modules.seo.tasks.site_audit",
    "modules.seo.tasks.backlink_analysis",
    "modules.seo.tasks.competitor_analysis",
    "modules.seo.tasks.keyword_research",
    "modules.seo.tasks.reporting",
    "modules.seo.tasks.technical_seo",
    "modules.seo.tasks.sitemap",
    "modules.seo.tasks.content_optimization",
    "modules.seo.tasks.ai_recommendations",
])
