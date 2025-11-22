"""Attachment handler for email attachments."""

import os
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, List, Dict, Any
from email.message import Message
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)


class AttachmentHandler:
    """Handler for email attachments."""

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize attachment handler.

        Args:
            storage_path: Path to store attachments (default: ./attachments)
        """
        self.storage_path = Path(storage_path or "./attachments")
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _generate_safe_filename(self, filename: str, content: bytes) -> str:
        """Generate a safe unique filename.

        Args:
            filename: Original filename
            content: File content (for hash)

        Returns:
            Safe unique filename
        """
        # Generate hash of content
        content_hash = hashlib.md5(content).hexdigest()[:8]

        # Clean filename
        safe_name = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-'))
        safe_name = safe_name.strip()

        # Add hash to ensure uniqueness
        name_parts = safe_name.rsplit('.', 1)
        if len(name_parts) == 2:
            safe_name = f"{name_parts[0]}_{content_hash}.{name_parts[1]}"
        else:
            safe_name = f"{safe_name}_{content_hash}"

        return safe_name

    def save_attachment(
        self,
        part: Message,
        filename: Optional[str] = None,
        subfolder: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save email attachment to disk.

        Args:
            part: Email message part containing attachment
            filename: Override filename
            subfolder: Subfolder to save in

        Returns:
            Dict with attachment info

        Raises:
            ValueError: If attachment is too large
        """
        # Get content
        content = part.get_payload(decode=True)
        if not content:
            raise ValueError("Attachment has no content")

        # Check size
        size_mb = len(content) / (1024 * 1024)
        if size_mb > settings.email_max_attachment_size_mb:
            raise ValueError(
                f"Attachment too large: {size_mb:.1f}MB > "
                f"{settings.email_max_attachment_size_mb}MB"
            )

        # Get filename
        if not filename:
            filename = part.get_filename()
            if filename:
                from src.modules.email.parser import EmailParser
                filename = EmailParser.decode_header_value(filename)

        if not filename:
            # Generate filename from content type
            ext = mimetypes.guess_extension(part.get_content_type()) or '.bin'
            filename = f"attachment{ext}"

        # Generate safe filename
        safe_filename = self._generate_safe_filename(filename, content)

        # Determine save path
        if subfolder:
            save_dir = self.storage_path / subfolder
            save_dir.mkdir(parents=True, exist_ok=True)
        else:
            save_dir = self.storage_path

        file_path = save_dir / safe_filename

        # Save file
        try:
            with open(file_path, 'wb') as f:
                f.write(content)

            logger.info(f"Saved attachment: {file_path} ({size_mb:.2f}MB)")

            return {
                'filename': filename,
                'safe_filename': safe_filename,
                'file_path': str(file_path),
                'content_type': part.get_content_type(),
                'size': len(content),
                'content_id': part.get('Content-ID', '').strip('<>')
            }

        except Exception as e:
            logger.error(f"Failed to save attachment: {e}")
            raise

    def save_attachments(
        self,
        msg: Message,
        subfolder: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Save all attachments from an email.

        Args:
            msg: Email message object
            subfolder: Subfolder to save in

        Returns:
            List of saved attachment info dicts
        """
        from src.modules.email.parser import EmailParser

        attachments_info = EmailParser.get_attachments_info(msg)
        saved_attachments = []

        for att_info in attachments_info:
            try:
                saved_info = self.save_attachment(
                    att_info['part'],
                    att_info['filename'],
                    subfolder
                )
                saved_info['is_inline'] = att_info['is_inline']
                saved_attachments.append(saved_info)

            except Exception as e:
                logger.error(
                    f"Failed to save attachment {att_info['filename']}: {e}"
                )

        logger.info(f"Saved {len(saved_attachments)} attachments")
        return saved_attachments

    def get_attachment(self, file_path: str) -> Optional[bytes]:
        """Get attachment content from disk.

        Args:
            file_path: Path to attachment file

        Returns:
            File content or None if not found
        """
        path = Path(file_path)

        if not path.exists():
            logger.error(f"Attachment not found: {file_path}")
            return None

        try:
            with open(path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read attachment: {e}")
            return None

    def delete_attachment(self, file_path: str) -> bool:
        """Delete attachment from disk.

        Args:
            file_path: Path to attachment file

        Returns:
            True if deleted successfully
        """
        path = Path(file_path)

        if not path.exists():
            logger.warning(f"Attachment not found: {file_path}")
            return False

        try:
            path.unlink()
            logger.info(f"Deleted attachment: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete attachment: {e}")
            return False

    def delete_attachments(self, file_paths: List[str]) -> int:
        """Delete multiple attachments.

        Args:
            file_paths: List of file paths

        Returns:
            Number of successfully deleted files
        """
        deleted_count = 0
        for file_path in file_paths:
            if self.delete_attachment(file_path):
                deleted_count += 1

        return deleted_count

    def get_attachment_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get attachment information.

        Args:
            file_path: Path to attachment file

        Returns:
            Attachment info dict or None
        """
        path = Path(file_path)

        if not path.exists():
            return None

        try:
            stat = path.stat()
            mime_type, _ = mimetypes.guess_type(str(path))

            return {
                'filename': path.name,
                'file_path': str(path),
                'content_type': mime_type or 'application/octet-stream',
                'size': stat.st_size,
                'created_at': stat.st_ctime,
                'modified_at': stat.st_mtime
            }
        except Exception as e:
            logger.error(f"Failed to get attachment info: {e}")
            return None

    def list_attachments(self, subfolder: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all saved attachments.

        Args:
            subfolder: Subfolder to list from

        Returns:
            List of attachment info dicts
        """
        search_dir = self.storage_path / subfolder if subfolder else self.storage_path

        if not search_dir.exists():
            return []

        attachments = []
        for file_path in search_dir.rglob('*'):
            if file_path.is_file():
                info = self.get_attachment_info(str(file_path))
                if info:
                    attachments.append(info)

        return attachments

    def cleanup_old_attachments(self, days: int = 30) -> int:
        """Clean up attachments older than specified days.

        Args:
            days: Number of days

        Returns:
            Number of deleted files
        """
        import time

        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)
        deleted_count = 0

        for file_path in self.storage_path.rglob('*'):
            if file_path.is_file():
                try:
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old attachment: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {e}")

        logger.info(f"Cleaned up {deleted_count} old attachments")
        return deleted_count

    def get_total_size(self, subfolder: Optional[str] = None) -> int:
        """Get total size of all attachments.

        Args:
            subfolder: Subfolder to calculate for

        Returns:
            Total size in bytes
        """
        search_dir = self.storage_path / subfolder if subfolder else self.storage_path

        if not search_dir.exists():
            return 0

        total_size = 0
        for file_path in search_dir.rglob('*'):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except Exception as e:
                    logger.error(f"Failed to get size of {file_path}: {e}")

        return total_size

    def validate_attachment(self, file_path: str) -> bool:
        """Validate attachment file.

        Args:
            file_path: Path to attachment file

        Returns:
            True if valid
        """
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            logger.error(f"Attachment not found: {file_path}")
            return False

        # Check if it's a file
        if not path.is_file():
            logger.error(f"Not a file: {file_path}")
            return False

        # Check size
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > settings.email_max_attachment_size_mb:
            logger.error(f"Attachment too large: {size_mb:.1f}MB")
            return False

        return True
