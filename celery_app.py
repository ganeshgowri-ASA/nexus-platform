"""
<<<<<<< HEAD
<<<<<<< HEAD
Celery application for asynchronous tasks.

Handles:
- Scheduled content publishing
- Analytics synchronization
- Notification sending
- Recurring content generation
- Webhook processing
"""
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab
from loguru import logger

from config import settings
from database import SessionLocal
from modules.content_calendar import (
    ContentScheduler,
    IntegrationManager,
    AnalyticsManager,
    WorkflowManager,
)

# Initialize Celery
celery_app = Celery(
    "nexus_content_calendar",
=======
Celery application configuration for NEXUS Platform.

This module sets up Celery for async task processing.
"""
from celery import Celery
from config.settings import settings
=======
Celery application configuration.
"""
from celery import Celery
from celery.schedules import crontab

from config import get_settings

settings = get_settings()
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi

# Create Celery app
celery_app = Celery(
    "nexus",
<<<<<<< HEAD
>>>>>>> origin/claude/marketing-automation-module-01QZjZLNDEejmtRGTMvcovNS
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

<<<<<<< HEAD
# Celery configuration
=======
# Configure Celery
>>>>>>> origin/claude/marketing-automation-module-01QZjZLNDEejmtRGTMvcovNS
=======
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "tasks.lead_generation_tasks",
        "tasks.advertising_tasks"
    ]
)

# Configure Celery
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
<<<<<<< HEAD
<<<<<<< HEAD
    task_time_limit=30 * 60,  # 30 minutes
)


# Database session dependency
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


# Publishing Tasks
@celery_app.task(name="publish_scheduled_content")
def publish_scheduled_content_task(content_id: int, channels: list[str]) -> dict:
    """
    Publish scheduled content to channels.

    Args:
        content_id: Content ID to publish
        channels: List of channels to publish to

    Returns:
        Publishing results
    """
    logger.info(f"Publishing content {content_id} to {channels}")

    try:
        db = get_db()
        integration_mgr = IntegrationManager(db)

        results = integration_mgr.publish_content(content_id, channels)

        logger.info(f"Successfully published content {content_id}")
        return results

    except Exception as e:
        logger.error(f"Error publishing content {content_id}: {e}")
        raise


@celery_app.task(name="check_scheduled_content")
def check_scheduled_content_task() -> int:
    """
    Check for content scheduled to be published now.

    Returns:
        Number of content items processed
    """
    logger.info("Checking for scheduled content")

    try:
        from database import ContentItem, ContentStatus

        db = get_db()
        now = datetime.utcnow()

        # Find content scheduled for now (within 5 minute window)
        scheduled_content = (
            db.query(ContentItem)
            .filter(
                ContentItem.status == ContentStatus.SCHEDULED,
                ContentItem.scheduled_at <= now + timedelta(minutes=5),
                ContentItem.scheduled_at >= now - timedelta(minutes=5),
            )
            .all()
        )

        count = 0
        for content in scheduled_content:
            if content.channels:
                publish_scheduled_content_task.delay(content.id, content.channels)
                count += 1

        logger.info(f"Queued {count} content items for publishing")
        return count

    except Exception as e:
        logger.error(f"Error checking scheduled content: {e}")
        return 0


# Analytics Tasks
@celery_app.task(name="sync_content_analytics")
def sync_content_analytics_task(content_id: int) -> dict:
    """
    Sync analytics for content from external platforms.

    Args:
        content_id: Content ID

    Returns:
        Sync results
    """
    logger.info(f"Syncing analytics for content {content_id}")

    try:
        db = get_db()
        integration_mgr = IntegrationManager(db)

        results = integration_mgr.sync_analytics(content_id)

        logger.info(f"Successfully synced analytics for content {content_id}")
        return results

    except Exception as e:
        logger.error(f"Error syncing analytics for content {content_id}: {e}")
        raise


@celery_app.task(name="sync_all_analytics")
def sync_all_analytics_task() -> int:
    """
    Sync analytics for all published content.

    Returns:
        Number of content items processed
    """
    logger.info("Syncing analytics for all published content")

    try:
        from database import ContentItem, ContentStatus

        db = get_db()

        # Find published content
        published_content = (
            db.query(ContentItem)
            .filter(ContentItem.status == ContentStatus.PUBLISHED)
            .all()
        )

        count = 0
        for content in published_content:
            sync_content_analytics_task.delay(content.id)
            count += 1

        logger.info(f"Queued {count} content items for analytics sync")
        return count

    except Exception as e:
        logger.error(f"Error syncing all analytics: {e}")
        return 0


