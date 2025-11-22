"""
Wiki Attachments Service

File attachment management including upload, download, versioning, image optimization,
thumbnail generation, and storage management for wiki pages.

Author: NEXUS Platform Team
"""

import os
import re
import hashlib
import mimetypes
from io import BytesIO
from typing import Dict, List, Optional, Any, Tuple, BinaryIO
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.utils import get_logger
from modules.wiki.models import WikiPage, WikiAttachment
from modules.wiki.wiki_types import AttachmentType

logger = get_logger(__name__)


class AttachmentService:
    """Manages file attachments for wiki pages."""

    # Maximum file sizes (in bytes)
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

    # Allowed file types
    ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'}
    ALLOWED_VIDEO_TYPES = {'video/mp4', 'video/webm', 'video/ogg'}
    ALLOWED_AUDIO_TYPES = {'audio/mpeg', 'audio/ogg', 'audio/wav'}
    ALLOWED_DOCUMENT_TYPES = {
        'application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain', 'text/csv'
    }

    def __init__(self, db: Session, storage_path: str = '/var/nexus/wiki/attachments'):
        """
        Initialize AttachmentService.

        Args:
            db: SQLAlchemy database session
            storage_path: Base path for file storage
        """
        self.db = db
        self.storage_path = Path(storage_path)
        self._ensure_storage_directory()

    def upload_attachment(
        self,
        page_id: int,
        file_data: BinaryIO,
        filename: str,
        user_id: int,
        description: Optional[str] = None
    ) -> Optional[WikiAttachment]:
        """
        Upload a file attachment to a wiki page.

        Args:
            page_id: ID of the page to attach file to
            file_data: File binary data
            filename: Original filename
            user_id: ID of user uploading the file
            description: Optional description of the file

        Returns:
            WikiAttachment instance or None if upload fails

        Raises:
            ValueError: If file type not allowed or file too large
            SQLAlchemyError: If database operation fails

        Example:
            >>> service = AttachmentService(db)
            >>> with open('document.pdf', 'rb') as f:
            ...     attachment = service.upload_attachment(
            ...         page_id=123,
            ...         file_data=f,
            ...         filename='document.pdf',
            ...         user_id=1
            ...     )
        """
        try:
            # Verify page exists
            page = self.db.query(WikiPage).filter(
                WikiPage.id == page_id,
                WikiPage.is_deleted == False
            ).first()

            if not page:
                logger.warning(f"Page {page_id} not found for attachment upload")
                return None

            # Read file data
            file_data.seek(0)
            file_bytes = file_data.read()
            file_size = len(file_bytes)

            # Validate file size
            if file_size > self.MAX_FILE_SIZE:
                raise ValueError(
                    f"File size ({file_size} bytes) exceeds maximum allowed "
                    f"({self.MAX_FILE_SIZE} bytes)"
                )

            # Detect MIME type and attachment type
            mime_type = self._detect_mime_type(filename, file_bytes)
            attachment_type = self._determine_attachment_type(mime_type)

            # Validate file type
            if not self._is_allowed_type(mime_type):
                raise ValueError(f"File type '{mime_type}' is not allowed")

            # Additional validation for images
            if attachment_type == AttachmentType.IMAGE and file_size > self.MAX_IMAGE_SIZE:
                raise ValueError(
                    f"Image size ({file_size} bytes) exceeds maximum allowed "
                    f"({self.MAX_IMAGE_SIZE} bytes)"
                )

            # Generate unique filename and path
            unique_filename = self._generate_unique_filename(filename)
            file_path = self._get_storage_path(page_id, unique_filename)

            # Save file to storage
            self._save_file(file_path, file_bytes)

            # Create attachment record
            attachment = WikiAttachment(
                page_id=page_id,
                filename=unique_filename,
                original_filename=filename,
                file_path=str(file_path),
                file_size=file_size,
                mime_type=mime_type,
                attachment_type=attachment_type,
                description=description,
                uploaded_by=user_id,
                version=1,
                metadata={}
            )

            # Process image-specific operations
            if attachment_type == AttachmentType.IMAGE:
                image_metadata = self._process_image(file_bytes, file_path)
                attachment.metadata = image_metadata

            self.db.add(attachment)
            self.db.commit()
            self.db.refresh(attachment)

            logger.info(f"Uploaded attachment {attachment.id}: {filename} to page {page_id}")
            return attachment

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error uploading attachment: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error uploading attachment: {str(e)}")
            raise

    def get_attachment(
        self,
        attachment_id: int,
        include_deleted: bool = False
    ) -> Optional[WikiAttachment]:
        """
        Get attachment by ID.

        Args:
            attachment_id: ID of the attachment
            include_deleted: Include deleted attachments

        Returns:
            WikiAttachment instance or None if not found

        Example:
            >>> attachment = service.get_attachment(456)
        """
        try:
            query = self.db.query(WikiAttachment).filter(
                WikiAttachment.id == attachment_id
            )

            if not include_deleted:
                query = query.filter(WikiAttachment.is_deleted == False)

            return query.first()

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving attachment {attachment_id}: {str(e)}")
            return None

    def get_page_attachments(
        self,
        page_id: int,
        attachment_type: Optional[AttachmentType] = None
    ) -> List[WikiAttachment]:
        """
        Get all attachments for a page.

        Args:
            page_id: ID of the page
            attachment_type: Filter by attachment type

        Returns:
            List of WikiAttachment instances

        Example:
            >>> images = service.get_page_attachments(123, AttachmentType.IMAGE)
        """
        try:
            query = self.db.query(WikiAttachment).filter(
                WikiAttachment.page_id == page_id,
                WikiAttachment.is_deleted == False
            )

            if attachment_type:
                query = query.filter(WikiAttachment.attachment_type == attachment_type)

            return query.order_by(WikiAttachment.uploaded_at.desc()).all()

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving attachments for page {page_id}: {str(e)}")
            return []

    def download_attachment(self, attachment_id: int) -> Optional[Tuple[bytes, str, str]]:
        """
        Download attachment file data.

        Args:
            attachment_id: ID of the attachment

        Returns:
            Tuple of (file_bytes, filename, mime_type) or None if not found

        Example:
            >>> data, filename, mime = service.download_attachment(456)
            >>> with open(filename, 'wb') as f:
            ...     f.write(data)
        """
        try:
            attachment = self.get_attachment(attachment_id)
            if not attachment:
                return None

            file_path = Path(attachment.file_path)
            if not file_path.exists():
                logger.error(f"Attachment file not found: {file_path}")
                return None

            with open(file_path, 'rb') as f:
                file_bytes = f.read()

            return file_bytes, attachment.original_filename, attachment.mime_type

        except Exception as e:
            logger.error(f"Error downloading attachment {attachment_id}: {str(e)}")
            return None

    def delete_attachment(
        self,
        attachment_id: int,
        user_id: int,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete an attachment (soft delete by default).

        Args:
            attachment_id: ID of the attachment
            user_id: ID of user performing deletion
            hard_delete: Permanently delete file and record

        Returns:
            True if successful, False otherwise

        Example:
            >>> success = service.delete_attachment(456, user_id=1)
        """
        try:
            attachment = self.get_attachment(attachment_id, include_deleted=True)
            if not attachment:
                return False

            if hard_delete:
                # Delete physical file
                file_path = Path(attachment.file_path)
                if file_path.exists():
                    file_path.unlink()

                    # Delete thumbnail if exists
                    thumb_path = self._get_thumbnail_path(file_path)
                    if thumb_path.exists():
                        thumb_path.unlink()

                # Delete database record
                self.db.delete(attachment)
                logger.warning(f"Hard deleted attachment {attachment_id}")
            else:
                # Soft delete
                attachment.is_deleted = True
                logger.info(f"Soft deleted attachment {attachment_id}")

            self.db.commit()
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting attachment {attachment_id}: {str(e)}")
            return False

    def update_attachment_version(
        self,
        attachment_id: int,
        file_data: BinaryIO,
        user_id: int
    ) -> Optional[WikiAttachment]:
        """
        Update an attachment with a new version.

        Args:
            attachment_id: ID of the attachment to update
            file_data: New file binary data
            user_id: ID of user uploading new version

        Returns:
            Updated WikiAttachment instance or None if failed

        Example:
            >>> with open('document_v2.pdf', 'rb') as f:
            ...     attachment = service.update_attachment_version(456, f, user_id=1)
        """
        try:
            attachment = self.get_attachment(attachment_id)
            if not attachment:
                return None

            # Read new file data
            file_data.seek(0)
            file_bytes = file_data.read()
            file_size = len(file_bytes)

            # Validate file size
            if file_size > self.MAX_FILE_SIZE:
                raise ValueError(f"File size exceeds maximum allowed")

            # Generate new filename for version
            unique_filename = self._generate_unique_filename(attachment.original_filename)
            file_path = self._get_storage_path(attachment.page_id, unique_filename)

            # Save new version
            self._save_file(file_path, file_bytes)

            # Update attachment record
            attachment.filename = unique_filename
            attachment.file_path = str(file_path)
            attachment.file_size = file_size
            attachment.version += 1

            # Update image metadata if applicable
            if attachment.attachment_type == AttachmentType.IMAGE:
                image_metadata = self._process_image(file_bytes, file_path)
                attachment.metadata = image_metadata

            self.db.commit()
            self.db.refresh(attachment)

            logger.info(f"Updated attachment {attachment_id} to version {attachment.version}")
            return attachment

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating attachment version: {str(e)}")
            return None

    def get_thumbnail(
        self,
        attachment_id: int,
        size: Tuple[int, int] = (200, 200)
    ) -> Optional[bytes]:
        """
        Get or generate thumbnail for image attachment.

        Args:
            attachment_id: ID of the attachment
            size: Thumbnail size as (width, height)

        Returns:
            Thumbnail image bytes or None

        Example:
            >>> thumb_bytes = service.get_thumbnail(456, size=(150, 150))
        """
        try:
            attachment = self.get_attachment(attachment_id)
            if not attachment or attachment.attachment_type != AttachmentType.IMAGE:
                return None

            file_path = Path(attachment.file_path)
            thumb_path = self._get_thumbnail_path(file_path, size)

            # Return existing thumbnail if available
            if thumb_path.exists():
                with open(thumb_path, 'rb') as f:
                    return f.read()

            # Generate new thumbnail
            thumbnail_bytes = self._generate_thumbnail(file_path, thumb_path, size)
            return thumbnail_bytes

        except Exception as e:
            logger.error(f"Error getting thumbnail: {str(e)}")
            return None

    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics for attachments.

        Returns:
            Dictionary with storage statistics

        Example:
            >>> stats = service.get_storage_statistics()
            >>> print(f"Total size: {stats['total_size_mb']} MB")
        """
        try:
            from sqlalchemy import func

            # Get total attachment count and size
            result = self.db.query(
                func.count(WikiAttachment.id).label('count'),
                func.sum(WikiAttachment.file_size).label('total_size')
            ).filter(
                WikiAttachment.is_deleted == False
            ).first()

            total_count = result.count or 0
            total_size = result.total_size or 0

            # Get counts by type
            type_counts = self.db.query(
                WikiAttachment.attachment_type,
                func.count(WikiAttachment.id).label('count'),
                func.sum(WikiAttachment.file_size).label('size')
            ).filter(
                WikiAttachment.is_deleted == False
            ).group_by(WikiAttachment.attachment_type).all()

            by_type = {}
            for att_type, count, size in type_counts:
                by_type[att_type.value] = {
                    'count': count,
                    'size_bytes': size or 0,
                    'size_mb': round((size or 0) / (1024 * 1024), 2)
                }

            return {
                'total_attachments': total_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'by_type': by_type
            }

        except Exception as e:
            logger.error(f"Error getting storage statistics: {str(e)}")
            return {}

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _ensure_storage_directory(self) -> None:
        """Ensure storage directory exists."""
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _detect_mime_type(self, filename: str, file_bytes: bytes) -> str:
        """Detect MIME type from filename and file content."""
        # Try to guess from filename
        mime_type, _ = mimetypes.guess_type(filename)

        if mime_type:
            return mime_type

        # Fallback to binary detection based on magic bytes
        if file_bytes.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        elif file_bytes.startswith(b'\x89PNG'):
            return 'image/png'
        elif file_bytes.startswith(b'GIF8'):
            return 'image/gif'
        elif file_bytes.startswith(b'%PDF'):
            return 'application/pdf'

        return 'application/octet-stream'

    def _determine_attachment_type(self, mime_type: str) -> AttachmentType:
        """Determine attachment type from MIME type."""
        if mime_type in self.ALLOWED_IMAGE_TYPES or mime_type.startswith('image/'):
            return AttachmentType.IMAGE
        elif mime_type in self.ALLOWED_VIDEO_TYPES or mime_type.startswith('video/'):
            return AttachmentType.VIDEO
        elif mime_type in self.ALLOWED_AUDIO_TYPES or mime_type.startswith('audio/'):
            return AttachmentType.AUDIO
        elif mime_type in self.ALLOWED_DOCUMENT_TYPES:
            return AttachmentType.DOCUMENT
        elif mime_type in {'application/zip', 'application/x-tar', 'application/gzip'}:
            return AttachmentType.ARCHIVE
        elif mime_type.startswith('text/'):
            return AttachmentType.CODE
        else:
            return AttachmentType.OTHER

    def _is_allowed_type(self, mime_type: str) -> bool:
        """Check if MIME type is allowed."""
        allowed_types = (
            self.ALLOWED_IMAGE_TYPES |
            self.ALLOWED_VIDEO_TYPES |
            self.ALLOWED_AUDIO_TYPES |
            self.ALLOWED_DOCUMENT_TYPES
        )

        return (
            mime_type in allowed_types or
            mime_type.startswith('text/') or
            mime_type in {'application/zip', 'application/json'}
        )

    def _generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename using timestamp and hash."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        random_hash = hashlib.md5(
            f"{original_filename}{timestamp}".encode()
        ).hexdigest()[:8]

        name, ext = os.path.splitext(original_filename)
        safe_name = re.sub(r'[^\w\-]', '_', name)[:50]

        return f"{timestamp}_{random_hash}_{safe_name}{ext}"

    def _get_storage_path(self, page_id: int, filename: str) -> Path:
        """Get storage path for attachment."""
        # Organize by page_id in subdirectories
        page_dir = self.storage_path / str(page_id % 1000) / str(page_id)
        page_dir.mkdir(parents=True, exist_ok=True)

        return page_dir / filename

    def _save_file(self, file_path: Path, file_bytes: bytes) -> None:
        """Save file to storage."""
        with open(file_path, 'wb') as f:
            f.write(file_bytes)

    def _process_image(self, file_bytes: bytes, file_path: Path) -> Dict[str, Any]:
        """
        Process image and extract metadata.

        In production, integrate with PIL/Pillow for image processing.
        """
        metadata = {
            'processed': True,
            'timestamp': datetime.utcnow().isoformat()
        }

        try:
            # TODO: Integrate PIL/Pillow
            # from PIL import Image
            # with Image.open(BytesIO(file_bytes)) as img:
            #     metadata['width'] = img.width
            #     metadata['height'] = img.height
            #     metadata['format'] = img.format
            #     metadata['mode'] = img.mode

            # For now, just return basic metadata
            logger.info("Image processing placeholder - integrate PIL/Pillow for production")

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")

        return metadata

    def _get_thumbnail_path(
        self,
        file_path: Path,
        size: Tuple[int, int] = (200, 200)
    ) -> Path:
        """Get path for thumbnail file."""
        thumb_dir = file_path.parent / 'thumbnails'
        thumb_dir.mkdir(exist_ok=True)

        name = file_path.stem
        ext = file_path.suffix
        size_str = f"{size[0]}x{size[1]}"

        return thumb_dir / f"{name}_{size_str}{ext}"

    def _generate_thumbnail(
        self,
        source_path: Path,
        thumb_path: Path,
        size: Tuple[int, int]
    ) -> Optional[bytes]:
        """
        Generate thumbnail for image.

        In production, integrate with PIL/Pillow.
        """
        try:
            # TODO: Integrate PIL/Pillow
            # from PIL import Image
            # with Image.open(source_path) as img:
            #     img.thumbnail(size, Image.Resampling.LANCZOS)
            #     img.save(thumb_path, optimize=True, quality=85)
            #     with open(thumb_path, 'rb') as f:
            #         return f.read()

            logger.warning("Thumbnail generation requires PIL/Pillow integration")

            # Return original image as fallback
            with open(source_path, 'rb') as f:
                return f.read()

        except Exception as e:
            logger.error(f"Error generating thumbnail: {str(e)}")
            return None
