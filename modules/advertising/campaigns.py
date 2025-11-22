"""Campaign creation and management."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .ad_types import Campaign, CampaignCreate, CampaignStatus
from .models import Campaign as CampaignModel
from shared.utils import generate_uuid
from shared.exceptions import ValidationError, NotFoundError, DatabaseError
from config.logging_config import get_logger

logger = get_logger(__name__)


class CampaignManager:
    """Campaign management service."""

    def __init__(self, db: Session):
        self.db = db

    async def create_campaign(self, campaign_data: CampaignCreate) -> Campaign:
        """Create a new advertising campaign."""
        try:
            campaign = CampaignModel(
                id=generate_uuid(),
                name=campaign_data.name,
                objective=campaign_data.objective,
                platform=campaign_data.platform.value,
                daily_budget=campaign_data.daily_budget,
                total_budget=campaign_data.total_budget,
                start_date=campaign_data.start_date,
                end_date=campaign_data.end_date,
                status=campaign_data.status.value,
            )

            self.db.add(campaign)
            self.db.commit()
            self.db.refresh(campaign)

            logger.info(f"Campaign created: {campaign.name} (ID: {campaign.id})")

            return Campaign.model_validate(campaign)

        except IntegrityError:
            self.db.rollback()
            raise ValidationError(f"Campaign with name '{campaign_data.name}' already exists")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating campaign: {e}")
            raise DatabaseError(f"Failed to create campaign: {str(e)}")

    async def get_campaign(self, campaign_id: str) -> Campaign:
        """Get campaign by ID."""
        campaign = self.db.query(CampaignModel).filter(
            CampaignModel.id == campaign_id
        ).first()
        if not campaign:
            raise NotFoundError(f"Campaign not found: {campaign_id}")

        return Campaign.model_validate(campaign)

    async def list_campaigns(
        self,
        status: Optional[CampaignStatus] = None,
        platform: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Campaign]:
        """List campaigns with filters."""
        query = self.db.query(CampaignModel)

        if status:
            query = query.filter(CampaignModel.status == status.value)
        if platform:
            query = query.filter(CampaignModel.platform == platform)

        campaigns = query.order_by(
            CampaignModel.created_at.desc()
        ).offset(skip).limit(limit).all()

        return [Campaign.model_validate(c) for c in campaigns]

    async def update_campaign_status(
        self,
        campaign_id: str,
        status: CampaignStatus,
    ) -> Campaign:
        """Update campaign status."""
        campaign = self.db.query(CampaignModel).filter(
            CampaignModel.id == campaign_id
        ).first()
        if not campaign:
            raise NotFoundError(f"Campaign not found: {campaign_id}")

        campaign.status = status.value
        self.db.commit()
        self.db.refresh(campaign)

        logger.info(f"Campaign status updated: {campaign.name} -> {status.value}")

        return Campaign.model_validate(campaign)

    async def update_campaign_metrics(
        self,
        campaign_id: str,
        impressions: int,
        clicks: int,
        conversions: int,
        spend: float,
    ) -> None:
        """Update campaign performance metrics."""
        campaign = self.db.query(CampaignModel).filter(
            CampaignModel.id == campaign_id
        ).first()
        if campaign:
            campaign.impressions += impressions
            campaign.clicks += clicks
            campaign.conversions += conversions
            campaign.spend += spend
            self.db.commit()