# Notification Tasks
@celery_app.task(name="send_deadline_reminders")
def send_deadline_reminders_task() -> int:
    """
    Send reminders for upcoming deadlines.

    Returns:
        Number of reminders sent
    """
    logger.info("Sending deadline reminders")

    try:
        db = get_db()
        workflow_mgr = WorkflowManager(db)

        count = workflow_mgr.send_deadline_reminders(days_before=1)

        logger.info(f"Sent {count} deadline reminders")
        return count

    except Exception as e:
        logger.error(f"Error sending deadline reminders: {e}")
        return 0


@celery_app.task(name="send_notification")
def send_notification_task(
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
) -> bool:
    """
    Send notification to user.

    Args:
        user_id: User ID
        notification_type: Type of notification
        title: Notification title
        message: Notification message

    Returns:
        True if sent successfully
    """
    logger.info(f"Sending notification to user {user_id}: {title}")

    try:
        # In production, integrate with notification service
        # (push notifications, email, SMS, etc.)
        logger.info(f"Notification sent: {notification_type} - {title}")
        return True

    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return False


# Recurring Content Tasks
@celery_app.task(name="generate_recurring_content")
def generate_recurring_content_task() -> int:
    """
    Generate instances of recurring content.

    Returns:
        Number of content instances created
    """
    logger.info("Generating recurring content instances")

    try:
        from database import ContentItem

        db = get_db()

        # Find content with recurring patterns
        # This would check metadata for recurring patterns
        recurring_content = (
            db.query(ContentItem)
            .filter(ContentItem.metadata.contains({"is_recurring": True}))
            .all()
        )

        count = 0
        for content in recurring_content:
            # Generate next occurrence
            # Implementation would check recurring pattern and create next instance
            logger.info(f"Processing recurring content {content.id}")
            count += 1

        logger.info(f"Generated {count} recurring content instances")
        return count

    except Exception as e:
        logger.error(f"Error generating recurring content: {e}")
        return 0


# Maintenance Tasks
@celery_app.task(name="cleanup_old_data")
def cleanup_old_data_task(days: int = 90) -> int:
    """
    Clean up old archived data.

    Args:
        days: Delete data older than this many days

    Returns:
        Number of records deleted
    """
    logger.info(f"Cleaning up data older than {days} days")

    try:
        from database import ContentItem, ContentStatus

        db = get_db()
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Delete archived content
        deleted = (
            db.query(ContentItem)
            .filter(
                ContentItem.status == ContentStatus.ARCHIVED,
                ContentItem.updated_at < cutoff_date,
            )
            .delete()
        )

        db.commit()

        logger.info(f"Deleted {deleted} archived content items")
        return deleted

    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        db.rollback()
        return 0


# Periodic task schedule
celery_app.conf.beat_schedule = {
    # Check for scheduled content every minute
    "check-scheduled-content": {
        "task": "check_scheduled_content",
        "schedule": crontab(minute="*"),
    },
    # Sync analytics every hour
    "sync-all-analytics": {
        "task": "sync_all_analytics",
        "schedule": crontab(minute=0),  # Every hour
    },
    # Send deadline reminders daily at 9 AM
    "send-deadline-reminders": {
        "task": "send_deadline_reminders",
        "schedule": crontab(hour=9, minute=0),
    },
    # Generate recurring content daily at midnight
    "generate-recurring-content": {
        "task": "generate_recurring_content",
        "schedule": crontab(hour=0, minute=0),
    },
    # Clean up old data weekly
    "cleanup-old-data": {
        "task": "cleanup_old_data",
        "schedule": crontab(day_of_week=0, hour=2, minute=0),  # Sunday at 2 AM
    },
}


if __name__ == "__main__":
    celery_app.start()
=======
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["src.tasks.marketing"])
>>>>>>> origin/claude/marketing-automation-module-01QZjZLNDEejmtRGTMvcovNS
=======
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
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi
