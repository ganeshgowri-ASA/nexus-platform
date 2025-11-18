"""Performance optimization and A/B testing."""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import Campaign, AdPerformance
from config.logging_config import get_logger

logger = get_logger(__name__)


class CampaignOptimizer:
    """Campaign optimization service."""

    def __init__(self, db: Session):
        self.db = db

    async def analyze_performance(self, campaign_id: str) -> Dict[str, Any]:
        """Analyze campaign performance and provide recommendations."""
        perf = self.db.query(AdPerformance).filter(
            AdPerformance.campaign_id == campaign_id
        ).all()

        if not perf:
            return {"status": "no_data"}

        total_impressions = sum(p.impressions for p in perf)
        total_clicks = sum(p.clicks for p in perf)
        total_spend = sum(p.spend for p in perf)
        total_conversions = sum(p.conversions for p in perf)

        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
        cpa = (total_spend / total_conversions) if total_conversions > 0 else 0

        recommendations = []
        if ctr < 1.0:
            recommendations.append("Low CTR - Consider improving ad copy or targeting")
        if cpc > 5.0:
            recommendations.append("High CPC - Consider adjusting bids or improving quality score")
        if cpa > 50.0:
            recommendations.append("High CPA - Review landing page and conversion funnel")

        return {
            "ctr": round(ctr, 2),
            "cpc": round(cpc, 2),
            "cpa": round(cpa, 2),
            "recommendations": recommendations,
        }

    async def auto_pause_underperforming(self, threshold_cpa: float = 100.0) -> List[str]:
        """Automatically pause underperforming campaigns."""
        paused = []
        campaigns = self.db.query(Campaign).filter(Campaign.status == "active").all()

        for campaign in campaigns:
            analysis = await self.analyze_performance(campaign.id)
            if analysis.get("cpa", 0) > threshold_cpa:
                campaign.status = "paused"
                paused.append(campaign.id)
                logger.warning(f"Auto-paused campaign {campaign.name} due to high CPA")

        self.db.commit()
        return paused
