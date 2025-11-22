"""
Social Media Module - Campaign Management.

This module provides campaign organization, performance tracking,
A/B testing, and budget allocation features.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .social_types import Campaign, CampaignStatus, PlatformType, Post

logger = logging.getLogger(__name__)


class CampaignError(Exception):
    """Base exception for campaign errors."""

    pass


class CampaignManager:
    """Campaign management and tracking system."""

    def __init__(self):
        """Initialize campaign manager."""
        self._campaigns: Dict[UUID, Campaign] = {}
        self._campaign_posts: Dict[UUID, List[UUID]] = {}  # campaign_id -> [post_ids]

    def create_campaign(
        self,
        name: str,
        owner_id: UUID,
        platforms: List[PlatformType],
        description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        budget: float = 0.0,
        goals: Optional[Dict[str, Any]] = None,
        target_audience: Optional[Dict[str, Any]] = None,
        color_code: str = "#3B82F6",
    ) -> Campaign:
        """
        Create a new campaign.

        Args:
            name: Campaign name
            owner_id: Campaign owner UUID
            platforms: Target platforms
            description: Optional description
            start_date: Campaign start date
            end_date: Campaign end date
            budget: Campaign budget
            goals: Campaign goals (impressions, engagement, conversions, etc.)
            target_audience: Target audience definition
            color_code: Color for calendar visualization

        Returns:
            Campaign object
        """
        campaign = Campaign(
            id=uuid4(),
            name=name,
            description=description,
            status=CampaignStatus.DRAFT,
            start_date=start_date,
            end_date=end_date,
            platforms=platforms,
            budget=budget,
            spent=0.0,
            goals=goals or {},
            target_audience=target_audience or {},
            color_code=color_code,
            owner_id=owner_id,
            team_members=[],
            performance_metrics={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self._campaigns[campaign.id] = campaign
        self._campaign_posts[campaign.id] = []

        logger.info(f"Created campaign {campaign.id}: {name}")
        return campaign

    def update_campaign(
        self,
        campaign_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[CampaignStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        budget: Optional[float] = None,
        goals: Optional[Dict[str, Any]] = None,
        target_audience: Optional[Dict[str, Any]] = None,
        color_code: Optional[str] = None,
    ) -> Campaign:
        """
        Update campaign details.

        Args:
            campaign_id: Campaign UUID
            name: New name
            description: New description
            status: New status
            start_date: New start date
            end_date: New end date
            budget: New budget
            goals: New goals
            target_audience: New target audience
            color_code: New color code

        Returns:
            Updated Campaign object

        Raises:
            ValueError: If campaign not found
        """
        if campaign_id not in self._campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")

        campaign = self._campaigns[campaign_id]

        if name is not None:
            campaign.name = name
        if description is not None:
            campaign.description = description
        if status is not None:
            campaign.status = status
        if start_date is not None:
            campaign.start_date = start_date
        if end_date is not None:
            campaign.end_date = end_date
        if budget is not None:
            campaign.budget = budget
        if goals is not None:
            campaign.goals.update(goals)
        if target_audience is not None:
            campaign.target_audience.update(target_audience)
        if color_code is not None:
            campaign.color_code = color_code

        campaign.updated_at = datetime.utcnow()

        logger.info(f"Updated campaign {campaign_id}")
        return campaign

    def add_post_to_campaign(self, campaign_id: UUID, post_id: UUID) -> None:
        """
        Add a post to a campaign.

        Args:
            campaign_id: Campaign UUID
            post_id: Post UUID

        Raises:
            ValueError: If campaign not found
        """
        if campaign_id not in self._campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign_id not in self._campaign_posts:
            self._campaign_posts[campaign_id] = []

        if post_id not in self._campaign_posts[campaign_id]:
            self._campaign_posts[campaign_id].append(post_id)
            logger.info(f"Added post {post_id} to campaign {campaign_id}")

    def remove_post_from_campaign(self, campaign_id: UUID, post_id: UUID) -> bool:
        """
        Remove a post from a campaign.

        Args:
            campaign_id: Campaign UUID
            post_id: Post UUID to remove

        Returns:
            True if removed, False if not found
        """
        if campaign_id in self._campaign_posts:
            if post_id in self._campaign_posts[campaign_id]:
                self._campaign_posts[campaign_id].remove(post_id)
                logger.info(f"Removed post {post_id} from campaign {campaign_id}")
                return True
        return False

    def get_campaign_posts(self, campaign_id: UUID) -> List[UUID]:
        """
        Get all posts in a campaign.

        Args:
            campaign_id: Campaign UUID

        Returns:
            List of post UUIDs
        """
        return self._campaign_posts.get(campaign_id, [])

    def update_campaign_metrics(
        self,
        campaign_id: UUID,
        metrics: Dict[str, Any],
        add_spent: Optional[float] = None,
    ) -> Campaign:
        """
        Update campaign performance metrics.

        Args:
            campaign_id: Campaign UUID
            metrics: Performance metrics to update
            add_spent: Amount to add to spent budget

        Returns:
            Updated Campaign object

        Raises:
            ValueError: If campaign not found
        """
        if campaign_id not in self._campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")

        campaign = self._campaigns[campaign_id]
        campaign.performance_metrics.update(metrics)

        if add_spent is not None:
            campaign.spent += add_spent

        campaign.updated_at = datetime.utcnow()

        logger.info(f"Updated metrics for campaign {campaign_id}")
        return campaign

    def get_campaign(self, campaign_id: UUID) -> Optional[Campaign]:
        """
        Get a campaign by ID.

        Args:
            campaign_id: Campaign UUID

        Returns:
            Campaign object or None
        """
        return self._campaigns.get(campaign_id)

    def list_campaigns(
        self,
        status: Optional[CampaignStatus] = None,
        platform: Optional[PlatformType] = None,
        owner_id: Optional[UUID] = None,
    ) -> List[Campaign]:
        """
        List campaigns with optional filters.

        Args:
            status: Filter by status
            platform: Filter by platform
            owner_id: Filter by owner

        Returns:
            List of Campaign objects
        """
        campaigns = list(self._campaigns.values())

        if status:
            campaigns = [c for c in campaigns if c.status == status]
        if platform:
            campaigns = [c for c in campaigns if platform in c.platforms]
        if owner_id:
            campaigns = [c for c in campaigns if c.owner_id == owner_id]

        campaigns.sort(key=lambda c: c.created_at, reverse=True)
        return campaigns

    def add_team_member(self, campaign_id: UUID, user_id: UUID) -> Campaign:
        """
        Add a team member to a campaign.

        Args:
            campaign_id: Campaign UUID
            user_id: User UUID to add

        Returns:
            Updated Campaign object

        Raises:
            ValueError: If campaign not found
        """
        if campaign_id not in self._campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")

        campaign = self._campaigns[campaign_id]
        if user_id not in campaign.team_members:
            campaign.team_members.append(user_id)
            campaign.updated_at = datetime.utcnow()
            logger.info(f"Added team member {user_id} to campaign {campaign_id}")

        return campaign

    def remove_team_member(self, campaign_id: UUID, user_id: UUID) -> bool:
        """
        Remove a team member from a campaign.

        Args:
            campaign_id: Campaign UUID
            user_id: User UUID to remove

        Returns:
            True if removed, False if not found
        """
        if campaign_id in self._campaigns:
            campaign = self._campaigns[campaign_id]
            if user_id in campaign.team_members:
                campaign.team_members.remove(user_id)
                campaign.updated_at = datetime.utcnow()
                logger.info(f"Removed team member {user_id} from campaign {campaign_id}")
                return True
        return False

    def calculate_campaign_roi(self, campaign_id: UUID) -> Dict[str, Any]:
        """
        Calculate ROI for a campaign.

        Args:
            campaign_id: Campaign UUID

        Returns:
            ROI calculation dictionary

        Raises:
            ValueError: If campaign not found
        """
        if campaign_id not in self._campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")

        campaign = self._campaigns[campaign_id]
        metrics = campaign.performance_metrics

        total_revenue = metrics.get("revenue", 0.0)
        total_cost = campaign.spent
        total_conversions = metrics.get("conversions", 0)
        total_engagement = metrics.get("engagement", 0)
        total_reach = metrics.get("reach", 0)

        # Calculate ROI
        roi = ((total_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0.0

        # Calculate other rates
        conversion_rate = (
            (total_conversions / total_reach * 100) if total_reach > 0 else 0.0
        )
        engagement_rate = (
            (total_engagement / total_reach * 100) if total_reach > 0 else 0.0
        )

        # Cost per metrics
        cost_per_conversion = (
            total_cost / total_conversions if total_conversions > 0 else 0.0
        )
        cost_per_engagement = (
            total_cost / total_engagement if total_engagement > 0 else 0.0
        )

        # Budget utilization
        budget_used_percentage = (
            (total_cost / campaign.budget * 100) if campaign.budget > 0 else 0.0
        )

        return {
            "campaign_id": str(campaign_id),
            "campaign_name": campaign.name,
            "budget": campaign.budget,
            "spent": total_cost,
            "revenue": total_revenue,
            "roi": round(roi, 2),
            "budget_used_percentage": round(budget_used_percentage, 2),
            "conversions": total_conversions,
            "conversion_rate": round(conversion_rate, 2),
            "engagement_rate": round(engagement_rate, 2),
            "cost_per_conversion": round(cost_per_conversion, 2),
            "cost_per_engagement": round(cost_per_engagement, 4),
        }

    def compare_campaigns(
        self, campaign_ids: List[UUID], metric: str = "roi"
    ) -> Dict[str, Any]:
        """
        Compare multiple campaigns.

        Args:
            campaign_ids: List of campaign UUIDs to compare
            metric: Metric to compare (roi, engagement, conversions, etc.)

        Returns:
            Comparison data dictionary
        """
        comparisons = []

        for campaign_id in campaign_ids:
            if campaign_id not in self._campaigns:
                continue

            campaign = self._campaigns[campaign_id]
            roi_data = self.calculate_campaign_roi(campaign_id)

            comparisons.append(
                {
                    "campaign_id": str(campaign_id),
                    "name": campaign.name,
                    "status": campaign.status.value,
                    "platforms": [p.value for p in campaign.platforms],
                    "roi": roi_data["roi"],
                    "spent": roi_data["spent"],
                    "revenue": roi_data["revenue"],
                    "conversions": roi_data["conversions"],
                    "engagement_rate": roi_data["engagement_rate"],
                    "post_count": len(self._campaign_posts.get(campaign_id, [])),
                }
            )

        # Sort by specified metric
        if metric in ["roi", "spent", "revenue", "conversions", "engagement_rate"]:
            comparisons.sort(key=lambda x: x[metric], reverse=True)

        return {
            "campaigns": comparisons,
            "best_performer": comparisons[0] if comparisons else None,
            "comparison_metric": metric,
        }

    def get_active_campaigns(self) -> List[Campaign]:
        """
        Get all active campaigns.

        Returns:
            List of active Campaign objects
        """
        now = datetime.utcnow()
        active = []

        for campaign in self._campaigns.values():
            if campaign.status == CampaignStatus.ACTIVE:
                # Check date range
                if campaign.start_date and campaign.start_date > now:
                    continue
                if campaign.end_date and campaign.end_date < now:
                    continue
                active.append(campaign)

        return active

    def archive_campaign(self, campaign_id: UUID) -> Campaign:
        """
        Archive a campaign.

        Args:
            campaign_id: Campaign UUID

        Returns:
            Updated Campaign object

        Raises:
            ValueError: If campaign not found
        """
        if campaign_id not in self._campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")

        campaign = self._campaigns[campaign_id]
        campaign.status = CampaignStatus.ARCHIVED
        campaign.updated_at = datetime.utcnow()

        logger.info(f"Archived campaign {campaign_id}")
        return campaign

    def get_campaign_summary(self, campaign_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive campaign summary.

        Args:
            campaign_id: Campaign UUID

        Returns:
            Campaign summary dictionary

        Raises:
            ValueError: If campaign not found
        """
        if campaign_id not in self._campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")

        campaign = self._campaigns[campaign_id]
        roi_data = self.calculate_campaign_roi(campaign_id)
        post_ids = self._campaign_posts.get(campaign_id, [])

        # Calculate progress
        progress = 0.0
        if campaign.start_date and campaign.end_date:
            total_duration = (campaign.end_date - campaign.start_date).total_seconds()
            if total_duration > 0:
                elapsed = (datetime.utcnow() - campaign.start_date).total_seconds()
                progress = min(100.0, (elapsed / total_duration) * 100)

        # Check goal progress
        goal_progress = {}
        for goal_name, goal_target in campaign.goals.items():
            actual_value = campaign.performance_metrics.get(goal_name, 0)
            if isinstance(goal_target, (int, float)) and goal_target > 0:
                goal_progress[goal_name] = {
                    "target": goal_target,
                    "actual": actual_value,
                    "progress": round((actual_value / goal_target * 100), 2),
                }

        return {
            "id": str(campaign.id),
            "name": campaign.name,
            "description": campaign.description,
            "status": campaign.status.value,
            "platforms": [p.value for p in campaign.platforms],
            "dates": {
                "start": campaign.start_date.isoformat() if campaign.start_date else None,
                "end": campaign.end_date.isoformat() if campaign.end_date else None,
                "progress_percentage": round(progress, 2),
            },
            "budget": {
                "allocated": campaign.budget,
                "spent": campaign.spent,
                "remaining": campaign.budget - campaign.spent,
                "utilization_percentage": roi_data["budget_used_percentage"],
            },
            "performance": roi_data,
            "goals": goal_progress,
            "content": {
                "total_posts": len(post_ids),
                "post_ids": [str(pid) for pid in post_ids],
            },
            "team": {
                "owner_id": str(campaign.owner_id),
                "members": [str(m) for m in campaign.team_members],
            },
        }
