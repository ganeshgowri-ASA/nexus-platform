"""Reporting system for lead generation."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .analytics import LeadAnalytics
from .tracking import LeadTrackingSystem
from config.logging_config import get_logger

logger = get_logger(__name__)


class LeadReports:
    """Lead generation reporting service."""

    def __init__(self, db: Session):
        self.db = db
        self.analytics = LeadAnalytics(db)
        self.tracking = LeadTrackingSystem(db)

    async def generate_funnel_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate lead funnel report."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        from .models import Lead as LeadModel

        funnel = {}
        
        # Top of funnel - all leads
        funnel["total"] = self.db.query(LeadModel).filter(
            LeadModel.created_at.between(start_date, end_date)
        ).count()

        # Contacted
        funnel["contacted"] = self.db.query(LeadModel).filter(
            LeadModel.created_at.between(start_date, end_date),
            LeadModel.status.in_(["contacted", "qualified", "converted"])
        ).count()

        # Qualified (MQL)
        funnel["qualified"] = self.db.query(LeadModel).filter(
            LeadModel.created_at.between(start_date, end_date),
            LeadModel.status.in_(["qualified", "converted"])
        ).count()

        # Converted (SQL)
        funnel["converted"] = self.db.query(LeadModel).filter(
            LeadModel.created_at.between(start_date, end_date),
            LeadModel.status == "converted"
        ).count()

        # Calculate conversion rates
        funnel["contact_rate"] = (funnel["contacted"] / funnel["total"] * 100) if funnel["total"] > 0 else 0
        funnel["qualification_rate"] = (funnel["qualified"] / funnel["contacted"] * 100) if funnel["contacted"] > 0 else 0
        funnel["conversion_rate"] = (funnel["converted"] / funnel["qualified"] * 100) if funnel["qualified"] > 0 else 0

        return funnel

    async def generate_source_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate source performance report."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        sources = await self.analytics.get_source_performance(start_date, end_date)

        return {
            "sources": sources,
            "period": {"start": start_date, "end": end_date},
        }

    async def generate_roi_report(
        self,
        campaign_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate ROI report for campaign."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        roi = await self.tracking.calculate_roi(campaign_id, start_date, end_date)

        return roi
