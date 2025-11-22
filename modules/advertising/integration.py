"""Integration with platform APIs."""

from typing import Dict, Any
from sqlalchemy.orm import Session

from .platforms import PlatformFactory
from .models import Campaign
from config.logging_config import get_logger

logger = get_logger(__name__)


class PlatformIntegration:
    """Platform API integration service."""

    def __init__(self, db: Session):
        self.db = db

    async def sync_campaign_to_platform(
        self,
        campaign_id: str,
    ) -> Dict[str, Any]:
        """Sync campaign to external platform."""
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id
        ).first()

        if not campaign:
            return {"error": "Campaign not found"}

        platform = PlatformFactory.get_platform(campaign.platform)
        
        result = await platform.create_campaign({
            "name": campaign.name,
            "objective": campaign.objective,
            "budget": campaign.daily_budget,
        })

        if result.get("platform_campaign_id"):
            campaign.platform_campaign_id = result["platform_campaign_id"]
            self.db.commit()

        logger.info(f"Campaign synced to {campaign.platform}: {campaign.name}")

        return result

    async def sync_performance_data(self) -> int:
        """Sync performance data from all platforms."""
        campaigns = self.db.query(Campaign).filter(
            Campaign.platform_campaign_id.isnot(None)
        ).all()

        synced = 0
        for campaign in campaigns:
            try:
                platform = PlatformFactory.get_platform(campaign.platform)
                perf = await platform.get_performance(campaign.platform_campaign_id)
                
                # Update campaign metrics
                campaign.impressions = perf.get("impressions", 0)
                campaign.clicks = perf.get("clicks", 0)
                campaign.conversions = perf.get("conversions", 0)
                campaign.spend = perf.get("spend", 0.0)
                
                synced += 1
            except Exception as e:
                logger.error(f"Error syncing campaign {campaign.id}: {e}")

        self.db.commit()
        logger.info(f"Synced performance data for {synced} campaigns")

        return synced
