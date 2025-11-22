"""
Social Media Module - Social Advertising Management.

This module provides social ad creation, targeting,
budget management, and performance tracking.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .social_types import Advertisement, AdStatus, PlatformType

logger = logging.getLogger(__name__)


class AdManager:
    """Social media advertising manager."""

    def __init__(self):
        """Initialize ad manager."""
        self._ads: Dict[UUID, Advertisement] = {}

    def create_ad(
        self,
        campaign_id: UUID,
        platform: PlatformType,
        name: str,
        ad_type: str,
        content: Dict[str, Any],
        targeting: Dict[str, Any],
        budget_daily: float = 0.0,
        budget_total: float = 0.0,
    ) -> Advertisement:
        """Create a new advertisement."""
        ad = Advertisement(
            id=uuid4(),
            campaign_id=campaign_id,
            platform=platform,
            name=name,
            ad_type=ad_type,
            status=AdStatus.DRAFT,
            content=content,
            targeting=targeting,
            budget_daily=budget_daily,
            budget_total=budget_total,
            created_at=datetime.utcnow(),
        )

        self._ads[ad.id] = ad
        logger.info(f"Created ad: {name} for platform {platform.value}")
        return ad

    def update_ad_status(
        self, ad_id: UUID, status: AdStatus
    ) -> Advertisement:
        """Update ad status."""
        if ad_id not in self._ads:
            raise ValueError(f"Ad {ad_id} not found")

        ad = self._ads[ad_id]
        ad.status = status
        ad.updated_at = datetime.utcnow()

        logger.info(f"Updated ad {ad_id} status to {status.value}")
        return ad

    def get_ads(
        self,
        campaign_id: Optional[UUID] = None,
        platform: Optional[PlatformType] = None,
        status: Optional[AdStatus] = None,
    ) -> List[Advertisement]:
        """Get filtered list of ads."""
        ads = list(self._ads.values())

        if campaign_id:
            ads = [a for a in ads if a.campaign_id == campaign_id]
        if platform:
            ads = [a for a in ads if a.platform == platform]
        if status:
            ads = [a for a in ads if a.status == status]

        return ads
