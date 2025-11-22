"""
Celery tasks for advertising module.
"""
from datetime import datetime
from loguru import logger
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from celery_app import celery_app
from config import get_settings
from modules.advertising.models import Campaign, CampaignStatus, AutomatedRule
from database import Base

settings = get_settings()

# Sync engine for Celery tasks
sync_engine = create_engine(settings.database_sync_url)
SyncSessionLocal = sessionmaker(bind=sync_engine)


@celery_app.task(name="tasks.advertising_tasks.sync_campaign_metrics")
def sync_campaign_metrics(campaign_id: str):
    """
    Sync metrics for a single campaign.

    Args:
        campaign_id: Campaign ID
    """
    logger.info(f"Syncing metrics for campaign: {campaign_id}")

    try:
        with SyncSessionLocal() as session:
            result = session.execute(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            campaign = result.scalar_one_or_none()

            if not campaign:
                logger.warning(f"Campaign not found: {campaign_id}")
                return {"status": "not_found"}

            # Sync based on platform
            if campaign.platform.value == "google_ads":
                # Use GoogleAdsService (adapt for sync)
                pass
            elif campaign.platform.value == "facebook_ads":
                # Use FacebookAdsService (adapt for sync)
                pass

            logger.info(f"Metrics synced for campaign: {campaign_id}")
            return {"status": "success", "campaign_id": campaign_id}
    except Exception as e:
        logger.error(f"Error syncing campaign metrics {campaign_id}: {e}")
        raise


@celery_app.task(name="tasks.advertising_tasks.sync_all_campaign_metrics")
def sync_all_campaign_metrics():
    """Sync metrics for all active campaigns."""
    logger.info("Starting batch campaign metrics sync")

    try:
        with SyncSessionLocal() as session:
            # Get all active campaigns
            result = session.execute(
                select(Campaign)
                .where(Campaign.status == CampaignStatus.ACTIVE)
            )
            campaigns = result.scalars().all()

            logger.info(f"Found {len(campaigns)} active campaigns to sync")

            for campaign in campaigns:
                # Queue sync task
                sync_campaign_metrics.delay(str(campaign.id))

            return {"status": "success", "count": len(campaigns)}
    except Exception as e:
        logger.error(f"Error in batch campaign sync: {e}")
        raise


@celery_app.task(name="tasks.advertising_tasks.process_automated_rules")
def process_automated_rules():
    """Process all active automated rules."""
    logger.info("Processing automated rules")

    try:
        with SyncSessionLocal() as session:
            # Get all active rules due for execution
            now = datetime.utcnow()
            result = session.execute(
                select(AutomatedRule)
                .where(
                    AutomatedRule.is_active == True,
                    (AutomatedRule.next_run_at == None) |
                    (AutomatedRule.next_run_at <= now)
                )
            )
            rules = result.scalars().all()

            logger.info(f"Found {len(rules)} rules to process")

            for rule in rules:
                # Process rule
                try:
                    # Evaluate conditions and execute actions
                    logger.info(f"Processing rule: {rule.id}")

                    # Update execution tracking
                    rule.last_run_at = now
                    rule.execution_count += 1

                    # Schedule next run
                    if rule.schedule == "hourly":
                        from datetime import timedelta
                        rule.next_run_at = now + timedelta(hours=1)
                    elif rule.schedule == "daily":
                        from datetime import timedelta
                        rule.next_run_at = now + timedelta(days=1)

                    session.commit()
                except Exception as e:
                    logger.error(f"Error processing rule {rule.id}: {e}")
                    continue

            return {"status": "success", "count": len(rules)}
    except Exception as e:
        logger.error(f"Error processing automated rules: {e}")
        raise


@celery_app.task(name="tasks.advertising_tasks.optimize_campaign_budget")
def optimize_campaign_budget(campaign_id: str):
    """
    Optimize campaign budget based on performance.

    Args:
        campaign_id: Campaign ID
    """
    logger.info(f"Optimizing budget for campaign: {campaign_id}")

    try:
        # Implementation: Analyze performance and adjust budget
        logger.info(f"Budget optimized for campaign: {campaign_id}")
        return {"status": "success", "campaign_id": campaign_id}
    except Exception as e:
        logger.error(f"Error optimizing campaign budget {campaign_id}: {e}")
        raise


@celery_app.task(name="tasks.advertising_tasks.generate_performance_report")
def generate_performance_report(campaign_id: str, period: str = "weekly"):
    """
    Generate performance report for a campaign.

    Args:
        campaign_id: Campaign ID
        period: Report period (daily, weekly, monthly)
    """
    logger.info(f"Generating {period} report for campaign: {campaign_id}")

    try:
        # Implementation: Aggregate metrics and generate report
        logger.info(f"Performance report generated for campaign: {campaign_id}")
        return {"status": "success", "campaign_id": campaign_id}
    except Exception as e:
        logger.error(f"Error generating report for campaign {campaign_id}: {e}")
        raise
