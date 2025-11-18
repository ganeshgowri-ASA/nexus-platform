"""Audience targeting capabilities."""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from .models import Audience
from .ad_types import Audience as AudienceType, AudienceCreate
from shared.utils import generate_uuid
from shared.exceptions import ValidationError, NotFoundError
from config.logging_config import get_logger

logger = get_logger(__name__)


class AudienceTargeting:
    """Audience targeting service."""

    def __init__(self, db: Session):
        self.db = db

    async def create_audience(self, audience_data: AudienceCreate) -> AudienceType:
        """Create a new audience."""
        audience = Audience(
            id=generate_uuid(),
            name=audience_data.name,
            platform=audience_data.platform.value,
            targeting_criteria=audience_data.targeting_criteria,
            size_estimate=audience_data.size_estimate,
        )

        self.db.add(audience)
        self.db.commit()
        self.db.refresh(audience)

        logger.info(f"Audience created: {audience.name}")

        return AudienceType.model_validate(audience)

    async def get_demographic_targeting(
        self,
        age_range: Optional[tuple[int, int]] = None,
        gender: Optional[str] = None,
        locations: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Build demographic targeting criteria."""
        criteria = {}

        if age_range:
            criteria["age_min"], criteria["age_max"] = age_range
        if gender:
            criteria["gender"] = gender
        if locations:
            criteria["locations"] = locations
        if languages:
            criteria["languages"] = languages

        return criteria

    async def get_interest_targeting(
        self,
        interests: List[str],
        behaviors: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Build interest and behavior targeting."""
        criteria = {"interests": interests}
        if behaviors:
            criteria["behaviors"] = behaviors
        return criteria

    async def create_lookalike_audience(
        self,
        source_audience_id: str,
        size_percentage: int = 1,
    ) -> AudienceType:
        """Create lookalike audience from source."""
        source = self.db.query(Audience).filter(Audience.id == source_audience_id).first()
        if not source:
            raise NotFoundError(f"Source audience not found: {source_audience_id}")

        lookalike = Audience(
            id=generate_uuid(),
            name=f"{source.name} - Lookalike {size_percentage}%",
            platform=source.platform,
            targeting_criteria={
                "type": "lookalike",
                "source_id": source_audience_id,
                "size_percentage": size_percentage,
            },
        )

        self.db.add(lookalike)
        self.db.commit()
        self.db.refresh(lookalike)

        logger.info(f"Lookalike audience created from {source.name}")

        return AudienceType.model_validate(lookalike)
