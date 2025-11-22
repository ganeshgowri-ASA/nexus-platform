"""
Analytics service for marketing automation.

This module handles campaign analytics, attribution, and reporting.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from config.logging_config import get_logger
from src.models.campaign import Campaign, CampaignMessage
from src.models.analytics import CampaignAnalytics, LinkClick, Attribution
from src.core.utils import calculate_percentage

logger = get_logger(__name__)


class AnalyticsService:
    """Service for marketing analytics and reporting."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize analytics service."""
        self.db = db

    async def get_campaign_analytics(
        self,
        campaign_id: UUID,
        workspace_id: UUID,
    ) -> Dict[str, Any]:
        """Get detailed campaign analytics."""
        # Get campaign
        result = await self.db.execute(
            select(Campaign).where(
                Campaign.id == campaign_id,
                Campaign.workspace_id == workspace_id
            )
        )
        campaign = result.scalar_one()

        # Calculate metrics
        open_rate = calculate_percentage(campaign.total_opened, campaign.total_delivered)
        click_rate = calculate_percentage(campaign.total_clicked, campaign.total_delivered)
        bounce_rate = calculate_percentage(campaign.total_bounced, campaign.total_sent)

        return {
            "campaign_id": str(campaign.id),
            "campaign_name": campaign.name,
            "status": campaign.status.value,
            "sent_at": campaign.sent_at.isoformat() if campaign.sent_at else None,
            "metrics": {
                "total_recipients": campaign.total_recipients,
                "total_sent": campaign.total_sent,
                "total_delivered": campaign.total_delivered,
                "total_opened": campaign.total_opened,
                "total_clicked": campaign.total_clicked,
                "total_bounced": campaign.total_bounced,
                "total_unsubscribed": campaign.total_unsubscribed,
                "open_rate": open_rate,
                "click_rate": click_rate,
                "bounce_rate": bounce_rate,
            }
        }

    async def get_workspace_analytics(
        self,
        workspace_id: UUID,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get workspace-level analytics."""
        since = datetime.utcnow() - timedelta(days=days)

        # Get campaign count
        campaign_count_result = await self.db.execute(
            select(func.count(Campaign.id)).where(
                Campaign.workspace_id == workspace_id,
                Campaign.created_at >= since
            )
        )
        campaign_count = campaign_count_result.scalar()

        # Get total contacts
        from src.models.contact import Contact
        contact_count_result = await self.db.execute(
            select(func.count(Contact.id)).where(
                Contact.workspace_id == workspace_id
            )
        )
        contact_count = contact_count_result.scalar()

        return {
            "workspace_id": str(workspace_id),
            "period_days": days,
            "campaign_count": campaign_count,
            "contact_count": contact_count,
        }

    async def track_link_click(
        self,
        campaign_id: UUID,
        contact_id: UUID,
        message_id: UUID,
        url: str,
        user_agent: str,
        ip_address: str,
    ) -> LinkClick:
        """Track email link click."""
        link_click = LinkClick(
            campaign_id=campaign_id,
            contact_id=contact_id,
            message_id=message_id,
            url=url,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        self.db.add(link_click)
        await self.db.commit()
        await self.db.refresh(link_click)

        logger.info("Link click tracked", campaign_id=str(campaign_id), url=url)

        return link_click
