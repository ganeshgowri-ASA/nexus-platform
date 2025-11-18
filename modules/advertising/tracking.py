"""Conversion tracking and pixel management."""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .models import AdPerformance
from shared.utils import generate_uuid
from config.logging_config import get_logger

logger = get_logger(__name__)


class ConversionTracker:
    """Conversion tracking service."""

    def __init__(self, db: Session):
        self.db = db

    async def track_conversion(
        self,
        campaign_id: Optional[str] = None,
        ad_id: Optional[str] = None,
        conversion_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Track a conversion event."""
        try:
            perf = AdPerformance(
                id=generate_uuid(),
                campaign_id=campaign_id,
                ad_id=ad_id,
                date=datetime.utcnow(),
                conversions=1,
                revenue=conversion_value,
            )

            self.db.add(perf)
            self.db.commit()

            logger.info(f"Conversion tracked: campaign={campaign_id}, value={conversion_value}")

            return True
        except Exception as e:
            logger.error(f"Error tracking conversion: {e}")
            return False

    def generate_pixel_code(self, campaign_id: str) -> str:
        """Generate tracking pixel code."""
        return f"""
        <script>
          (function() {{
            var pixel = new Image();
            pixel.src = 'https://nexus.com/track?campaign_id={campaign_id}&event=page_view';
          }})();
        </script>
        """

    def generate_utm_url(
        self,
        url: str,
        source: str,
        medium: str,
        campaign: str,
        content: Optional[str] = None,
    ) -> str:
        """Generate URL with UTM parameters."""
        utm = f"{url}?utm_source={source}&utm_medium={medium}&utm_campaign={campaign}"
        if content:
            utm += f"&utm_content={content}"
        return utm
