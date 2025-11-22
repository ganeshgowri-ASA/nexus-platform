"""UTM tracking, source attribution, and campaign tracking."""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .models import Lead as LeadModel, TouchpointRecord
from shared.utils import generate_uuid
from config.logging_config import get_logger

logger = get_logger(__name__)


class LeadTrackingSystem:
    """Lead tracking and attribution service."""

    def __init__(self, db: Session):
        self.db = db

    async def track_touchpoint(
        self,
        lead_id: str,
        channel: str,
        campaign_id: Optional[str] = None,
        content: Optional[str] = None,
        utm_params: Optional[Dict[str, str]] = None,
    ) -> TouchpointRecord:
        """Track a new touchpoint for lead."""
        touchpoint = TouchpointRecord(
            id=generate_uuid(),
            lead_id=lead_id,
            channel=channel,
            campaign_id=campaign_id,
            content=content or "",
            timestamp=datetime.utcnow(),
        )

        self.db.add(touchpoint)
        self.db.commit()
        self.db.refresh(touchpoint)

        logger.info(f"Touchpoint tracked: {lead_id} - {channel}")

        return touchpoint

    async def get_attribution_path(self, lead_id: str) -> List[Dict[str, Any]]:
        """Get full attribution path for lead."""
        touchpoints = self.db.query(TouchpointRecord).filter(
            TouchpointRecord.lead_id == lead_id
        ).order_by(TouchpointRecord.timestamp).all()

        return [
            {
                "channel": tp.channel,
                "campaign_id": tp.campaign_id,
                "timestamp": tp.timestamp,
                "content": tp.content,
            }
            for tp in touchpoints
        ]

    async def calculate_roi(
        self,
        campaign_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Calculate ROI for campaign."""
        # Get all leads from this campaign
        touchpoints = self.db.query(TouchpointRecord).filter(
            TouchpointRecord.campaign_id == campaign_id,
            TouchpointRecord.timestamp.between(start_date, end_date)
        ).all()

        total_leads = len(set(tp.lead_id for tp in touchpoints))
        
        # Get converted leads
        converted_leads = self.db.query(LeadModel).filter(
            LeadModel.id.in_([tp.lead_id for tp in touchpoints]),
            LeadModel.status == "converted"
        ).count()

        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0

        return {
            "campaign_id": campaign_id,
            "total_leads": total_leads,
            "converted_leads": converted_leads,
            "conversion_rate": conversion_rate,
            "period": {"start": start_date, "end": end_date},
        }
