"""Reporting for advertising campaigns."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .analytics import AdAnalytics
from config.logging_config import get_logger

logger = get_logger(__name__)


class AdReporting:
    """Advertising reporting service."""

    def __init__(self, db: Session):
        self.db = db
        self.analytics = AdAnalytics(db)

    async def generate_performance_report(
        self,
        campaign_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        metrics = await self.analytics.get_campaign_metrics(
            campaign_id, start_date, end_date
        )

        return {
            "campaign_id": campaign_id,
            "period": {"start": start_date, "end": end_date},
            "metrics": metrics,
        }

    async def generate_roi_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate ROI report across all campaigns."""
        from .models import Campaign
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        campaigns = self.db.query(Campaign).all()
        
        total_spend = sum(c.spend for c in campaigns)
        total_conversions = sum(c.conversions for c in campaigns)

        return {
            "period": {"start": start_date, "end": end_date},
            "total_spend": round(total_spend, 2),
            "total_conversions": total_conversions,
            "avg_cpa": round(total_spend / total_conversions, 2) if total_conversions > 0 else 0,
        }
