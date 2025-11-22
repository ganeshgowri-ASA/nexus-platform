"""
Campaign service for managing advertising campaigns.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.advertising.models import (
    Campaign, AdSet, Ad, CampaignStatus, CampaignPerformance
)
from modules.advertising.schemas import CampaignCreate, CampaignUpdate


class CampaignService:
    """Service for managing campaigns."""

    @staticmethod
    async def create_campaign(
        db: AsyncSession,
        campaign_data: CampaignCreate
    ) -> Campaign:
        """
        Create a new campaign.

        Args:
            db: Database session
            campaign_data: Campaign creation data

        Returns:
            Created campaign
        """
        try:
            campaign = Campaign(**campaign_data.model_dump())
            db.add(campaign)
            await db.commit()
            await db.refresh(campaign)

            logger.info(f"Campaign created: {campaign.id}")
            return campaign
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating campaign: {e}")
            raise

    @staticmethod
    async def get_campaign(db: AsyncSession, campaign_id: UUID) -> Optional[Campaign]:
        """
        Get a campaign by ID.

        Args:
            db: Database session
            campaign_id: Campaign ID

        Returns:
            Campaign or None
        """
        try:
            result = await db.execute(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting campaign: {e}")
            raise

    @staticmethod
    async def list_campaigns(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[CampaignStatus] = None,
        platform: Optional[str] = None
    ) -> List[Campaign]:
        """
        List campaigns with optional filtering.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by status
            platform: Filter by platform

        Returns:
            List of campaigns
        """
        try:
            query = select(Campaign)

            if status:
                query = query.where(Campaign.status == status)

            if platform:
                query = query.where(Campaign.platform == platform)

            query = query.offset(skip).limit(limit).order_by(Campaign.created_at.desc())

            result = await db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error listing campaigns: {e}")
            raise

    @staticmethod
    async def update_campaign(
        db: AsyncSession,
        campaign_id: UUID,
        campaign_data: CampaignUpdate
    ) -> Optional[Campaign]:
        """
        Update a campaign.

        Args:
            db: Database session
            campaign_id: Campaign ID
            campaign_data: Campaign update data

        Returns:
            Updated campaign or None
        """
        try:
            result = await db.execute(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            campaign = result.scalar_one_or_none()

            if not campaign:
                return None

            update_data = campaign_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(campaign, field, value)

            await db.commit()
            await db.refresh(campaign)

            logger.info(f"Campaign updated: {campaign.id}")
            return campaign
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating campaign: {e}")
            raise

    @staticmethod
    async def update_campaign_metrics(
        db: AsyncSession,
        campaign_id: UUID,
        metrics: dict
    ) -> Optional[Campaign]:
        """
        Update campaign performance metrics.

        Args:
            db: Database session
            campaign_id: Campaign ID
            metrics: Performance metrics

        Returns:
            Updated campaign or None
        """
        try:
            result = await db.execute(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            campaign = result.scalar_one_or_none()

            if not campaign:
                return None

            # Update metrics
            campaign.impressions = metrics.get("impressions", campaign.impressions)
            campaign.clicks = metrics.get("clicks", campaign.clicks)
            campaign.conversions = metrics.get("conversions", campaign.conversions)
            campaign.spent = metrics.get("spent", campaign.spent)

            # Calculate derived metrics
            if campaign.impressions > 0:
                campaign.ctr = (campaign.clicks / campaign.impressions) * 100

            if campaign.clicks > 0:
                campaign.cpc = campaign.spent / campaign.clicks

            if campaign.impressions > 0:
                campaign.cpm = (campaign.spent / campaign.impressions) * 1000

            if campaign.conversions > 0:
                campaign.cpa = campaign.spent / campaign.conversions

            if campaign.spent > 0:
                revenue = metrics.get("revenue", 0)
                campaign.roas = revenue / campaign.spent

            campaign.synced_at = datetime.utcnow()

            await db.commit()
            await db.refresh(campaign)

            logger.info(f"Campaign metrics updated: {campaign.id}")
            return campaign
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating campaign metrics: {e}")
            raise

    @staticmethod
    async def pause_campaign(db: AsyncSession, campaign_id: UUID) -> Optional[Campaign]:
        """
        Pause a campaign.

        Args:
            db: Database session
            campaign_id: Campaign ID

        Returns:
            Updated campaign or None
        """
        try:
            result = await db.execute(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            campaign = result.scalar_one_or_none()

            if not campaign:
                return None

            campaign.status = CampaignStatus.PAUSED
            await db.commit()
            await db.refresh(campaign)

            logger.info(f"Campaign paused: {campaign.id}")
            return campaign
        except Exception as e:
            await db.rollback()
            logger.error(f"Error pausing campaign: {e}")
            raise

    @staticmethod
    async def activate_campaign(db: AsyncSession, campaign_id: UUID) -> Optional[Campaign]:
        """
        Activate a campaign.

        Args:
            db: Database session
            campaign_id: Campaign ID

        Returns:
            Updated campaign or None
        """
        try:
            result = await db.execute(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            campaign = result.scalar_one_or_none()

            if not campaign:
                return None

            campaign.status = CampaignStatus.ACTIVE
            await db.commit()
            await db.refresh(campaign)

            logger.info(f"Campaign activated: {campaign.id}")
            return campaign
        except Exception as e:
            await db.rollback()
            logger.error(f"Error activating campaign: {e}")
            raise

    @staticmethod
    async def get_campaign_performance(
        db: AsyncSession,
        campaign_id: UUID,
        days: int = 30
    ) -> List[CampaignPerformance]:
        """
        Get campaign performance history.

        Args:
            db: Database session
            campaign_id: Campaign ID
            days: Number of days to retrieve

        Returns:
            List of performance records
        """
        try:
            cutoff_date = datetime.utcnow().date()

            result = await db.execute(
                select(CampaignPerformance)
                .where(CampaignPerformance.campaign_id == campaign_id)
                .order_by(CampaignPerformance.date.desc())
                .limit(days)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting campaign performance: {e}")
            raise
