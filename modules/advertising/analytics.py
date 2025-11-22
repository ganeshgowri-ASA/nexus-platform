"""Analytics and metrics for advertising."""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import Campaign, AdPerformance
from config.logging_config import get_logger

logger = get_logger(__name__)


class AdAnalytics:
    """Advertising analytics service."""

    def __init__(self, db: Session):
        self.db = db

    async def get_campaign_metrics(
        self,
        campaign_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Get comprehensive campaign metrics."""
        perf = self.db.query(AdPerformance).filter(
            AdPerformance.campaign_id == campaign_id,
            AdPerformance.date.between(start_date, end_date)
        ).all()

        total_impressions = sum(p.impressions for p in perf)
        total_clicks = sum(p.clicks for p in perf)
        total_conversions = sum(p.conversions for p in perf)
        total_spend = sum(p.spend for p in perf)
        total_revenue = sum(p.revenue or 0 for p in perf)

        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
        cpa = (total_spend / total_conversions) if total_conversions > 0 else 0
        roas = (total_revenue / total_spend) if total_spend > 0 else 0

        return {
            "impressions": total_impressions,
            "clicks": total_clicks,
            "conversions": total_conversions,
            "spend": round(total_spend, 2),
            "revenue": round(total_revenue, 2),
            "ctr": round(ctr, 2),
            "cpc": round(cpc, 2),
            "cpa": round(cpa, 2),
            "roas": round(roas, 2),
        }

    async def get_cross_platform_metrics(self) -> List[Dict[str, Any]]:
        """Get metrics across all platforms."""
        campaigns = self.db.query(Campaign).all()
        
        platform_metrics = {}
        for campaign in campaigns:
            platform = campaign.platform
            if platform not in platform_metrics:
                platform_metrics[platform] = {
                    "campaigns": 0,
                    "spend": 0.0,
                    "conversions": 0,
                }
            
            platform_metrics[platform]["campaigns"] += 1
            platform_metrics[platform]["spend"] += campaign.spend
            platform_metrics[platform]["conversions"] += campaign.conversions

        return [
            {"platform": k, **v}
            for k, v in platform_metrics.items()
        ]
