"""Analytics and metrics for lead generation."""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import Lead as LeadModel, LeadSource, Form, LandingPage, Popup
from config.logging_config import get_logger

logger = get_logger(__name__)


class LeadAnalytics:
    """Lead generation analytics service."""

    def __init__(self, db: Session):
        self.db = db

    async def get_conversion_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Get conversion metrics for period."""
        # Total leads
        total_leads = self.db.query(LeadModel).filter(
            LeadModel.created_at.between(start_date, end_date)
        ).count()

        # Converted leads
        converted = self.db.query(LeadModel).filter(
            LeadModel.created_at.between(start_date, end_date),
            LeadModel.status == "converted"
        ).count()

        # Qualified leads
        qualified = self.db.query(LeadModel).filter(
            LeadModel.created_at.between(start_date, end_date),
            LeadModel.status == "qualified"
        ).count()

        conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0
        qualification_rate = (qualified / total_leads * 100) if total_leads > 0 else 0

        return {
            "total_leads": total_leads,
            "converted_leads": converted,
            "qualified_leads": qualified,
            "conversion_rate": round(conversion_rate, 2),
            "qualification_rate": round(qualification_rate, 2),
            "period": {"start": start_date, "end": end_date},
        }

    async def get_source_performance(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """Get performance metrics by source."""
        sources = self.db.query(LeadSource).all()
        
        performance = []
        for source in sources:
            leads = self.db.query(LeadModel).filter(
                LeadModel.source_id == source.id,
                LeadModel.created_at.between(start_date, end_date)
            ).count()

            converted = self.db.query(LeadModel).filter(
                LeadModel.source_id == source.id,
                LeadModel.created_at.between(start_date, end_date),
                LeadModel.status == "converted"
            ).count()

            conversion_rate = (converted / leads * 100) if leads > 0 else 0

            performance.append({
                "source": source.name,
                "leads": leads,
                "converted": converted,
                "conversion_rate": round(conversion_rate, 2),
            })

        return sorted(performance, key=lambda x: x["leads"], reverse=True)

    async def get_lead_quality_metrics(self) -> Dict[str, Any]:
        """Get lead quality metrics."""
        avg_score = self.db.query(func.avg(LeadModel.score)).scalar() or 0

        score_distribution = {
            "high": self.db.query(LeadModel).filter(LeadModel.score >= 70).count(),
            "medium": self.db.query(LeadModel).filter(
                LeadModel.score >= 40, LeadModel.score < 70
            ).count(),
            "low": self.db.query(LeadModel).filter(LeadModel.score < 40).count(),
        }

        return {
            "average_score": round(avg_score, 2),
            "score_distribution": score_distribution,
        }
