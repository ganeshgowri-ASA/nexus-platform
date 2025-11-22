"""Creative management for ads."""

from typing import Optional, List
from sqlalchemy.orm import Session

from .models import Creative as CreativeModel
from .ad_types import Creative, CreativeCreate, AdType
from shared.utils import generate_uuid
from shared.exceptions import ValidationError, NotFoundError
from config.logging_config import get_logger

logger = get_logger(__name__)


class CreativeManager:
    """Creative management service."""

    def __init__(self, db: Session):
        self.db = db

    async def create_creative(self, creative_data: CreativeCreate) -> Creative:
        """Create a new creative."""
        creative = CreativeModel(
            id=generate_uuid(),
            name=creative_data.name,
            type=creative_data.type.value,
            asset_url=creative_data.asset_url,
            thumbnail_url=creative_data.thumbnail_url,
            metadata=creative_data.metadata,
        )

        self.db.add(creative)
        self.db.commit()
        self.db.refresh(creative)

        logger.info(f"Creative created: {creative.name}")

        return Creative.model_validate(creative)

    async def upload_creative_asset(
        self,
        creative_id: str,
        file_path: str,
    ) -> str:
        """Upload creative asset (image/video)."""
        # Implement file upload logic
        # For now, return placeholder URL
        asset_url = f"https://cdn.nexus.com/creatives/{creative_id}"
        
        creative = self.db.query(CreativeModel).filter(
            CreativeModel.id == creative_id
        ).first()
        
        if creative:
            creative.asset_url = asset_url
            self.db.commit()

        logger.info(f"Creative asset uploaded: {creative_id}")

        return asset_url

    async def list_creatives(
        self,
        type: Optional[AdType] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Creative]:
        """List creatives."""
        query = self.db.query(CreativeModel)

        if type:
            query = query.filter(CreativeModel.type == type.value)

        creatives = query.offset(skip).limit(limit).all()

        return [Creative.model_validate(c) for c in creatives]
