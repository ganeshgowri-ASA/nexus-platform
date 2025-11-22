"""
File Sharing - Handles file uploads and attachments.

Manages file uploads, image/video processing, file storage,
and file metadata. Supports drag-and-drop, previews, and limits.
"""

import logging
import mimetypes
from typing import Optional, List, Dict, Any, BinaryIO
from datetime import datetime
from uuid import UUID, uuid4
from pathlib import Path

from .models import Attachment, Message

logger = logging.getLogger(__name__)


class FileSharing:
    """
    Manages file sharing and attachments.

    Handles:
    - File uploads
    - File validation (size, type)
    - Image/video thumbnail generation
    - File storage and retrieval
    - File metadata

    Example:
        >>> fs = FileSharing(engine)
        >>> attachment = await fs.upload_file(user_id, file_data, "photo.jpg")
        >>> await fs.attach_to_message(message_id, attachment)
    """

    # File size limits (in bytes)
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
    MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50 MB

    # Allowed file types
    ALLOWED_IMAGE_TYPES = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
    ALLOWED_VIDEO_TYPES = {'.mp4', '.webm', '.mov', '.avi'}
    ALLOWED_AUDIO_TYPES = {'.mp3', '.wav', '.ogg', '.m4a'}
    ALLOWED_DOCUMENT_TYPES = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt'}

    def __init__(self, engine):
        """
        Initialize file sharing manager.

        Args:
            engine: Reference to the ChatEngine
        """
        self.engine = engine
        self._storage_path = Path("./storage/chat_files")
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._attachment_cache: Dict[UUID, Attachment] = {}
        logger.info("FileSharing initialized")

    async def upload_file(
        self,
        user_id: UUID,
        file_data: bytes,
        filename: str,
        content_type: Optional[str] = None
    ) -> Attachment:
        """
        Upload a file.

        Args:
            user_id: ID of the user uploading
            file_data: File binary data
            filename: Original filename
            content_type: MIME type (auto-detected if not provided)

        Returns:
            Created Attachment object

        Raises:
            ValueError: If file is invalid or too large
        """
        # Validate file
        file_ext = Path(filename).suffix.lower()
        file_size = len(file_data)

        # Check file size
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large (max {self.MAX_FILE_SIZE / 1024 / 1024}MB)")

        # Check specific limits for media
        if file_ext in self.ALLOWED_IMAGE_TYPES and file_size > self.MAX_IMAGE_SIZE:
            raise ValueError(f"Image too large (max {self.MAX_IMAGE_SIZE / 1024 / 1024}MB)")

        if file_ext in self.ALLOWED_VIDEO_TYPES and file_size > self.MAX_VIDEO_SIZE:
            raise ValueError(f"Video too large (max {self.MAX_VIDEO_SIZE / 1024 / 1024}MB)")

        # Check allowed types
        if not self._is_allowed_file_type(file_ext):
            raise ValueError(f"File type {file_ext} not allowed")

        # Detect content type
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or 'application/octet-stream'

        # Generate unique file ID
        file_id = uuid4()
        file_path = self._storage_path / str(user_id) / str(file_id)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Save file
        try:
            with open(file_path, 'wb') as f:
                f.write(file_data)
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise ValueError(f"Failed to save file: {e}")

        # Generate thumbnail for images/videos
        thumbnail_url = None
        if file_ext in self.ALLOWED_IMAGE_TYPES:
            thumbnail_url = await self._generate_image_thumbnail(file_path)
        elif file_ext in self.ALLOWED_VIDEO_TYPES:
            thumbnail_url = await self._generate_video_thumbnail(file_path)

        # Create attachment record
        attachment = Attachment(
            id=file_id,
            message_id=uuid4(),  # Temporary, will be updated when attached
            file_name=filename,
            file_type=content_type,
            file_size=file_size,
            file_url=str(file_path),
            thumbnail_url=thumbnail_url,
            uploaded_at=datetime.utcnow(),
            metadata={
                'uploader_id': str(user_id),
                'extension': file_ext
            }
        )

        # Cache attachment
        self._attachment_cache[attachment.id] = attachment

        logger.info(f"File uploaded: {filename} ({file_size} bytes)")
        return attachment

    async def attach_to_message(
        self,
        message_id: UUID,
        attachment_id: UUID
    ) -> bool:
        """
        Attach a file to a message.

        Args:
            message_id: ID of the message
            attachment_id: ID of the attachment

        Returns:
            True if successful
        """
        attachment = self._attachment_cache.get(attachment_id)

        if not attachment:
            raise ValueError(f"Attachment {attachment_id} not found")

        # Update attachment message ID
        attachment.message_id = message_id
        self._attachment_cache[attachment_id] = attachment

        # Update message attachments
        # In production: update message record in database

        logger.info(f"Attachment {attachment_id} linked to message {message_id}")
        return True

    async def get_attachment(self, attachment_id: UUID) -> Optional[Attachment]:
        """
        Get attachment by ID.

        Args:
            attachment_id: ID of the attachment

        Returns:
            Attachment object or None
        """
        return self._attachment_cache.get(attachment_id)

    async def get_message_attachments(
        self,
        message_id: UUID
    ) -> List[Attachment]:
        """
        Get all attachments for a message.

        Args:
            message_id: ID of the message

        Returns:
            List of Attachment objects
        """
        attachments = [
            att for att in self._attachment_cache.values()
            if att.message_id == message_id
        ]

        return attachments

    async def delete_attachment(
        self,
        attachment_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete an attachment.

        Args:
            attachment_id: ID of the attachment
            user_id: ID of the user deleting

        Returns:
            True if successful
        """
        attachment = self._attachment_cache.get(attachment_id)

        if not attachment:
            return False

        # Check permissions (user must own the message)
        # In production: check message ownership

        # Delete file
        try:
            file_path = Path(attachment.file_url)
            if file_path.exists():
                file_path.unlink()

            # Delete thumbnail if exists
            if attachment.thumbnail_url:
                thumb_path = Path(attachment.thumbnail_url)
                if thumb_path.exists():
                    thumb_path.unlink()

        except Exception as e:
            logger.error(f"Error deleting file: {e}")

        # Remove from cache
        self._attachment_cache.pop(attachment_id, None)

        logger.info(f"Attachment {attachment_id} deleted")
        return True

    async def get_file_data(self, attachment_id: UUID) -> Optional[bytes]:
        """
        Get file binary data.

        Args:
            attachment_id: ID of the attachment

        Returns:
            File data bytes or None
        """
        attachment = self._attachment_cache.get(attachment_id)

        if not attachment:
            return None

        try:
            with open(attachment.file_url, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return None

    async def get_channel_files(
        self,
        channel_id: UUID,
        file_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Attachment]:
        """
        Get all files shared in a channel.

        Args:
            channel_id: ID of the channel
            file_type: Filter by file type (image, video, document, etc.)
            limit: Maximum results

        Returns:
            List of Attachment objects
        """
        # In production: query from database
        # SELECT a.* FROM attachments a
        # JOIN messages m ON a.message_id = m.id
        # WHERE m.channel_id = channel_id
        # ORDER BY a.uploaded_at DESC
        # LIMIT limit

        attachments = []

        logger.debug(f"Retrieved {len(attachments)} files from channel {channel_id}")
        return attachments[:limit]

    async def search_files(
        self,
        channel_id: UUID,
        query: str,
        limit: int = 20
    ) -> List[Attachment]:
        """
        Search files by filename.

        Args:
            channel_id: ID of the channel
            query: Search query
            limit: Maximum results

        Returns:
            List of Attachment objects
        """
        # Get channel files
        files = await self.get_channel_files(channel_id, limit=1000)

        # Filter by query
        query_lower = query.lower()
        matches = [
            f for f in files
            if query_lower in f.file_name.lower()
        ]

        return matches[:limit]

    def _is_allowed_file_type(self, extension: str) -> bool:
        """Check if file type is allowed."""
        allowed_types = (
            self.ALLOWED_IMAGE_TYPES |
            self.ALLOWED_VIDEO_TYPES |
            self.ALLOWED_AUDIO_TYPES |
            self.ALLOWED_DOCUMENT_TYPES
        )

        return extension in allowed_types

    async def _generate_image_thumbnail(
        self,
        image_path: Path,
        size: tuple = (200, 200)
    ) -> Optional[str]:
        """
        Generate thumbnail for an image.

        Args:
            image_path: Path to the image file
            size: Thumbnail size (width, height)

        Returns:
            Thumbnail file path or None
        """
        # In production: use PIL/Pillow to generate thumbnail
        # from PIL import Image
        # img = Image.open(image_path)
        # img.thumbnail(size)
        # thumb_path = image_path.with_suffix('.thumb.jpg')
        # img.save(thumb_path)
        # return str(thumb_path)

        logger.debug(f"Thumbnail generation skipped for {image_path}")
        return None

    async def _generate_video_thumbnail(
        self,
        video_path: Path
    ) -> Optional[str]:
        """
        Generate thumbnail for a video.

        Args:
            video_path: Path to the video file

        Returns:
            Thumbnail file path or None
        """
        # In production: use ffmpeg to extract frame
        # ffmpeg -i video.mp4 -ss 00:00:01 -vframes 1 thumb.jpg

        logger.debug(f"Video thumbnail generation skipped for {video_path}")
        return None

    async def get_storage_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get storage statistics for a user.

        Args:
            user_id: ID of the user

        Returns:
            Dictionary with storage stats
        """
        # Calculate total size
        user_attachments = [
            att for att in self._attachment_cache.values()
            if att.metadata.get('uploader_id') == str(user_id)
        ]

        total_size = sum(att.file_size for att in user_attachments)
        total_files = len(user_attachments)

        # Count by type
        by_type = {}
        for att in user_attachments:
            ext = att.metadata.get('extension', 'unknown')
            by_type[ext] = by_type.get(ext, 0) + 1

        return {
            'total_size': total_size,
            'total_files': total_files,
            'by_type': by_type,
            'formatted_size': self._format_bytes(total_size)
        }

    @staticmethod
    def _format_bytes(bytes_size: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"
