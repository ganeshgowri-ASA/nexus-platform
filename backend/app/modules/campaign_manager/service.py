"""
Campaign Manager service layer.

This module contains business logic for campaign management operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.campaign import (
    Campaign,
    CampaignChannel,
    CampaignAsset,
    TeamMember,
    Milestone,
    PerformanceMetric,
    CampaignReport,
    CampaignStatus,
    MilestoneStatus,
)
from app.models.user import User
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignChannelCreate,
    CampaignAssetCreate,
    TeamMemberCreate,
    MilestoneCreate,
    PerformanceMetricCreate,
    CampaignReportCreate,
)
from app.core.exceptions import (
    ResourceNotFoundError,
    BudgetExceededError,
    InvalidStatusTransitionError,
    AuthorizationError,
)


class CampaignService:
    """Service for campaign operations."""

    @staticmethod
    def create_campaign(
        db: Session,
        campaign_data: CampaignCreate,
        owner_id: int
    ) -> Campaign:
        """
        Create a new campaign.

        Args:
            db: Database session
            campaign_data: Campaign creation data
            owner_id: ID of campaign owner

        Returns:
            Campaign: Created campaign
        """
        campaign = Campaign(
            **campaign_data.model_dump(),
            owner_id=owner_id,
            status=CampaignStatus.DRAFT
        )

        db.add(campaign)
        db.commit()
        db.refresh(campaign)

        return campaign

    @staticmethod
    def get_campaign(
        db: Session,
        campaign_id: int,
        user: Optional[User] = None
    ) -> Campaign:
        """
        Get campaign by ID.

        Args:
            db: Database session
            campaign_id: Campaign ID
            user: Optional user for permission check

        Returns:
            Campaign: Campaign instance

        Raises:
            ResourceNotFoundError: If campaign not found
            AuthorizationError: If user lacks permission
        """
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.is_deleted == False
        ).first()

        if not campaign:
            raise ResourceNotFoundError("Campaign", campaign_id)

        # Check permissions if user provided
        if user and not user.can_manage_campaign(campaign):
            if user.role.value != "admin":
                raise AuthorizationError("You don't have access to this campaign")

        return campaign

    @staticmethod
    def list_campaigns(
        db: Session,
        user: User,
        skip: int = 0,
        limit: int = 100,
        status: Optional[CampaignStatus] = None
    ) -> tuple[List[Campaign], int]:
        """
        List campaigns accessible to user.

        Args:
            db: Database session
            user: Current user
            skip: Number of records to skip
            limit: Maximum records to return
            status: Optional status filter

        Returns:
            tuple: (campaigns list, total count)
        """
        query = db.query(Campaign).filter(Campaign.is_deleted == False)

        # Apply filters
        if status:
            query = query.filter(Campaign.status == status)

        # Apply permissions
        if user.role.value != "admin":
            # Show only campaigns user owns or is a member of
            query = query.outerjoin(TeamMember).filter(
                or_(
                    Campaign.owner_id == user.id,
                    TeamMember.user_id == user.id
                )
            )

        total = query.count()
        campaigns = query.order_by(desc(Campaign.created_at)).offset(skip).limit(limit).all()

        return campaigns, total

    @staticmethod
    def update_campaign(
        db: Session,
        campaign_id: int,
        campaign_data: CampaignUpdate,
        user: User
    ) -> Campaign:
        """
        Update campaign.

        Args:
            db: Database session
            campaign_id: Campaign ID
            campaign_data: Update data
            user: Current user

        Returns:
            Campaign: Updated campaign
        """
        campaign = CampaignService.get_campaign(db, campaign_id, user)

        # Check if user can manage
        if not user.can_manage_campaign(campaign):
            raise AuthorizationError("You cannot modify this campaign")

        # Update fields
        update_data = campaign_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)

        db.commit()
        db.refresh(campaign)

        return campaign

    @staticmethod
    def delete_campaign(
        db: Session,
        campaign_id: int,
        user: User
    ) -> None:
        """Soft delete campaign."""
        campaign = CampaignService.get_campaign(db, campaign_id, user)

        if not user.can_manage_campaign(campaign):
            raise AuthorizationError("You cannot delete this campaign")

        campaign.soft_delete()
        db.commit()

    @staticmethod
    def update_campaign_status(
        db: Session,
        campaign_id: int,
        new_status: CampaignStatus,
        user: User
    ) -> Campaign:
        """
        Update campaign status with validation.

        Args:
            db: Database session
            campaign_id: Campaign ID
            new_status: New status
            user: Current user

        Returns:
            Campaign: Updated campaign
        """
        campaign = CampaignService.get_campaign(db, campaign_id, user)

        # Validate status transition
        valid_transitions = {
            CampaignStatus.DRAFT: [CampaignStatus.PLANNED, CampaignStatus.CANCELLED],
            CampaignStatus.PLANNED: [CampaignStatus.ACTIVE, CampaignStatus.CANCELLED],
            CampaignStatus.ACTIVE: [CampaignStatus.PAUSED, CampaignStatus.COMPLETED, CampaignStatus.CANCELLED],
            CampaignStatus.PAUSED: [CampaignStatus.ACTIVE, CampaignStatus.CANCELLED],
        }

        if new_status not in valid_transitions.get(campaign.status, []):
            raise InvalidStatusTransitionError(campaign.status.value, new_status.value)

        campaign.status = new_status
        db.commit()
        db.refresh(campaign)

        return campaign


class ChannelService:
    """Service for campaign channel operations."""

    @staticmethod
    def add_channel(
        db: Session,
        campaign_id: int,
        channel_data: CampaignChannelCreate,
        user: User
    ) -> CampaignChannel:
        """Add channel to campaign."""
        campaign = CampaignService.get_campaign(db, campaign_id, user)

        # Validate budget allocation
        total_allocated = db.query(CampaignChannel).filter(
            CampaignChannel.campaign_id == campaign_id
        ).with_entities(
            db.func.sum(CampaignChannel.allocated_budget)
        ).scalar() or 0.0

        if total_allocated + channel_data.allocated_budget > campaign.total_budget:
            raise BudgetExceededError(
                campaign.total_budget - total_allocated,
                channel_data.allocated_budget
            )

        channel = CampaignChannel(
            campaign_id=campaign_id,
            **channel_data.model_dump()
        )

        db.add(channel)
        db.commit()
        db.refresh(channel)

        return channel

    @staticmethod
    def update_channel_metrics(
        db: Session,
        channel_id: int,
        impressions: int = 0,
        clicks: int = 0,
        conversions: int = 0,
        revenue: float = 0.0,
        cost: float = 0.0
    ) -> CampaignChannel:
        """Update channel performance metrics."""
        channel = db.query(CampaignChannel).filter(
            CampaignChannel.id == channel_id
        ).first()

        if not channel:
            raise ResourceNotFoundError("Channel", channel_id)

        channel.impressions += impressions
        channel.clicks += clicks
        channel.conversions += conversions
        channel.revenue += revenue
        channel.spent_budget += cost

        db.commit()
        db.refresh(channel)

        return channel


class AssetService:
    """Service for campaign asset operations."""

    @staticmethod
    def add_asset(
        db: Session,
        campaign_id: int,
        asset_data: CampaignAssetCreate,
        user: User
    ) -> CampaignAsset:
        """Add asset to campaign."""
        campaign = CampaignService.get_campaign(db, campaign_id, user)

        asset = CampaignAsset(
            campaign_id=campaign_id,
            **asset_data.model_dump()
        )

        db.add(asset)
        db.commit()
        db.refresh(asset)

        return asset

    @staticmethod
    def approve_asset(
        db: Session,
        asset_id: int,
        user: User
    ) -> CampaignAsset:
        """Approve campaign asset."""
        asset = db.query(CampaignAsset).filter(
            CampaignAsset.id == asset_id
        ).first()

        if not asset:
            raise ResourceNotFoundError("Asset", asset_id)

        asset.is_approved = True
        asset.approved_by_id = user.id
        asset.approved_at = datetime.utcnow()

        db.commit()
        db.refresh(asset)

        return asset


class TeamService:
    """Service for team collaboration operations."""

    @staticmethod
    def add_team_member(
        db: Session,
        campaign_id: int,
        member_data: TeamMemberCreate,
        user: User
    ) -> TeamMember:
        """Add team member to campaign."""
        campaign = CampaignService.get_campaign(db, campaign_id, user)

        if not user.can_manage_campaign(campaign):
            raise AuthorizationError("You cannot add team members to this campaign")

        # Check if user already in team
        existing = db.query(TeamMember).filter(
            TeamMember.campaign_id == campaign_id,
            TeamMember.user_id == member_data.user_id
        ).first()

        if existing:
            raise ValueError("User is already a team member")

        member = TeamMember(
            campaign_id=campaign_id,
            **member_data.model_dump()
        )

        db.add(member)
        db.commit()
        db.refresh(member)

        return member

    @staticmethod
    def remove_team_member(
        db: Session,
        campaign_id: int,
        user_id: int,
        current_user: User
    ) -> None:
        """Remove team member from campaign."""
        campaign = CampaignService.get_campaign(db, campaign_id, current_user)

        if not current_user.can_manage_campaign(campaign):
            raise AuthorizationError("You cannot remove team members")

        member = db.query(TeamMember).filter(
            TeamMember.campaign_id == campaign_id,
            TeamMember.user_id == user_id
        ).first()

        if member:
            db.delete(member)
            db.commit()


class MilestoneService:
    """Service for timeline and milestone operations."""

    @staticmethod
    def create_milestone(
        db: Session,
        campaign_id: int,
        milestone_data: MilestoneCreate,
        user: User
    ) -> Milestone:
        """Create campaign milestone."""
        campaign = CampaignService.get_campaign(db, campaign_id, user)

        milestone = Milestone(
            campaign_id=campaign_id,
            **milestone_data.model_dump()
        )

        db.add(milestone)
        db.commit()
        db.refresh(milestone)

        return milestone

    @staticmethod
    def update_milestone_progress(
        db: Session,
        milestone_id: int,
        progress_percentage: int,
        status: Optional[MilestoneStatus] = None
    ) -> Milestone:
        """Update milestone progress."""
        milestone = db.query(Milestone).filter(
            Milestone.id == milestone_id
        ).first()

        if not milestone:
            raise ResourceNotFoundError("Milestone", milestone_id)

        milestone.progress_percentage = progress_percentage

        if status:
            milestone.status = status

        if progress_percentage == 100 and not milestone.completed_at:
            milestone.completed_at = datetime.utcnow()
            milestone.status = MilestoneStatus.COMPLETED

        db.commit()
        db.refresh(milestone)

        return milestone


class AnalyticsService:
    """Service for performance analytics."""

    @staticmethod
    def record_performance(
        db: Session,
        campaign_id: int,
        metric_data: PerformanceMetricCreate
    ) -> PerformanceMetric:
        """Record performance metrics."""
        metric = PerformanceMetric(
            campaign_id=campaign_id,
            **metric_data.model_dump()
        )

        db.add(metric)
        db.commit()
        db.refresh(metric)

        return metric

    @staticmethod
    def calculate_campaign_roi(
        db: Session,
        campaign_id: int
    ) -> Dict[str, float]:
        """Calculate campaign ROI and key metrics."""
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id
        ).first()

        if not campaign:
            raise ResourceNotFoundError("Campaign", campaign_id)

        # Aggregate channel metrics
        total_revenue = 0.0
        total_cost = campaign.spent_budget
        total_impressions = 0
        total_clicks = 0
        total_conversions = 0

        for channel in campaign.channels:
            total_revenue += channel.revenue
            total_impressions += channel.impressions
            total_clicks += channel.clicks
            total_conversions += channel.conversions

        # Calculate metrics
        roi = ((total_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0.0
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0
        conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0.0

        return {
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "roi": roi,
            "ctr": ctr,
            "conversion_rate": conversion_rate,
        }

    @staticmethod
    def get_dashboard_stats(
        db: Session,
        user: User
    ) -> Dict[str, Any]:
        """Get dashboard statistics."""
        # Base query for user's campaigns
        query = db.query(Campaign).filter(Campaign.is_deleted == False)

        if user.role.value != "admin":
            query = query.outerjoin(TeamMember).filter(
                or_(
                    Campaign.owner_id == user.id,
                    TeamMember.user_id == user.id
                )
            )

        total_campaigns = query.count()
        active_campaigns = query.filter(
            Campaign.status == CampaignStatus.ACTIVE
        ).count()

        # Aggregate budgets
        campaigns = query.all()
        total_budget = sum(c.total_budget for c in campaigns)
        spent_budget = sum(c.spent_budget for c in campaigns)

        # Calculate average ROI
        rois = []
        for campaign in campaigns:
            metrics = AnalyticsService.calculate_campaign_roi(db, campaign.id)
            rois.append(metrics["roi"])

        average_roi = sum(rois) / len(rois) if rois else 0.0

        return {
            "total_campaigns": total_campaigns,
            "active_campaigns": active_campaigns,
            "total_budget": total_budget,
            "spent_budget": spent_budget,
            "average_roi": average_roi,
        }
