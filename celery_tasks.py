"""Celery tasks for async operations."""

from config.celery_config import celery_app
from config.database import get_db_context
from config.logging_config import get_logger

logger = get_logger(__name__)


# Lead Generation Tasks

@celery_app.task(name="enrich_lead")
def enrich_lead_task(lead_id: str):
    """Enrich lead with external data."""
    try:
        with get_db_context() as db:
            from modules.lead_generation.enrichment import LeadEnricher
            
            enricher = LeadEnricher(db)
            import asyncio
            result = asyncio.run(enricher.enrich_lead(lead_id))
            
            logger.info(f"Lead enriched: {lead_id}")
            return result
    except Exception as e:
        logger.error(f"Error enriching lead {lead_id}: {e}")
        raise


@celery_app.task(name="calculate_lead_score")
def calculate_lead_score_task(lead_id: str):
    """Calculate lead score."""
    try:
        with get_db_context() as db:
            from modules.lead_generation.scoring import LeadScoring
            
            scorer = LeadScoring(db)
            import asyncio
            score = asyncio.run(scorer.calculate_score(lead_id))
            
            logger.info(f"Lead score calculated: {lead_id} = {score}")
            return score
    except Exception as e:
        logger.error(f"Error calculating score for {lead_id}: {e}")
        raise


@celery_app.task(name="send_nurture_emails")
def send_nurture_emails_task():
    """Send scheduled nurture emails."""
    logger.info("Processing nurture emails")
    # Implement email sending logic
    return {"status": "emails_sent"}


@celery_app.task(name="enrich_pending_leads")
def enrich_pending_leads_task():
    """Batch enrich pending leads."""
    try:
        with get_db_context() as db:
            from modules.lead_generation.models import Lead as LeadModel
            
            # Get leads without enrichment
            leads = db.query(LeadModel).filter(
                LeadModel.enriched_at.is_(None)
            ).limit(100).all()
            
            for lead in leads:
                enrich_lead_task.delay(lead.id)
            
            logger.info(f"Queued {len(leads)} leads for enrichment")
            return {"leads_queued": len(leads)}
    except Exception as e:
        logger.error(f"Error queuing leads for enrichment: {e}")
        raise


# Advertising Tasks

@celery_app.task(name="sync_ad_performance")
def sync_ad_performance_task():
    """Sync ad performance data from platforms."""
    try:
        with get_db_context() as db:
            from modules.advertising.integration import PlatformIntegration
            
            integration = PlatformIntegration(db)
            import asyncio
            synced = asyncio.run(integration.sync_performance_data())
            
            logger.info(f"Synced performance for {synced} campaigns")
            return {"campaigns_synced": synced}
    except Exception as e:
        logger.error(f"Error syncing ad performance: {e}")
        raise


@celery_app.task(name="check_budget_alerts")
def check_budget_alerts_task():
    """Check and alert on budget thresholds."""
    try:
        with get_db_context() as db:
            from modules.advertising.budgets import BudgetManager
            
            budget_mgr = BudgetManager(db)
            import asyncio
            alerts = asyncio.run(budget_mgr.check_budget_alerts())
            
            logger.info(f"Found {len(alerts)} budget alerts")
            return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Error checking budget alerts: {e}")
        raise


@celery_app.task(name="optimize_campaigns")
def optimize_campaigns_task():
    """Run campaign optimization."""
    try:
        with get_db_context() as db:
            from modules.advertising.automation import AutomationRules
            
            automation = AutomationRules(db)
            import asyncio
            results = asyncio.run(automation.apply_rules())
            
            logger.info(f"Optimization complete: {results}")
            return results
    except Exception as e:
        logger.error(f"Error optimizing campaigns: {e}")
        raise
