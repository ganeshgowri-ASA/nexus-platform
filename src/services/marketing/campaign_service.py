"""
Campaign service for marketing automation.

This module handles all campaign-related business logic including creation,
management, scheduling, and metrics tracking.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from config.logging_config import get_logger
from config.constants import CampaignStatus, MessageStatus, CampaignType
from src.core.exceptions import NotFoundError, ValidationError, CampaignError
from src.core.llm_client import llm_client
from src.models.campaign import Campaign, CampaignMessage, EmailTemplate, ABTest
from src.models.contact import Contact
from src.schemas.marketing.campaign_schema import (
    CampaignCreate,
    CampaignUpdate,
    CampaignMetrics,
)

logger = get_logger(__name__)


class CampaignService:
    """
    Service for managing marketing campaigns.

    Provides methods for campaign CRUD operations, sending, scheduling,
    and analytics.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize campaign service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_campaign(
        self,
        campaign_data: CampaignCreate,
        workspace_id: UUID,
        user_id: UUID,
    ) -> Campaign:
        """
        Create a new campaign.

        Args:
            campaign_data: Campaign creation data
            workspace_id: Workspace ID
            user_id: User ID creating the campaign

        Returns:
            Created campaign

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Create campaign
            campaign = Campaign(
                workspace_id=workspace_id,
                name=campaign_data.name,
                description=campaign_data.description,
                type=campaign_data.type,
                subject=campaign_data.subject,
                content=campaign_data.content,
                from_name=campaign_data.from_name,
                from_email=campaign_data.from_email,
                reply_to=campaign_data.reply_to,
                segment_id=campaign_data.segment_id,
                scheduled_at=campaign_data.scheduled_at,
                created_by=user_id,
                status=CampaignStatus.DRAFT,
                metadata=campaign_data.metadata or {},
            )

            self.db.add(campaign)
            await self.db.commit()
            await self.db.refresh(campaign)

            logger.info(
                "Campaign created",
                campaign_id=str(campaign.id),
                workspace_id=str(workspace_id),
                user_id=str(user_id)
            )

            return campaign

        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to create campaign", error=str(e))
            raise CampaignError(f"Failed to create campaign: {str(e)}")

    async def get_campaign(
        self,
        campaign_id: UUID,
        workspace_id: UUID,
    ) -> Campaign:
        """
        Get campaign by ID.

        Args:
            campaign_id: Campaign ID
            workspace_id: Workspace ID

        Returns:
            Campaign

        Raises:
            NotFoundError: If campaign not found
        """
        result = await self.db.execute(
            select(Campaign).where(
                Campaign.id == campaign_id,
                Campaign.workspace_id == workspace_id
            )
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise NotFoundError("Campaign", str(campaign_id))

        return campaign

    async def list_campaigns(
        self,
        workspace_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[CampaignStatus] = None,
    ) -> Dict[str, Any]:
        """
        List campaigns for workspace.

        Args:
            workspace_id: Workspace ID
            page: Page number
            page_size: Items per page
            status: Filter by status

        Returns:
            Dictionary with campaigns and pagination info
        """
        query = select(Campaign).where(Campaign.workspace_id == workspace_id)

        if status:
            query = query.where(Campaign.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(Campaign.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        campaigns = result.scalars().all()

        return {
            "campaigns": campaigns,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    async def update_campaign(
        self,
        campaign_id: UUID,
        workspace_id: UUID,
        campaign_data: CampaignUpdate,
    ) -> Campaign:
        """
        Update campaign.

        Args:
            campaign_id: Campaign ID
            workspace_id: Workspace ID
            campaign_data: Update data

        Returns:
            Updated campaign

        Raises:
            NotFoundError: If campaign not found
            ValidationError: If update is invalid
        """
        campaign = await self.get_campaign(campaign_id, workspace_id)

        # Don't allow updates if campaign is running
        if campaign.status in [CampaignStatus.RUNNING, CampaignStatus.COMPLETED]:
            raise ValidationError(
                f"Cannot update campaign with status {campaign.status.value}"
            )

        # Update fields
        update_data = campaign_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(campaign, key, value)

        campaign.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(campaign)

        logger.info("Campaign updated", campaign_id=str(campaign_id))

        return campaign

    async def delete_campaign(
        self,
        campaign_id: UUID,
        workspace_id: UUID,
    ) -> None:
        """
        Delete campaign.

        Args:
            campaign_id: Campaign ID
            workspace_id: Workspace ID

        Raises:
            NotFoundError: If campaign not found
            ValidationError: If campaign cannot be deleted
        """
        campaign = await self.get_campaign(campaign_id, workspace_id)

        if campaign.status == CampaignStatus.RUNNING:
            raise ValidationError("Cannot delete running campaign")

        await self.db.delete(campaign)
        await self.db.commit()

        logger.info("Campaign deleted", campaign_id=str(campaign_id))

    async def generate_content_with_ai(
        self,
        campaign_goal: str,
        target_audience: str,
        key_points: List[str],
        tone: str = "professional",
    ) -> Dict[str, str]:
        """
        Generate campaign content using AI.

        Args:
            campaign_goal: Campaign goal/objective
            target_audience: Target audience description
            key_points: Key points to include
            tone: Content tone

        Returns:
            Dictionary with subject and body
        """
        try:
            content = await llm_client.generate_email_content(
                campaign_goal=campaign_goal,
                target_audience=target_audience,
                key_points=key_points,
                tone=tone,
                include_cta=True,
            )

            logger.info("AI content generated", campaign_goal=campaign_goal)

            return content

        except Exception as e:
            logger.error("Failed to generate AI content", error=str(e))
            raise CampaignError(f"Failed to generate content: {str(e)}")

    async def get_campaign_metrics(
        self,
        campaign_id: UUID,
        workspace_id: UUID,
    ) -> CampaignMetrics:
        """
        Get campaign metrics.

        Args:
            campaign_id: Campaign ID
            workspace_id: Workspace ID

        Returns:
            Campaign metrics

        Raises:
            NotFoundError: If campaign not found
        """
        campaign = await self.get_campaign(campaign_id, workspace_id)

        # Calculate rates
        open_rate = 0.0
        click_rate = 0.0
        bounce_rate = 0.0
        unsubscribe_rate = 0.0

        if campaign.total_delivered > 0:
            open_rate = (campaign.total_opened / campaign.total_delivered) * 100
            click_rate = (campaign.total_clicked / campaign.total_delivered) * 100

        if campaign.total_sent > 0:
            bounce_rate = (campaign.total_bounced / campaign.total_sent) * 100
            unsubscribe_rate = (campaign.total_unsubscribed / campaign.total_sent) * 100

        return CampaignMetrics(
            total_recipients=campaign.total_recipients,
            total_sent=campaign.total_sent,
            total_delivered=campaign.total_delivered,
            total_opened=campaign.total_opened,
            total_clicked=campaign.total_clicked,
            total_bounced=campaign.total_bounced,
            total_unsubscribed=campaign.total_unsubscribed,
            open_rate=round(open_rate, 2),
            click_rate=round(click_rate, 2),
            bounce_rate=round(bounce_rate, 2),
            unsubscribe_rate=round(unsubscribe_rate, 2),
        )

    async def schedule_campaign(
        self,
        campaign_id: UUID,
        workspace_id: UUID,
        scheduled_at: datetime,
    ) -> Campaign:
        """
        Schedule campaign for sending.

        Args:
            campaign_id: Campaign ID
            workspace_id: Workspace ID
            scheduled_at: Scheduled send time

        Returns:
            Updated campaign

        Raises:
            NotFoundError: If campaign not found
            ValidationError: If scheduling is invalid
        """
        campaign = await self.get_campaign(campaign_id, workspace_id)

        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
            raise ValidationError(
                f"Cannot schedule campaign with status {campaign.status.value}"
            )

        if scheduled_at <= datetime.utcnow():
            raise ValidationError("Scheduled time must be in the future")

        campaign.scheduled_at = scheduled_at
        campaign.status = CampaignStatus.SCHEDULED
        campaign.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(campaign)

        logger.info(
            "Campaign scheduled",
            campaign_id=str(campaign_id),
            scheduled_at=scheduled_at.isoformat()
        )

        return campaign

    async def update_message_status(
        self,
        message_id: UUID,
        status: MessageStatus,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update campaign message status.

        Args:
            message_id: Message ID
            status: New status
            error_message: Error message if failed
        """
        timestamp = datetime.utcnow()

        update_data: Dict[str, Any] = {
            "status": status,
            "updated_at": timestamp,
        }

        if status == MessageStatus.SENT:
            update_data["sent_at"] = timestamp
        elif status == MessageStatus.DELIVERED:
            update_data["delivered_at"] = timestamp
        elif status == MessageStatus.OPENED:
            update_data["opened_at"] = timestamp
        elif status == MessageStatus.CLICKED:
            update_data["clicked_at"] = timestamp
        elif status == MessageStatus.BOUNCED:
            update_data["bounced_at"] = timestamp

        if error_message:
            update_data["error_message"] = error_message

        await self.db.execute(
            update(CampaignMessage)
            .where(CampaignMessage.id == message_id)
            .values(**update_data)
        )

        await self.db.commit()

        logger.info("Message status updated", message_id=str(message_id), status=status.value)
