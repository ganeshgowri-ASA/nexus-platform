"""
Social Media Module - User-Generated Content Management.

This module provides UGC curation, rights management,
and repost tools.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .social_types import PlatformType

logger = logging.getLogger(__name__)


class UGCManager:
    """User-generated content management."""

    def __init__(self):
        """Initialize UGC manager."""
        self._ugc_items: Dict[UUID, Dict[str, Any]] = {}

    def add_ugc(
        self,
        platform: PlatformType,
        author_username: str,
        content_url: str,
        media_url: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add UGC item for tracking."""
        ugc_id = uuid4()
        ugc_item = {
            "id": ugc_id,
            "platform": platform.value,
            "author_username": author_username,
            "content_url": content_url,
            "media_url": media_url,
            "caption": caption,
            "rights_approved": False,
            "reposted": False,
            "created_at": datetime.utcnow(),
        }

        self._ugc_items[ugc_id] = ugc_item
        logger.info(f"Added UGC from {author_username}")
        return ugc_item

    def approve_rights(self, ugc_id: UUID) -> bool:
        """Approve rights for UGC usage."""
        if ugc_id in self._ugc_items:
            self._ugc_items[ugc_id]["rights_approved"] = True
            self._ugc_items[ugc_id]["rights_approved_at"] = datetime.utcnow()
            return True
        return False

    def mark_reposted(self, ugc_id: UUID, post_id: UUID) -> bool:
        """Mark UGC as reposted."""
        if ugc_id in self._ugc_items:
            self._ugc_items[ugc_id]["reposted"] = True
            self._ugc_items[ugc_id]["repost_post_id"] = str(post_id)
            self._ugc_items[ugc_id]["reposted_at"] = datetime.utcnow()
            return True
        return False
