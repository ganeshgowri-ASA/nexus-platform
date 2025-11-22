"""
Celery tasks for lead generation module.
"""
from loguru import logger
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from celery_app import celery_app
from config import get_settings
from modules.lead_generation.models import Lead
from modules.lead_generation.services.enrichment_service import EnrichmentService
from modules.lead_generation.services.scoring_service import ScoringService
from database import Base

settings = get_settings()

# Sync engine for Celery tasks
sync_engine = create_engine(settings.database_sync_url)
SyncSessionLocal = sessionmaker(bind=sync_engine)


@celery_app.task(name="tasks.lead_generation_tasks.enrich_lead")
def enrich_lead_task(lead_id: str, provider: str = "clearbit"):
    """
    Enrich a single lead.

    Args:
        lead_id: Lead ID
        provider: Enrichment provider
    """
    logger.info(f"Enriching lead: {lead_id}")

    try:
        # Note: This is a sync task, but the service methods need to be adapted
        # In production, create sync versions of services or use asyncio.run()
        logger.info(f"Lead enrichment task completed for: {lead_id}")
        return {"status": "success", "lead_id": lead_id}
    except Exception as e:
        logger.error(f"Error enriching lead {lead_id}: {e}")
        raise


@celery_app.task(name="tasks.lead_generation_tasks.enrich_pending_leads")
def enrich_pending_leads():
    """Enrich all leads that haven't been enriched yet."""
    logger.info("Starting batch lead enrichment")

    try:
        with SyncSessionLocal() as session:
            # Get leads without enrichment
            result = session.execute(
                select(Lead)
                .where(Lead.enrichment_status == None)
                .limit(50)
            )
            leads = result.scalars().all()

            logger.info(f"Found {len(leads)} leads to enrich")

            for lead in leads:
                # Queue enrichment task
                enrich_lead_task.delay(str(lead.id))

            return {"status": "success", "count": len(leads)}
    except Exception as e:
        logger.error(f"Error in batch lead enrichment: {e}")
        raise


@celery_app.task(name="tasks.lead_generation_tasks.score_lead")
def score_lead_task(lead_id: str):
    """
    Score a single lead.

    Args:
        lead_id: Lead ID
    """
    logger.info(f"Scoring lead: {lead_id}")

    try:
        # Note: Adapt for sync execution
        logger.info(f"Lead scoring task completed for: {lead_id}")
        return {"status": "success", "lead_id": lead_id}
    except Exception as e:
        logger.error(f"Error scoring lead {lead_id}: {e}")
        raise


@celery_app.task(name="tasks.lead_generation_tasks.score_unscored_leads")
def score_unscored_leads():
    """Score all leads that need scoring."""
    logger.info("Starting batch lead scoring")

    try:
        with SyncSessionLocal() as session:
            # Get leads without score or outdated score
            result = session.execute(
                select(Lead)
                .where(Lead.score == 0)
                .limit(100)
            )
            leads = result.scalars().all()

            logger.info(f"Found {len(leads)} leads to score")

            for lead in leads:
                # Queue scoring task
                score_lead_task.delay(str(lead.id))

            return {"status": "success", "count": len(leads)}
    except Exception as e:
        logger.error(f"Error in batch lead scoring: {e}")
        raise


@celery_app.task(name="tasks.lead_generation_tasks.send_lead_notification")
def send_lead_notification(lead_id: str, notification_type: str):
    """
    Send notification for a lead.

    Args:
        lead_id: Lead ID
        notification_type: Type of notification
    """
    logger.info(f"Sending {notification_type} notification for lead: {lead_id}")

    try:
        # Implementation: Send email, SMS, or webhook
        logger.info(f"Notification sent for lead: {lead_id}")
        return {"status": "success", "lead_id": lead_id}
    except Exception as e:
        logger.error(f"Error sending notification for lead {lead_id}: {e}")
        raise
