"""
Social Media Module - Media Library Management.

This module provides asset storage, organization,
image editing, and brand asset management.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .social_types import Media, MediaType

logger = logging.getLogger(__name__)


class MediaLibrary:
    """Media asset management system."""

    def __init__(self, storage_path: str = "/media"):
        """Initialize media library."""
        self.storage_path = storage_path
        self._media_items: Dict[UUID, Media] = {}
        self._folders: Dict[str, List[UUID]] = {"root": []}

    def upload_media(
        self,
        file_path: str,
        media_type: MediaType,
        folder: str = "root",
        alt_text: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Media:
        """Upload media to library."""
        media = Media(
            id=uuid4(),
            media_type=media_type,
            file_path=file_path,
            url=f"{self.storage_path}/{file_path}",
            alt_text=alt_text,
            tags=tags or [],
            created_at=datetime.utcnow(),
        )

        self._media_items[media.id] = media

        if folder not in self._folders:
            self._folders[folder] = []
        self._folders[folder].append(media.id)

        logger.info(f"Uploaded {media_type.value} to library: {file_path}")
        return media

    def get_media(
        self,
        folder: Optional[str] = None,
        media_type: Optional[MediaType] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Media]:
        """Get filtered media items."""
        media_items = list(self._media_items.values())

        if folder:
            folder_ids = self._folders.get(folder, [])
            media_items = [m for m in media_items if m.id in folder_ids]
        if media_type:
            media_items = [m for m in media_items if m.media_type == media_type]
        if tags:
            media_items = [
                m for m in media_items if any(tag in m.tags for tag in tags)
            ]

        return media_items

    def delete_media(self, media_id: UUID) -> bool:
        """Delete media from library."""
        if media_id in self._media_items:
            del self._media_items[media_id]
            # Remove from folders
            for folder_media in self._folders.values():
                if media_id in folder_media:
                    folder_media.remove(media_id)
            return True
        return False
