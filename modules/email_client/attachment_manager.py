"""
Attachment Manager

Handles email attachments - storage, retrieval, and virus scanning.
"""

import hashlib
import logging
import mimetypes
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class Attachment:
    """Attachment metadata."""
    attachment_id: str
    filename: str
    content_type: str
    size_bytes: int
    file_path: Optional[str] = None
    data: Optional[bytes] = None
    checksum: Optional[str] = None
    is_safe: bool = True
    virus_scan_result: Optional[str] = None
    created_at: datetime = datetime.utcnow()


class AttachmentManager:
    """
    Email attachment manager.

    Handles attachment storage, retrieval, and security scanning.
    """

    def __init__(
        self,
        storage_path: str = "./email_attachments",
        max_attachment_size: int = 25 * 1024 * 1024,  # 25MB
        allowed_extensions: Optional[List[str]] = None,
        enable_virus_scan: bool = False
    ):
        """
        Initialize attachment manager.

        Args:
            storage_path: Path for storing attachments
            max_attachment_size: Maximum attachment size in bytes
            allowed_extensions: List of allowed file extensions
            enable_virus_scan: Enable virus scanning
        """
        self.storage_path = Path(storage_path)
        self.max_attachment_size = max_attachment_size
        self.allowed_extensions = allowed_extensions
        self.enable_virus_scan = enable_virus_scan

        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Dangerous extensions to block
        self.dangerous_extensions = {
            '.exe', '.bat', '.cmd', '.com', '.pif', '.scr',
            '.vbs', '.js', '.jar', '.dll', '.msi'
        }

    async def process_attachments(
        self,
        attachments: List[Dict[str, Any]]
    ) -> List[Attachment]:
        """
        Process and store attachments.

        Args:
            attachments: List of attachment data

        Returns:
            List[Attachment]: Processed attachments
        """
        processed = []

        for att_data in attachments:
            try:
                attachment = await self.process_attachment(att_data)
                if attachment:
                    processed.append(attachment)
            except Exception as e:
                logger.error(f"Failed to process attachment: {e}")

        return processed

    async def process_attachment(
        self,
        attachment_data: Dict[str, Any]
    ) -> Optional[Attachment]:
        """
        Process a single attachment.

        Args:
            attachment_data: Attachment data dict

        Returns:
            Optional[Attachment]: Processed attachment
        """
        filename = attachment_data.get('filename', 'attachment')
        content_type = attachment_data.get('content_type', 'application/octet-stream')
        data = attachment_data.get('data')

        if not data:
            return None

        # Size check
        size = len(data)
        if size > self.max_attachment_size:
            logger.warning(f"Attachment {filename} exceeds size limit: {size} bytes")
            return None

        # Extension check
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext in self.dangerous_extensions:
            logger.warning(f"Dangerous extension blocked: {ext}")
            return None

        if self.allowed_extensions and ext not in self.allowed_extensions:
            logger.warning(f"Extension not allowed: {ext}")
            return None

        # Generate ID and storage path
        attachment_id = str(uuid4())
        file_path = self._get_storage_path(attachment_id, filename)

        # Calculate checksum
        checksum = hashlib.sha256(data).hexdigest()

        # Virus scan
        is_safe = True
        scan_result = None
        if self.enable_virus_scan:
            is_safe, scan_result = await self._scan_for_virus(data)

        if not is_safe:
            logger.warning(f"Virus detected in attachment {filename}: {scan_result}")
            return None

        # Save to disk
        try:
            with open(file_path, 'wb') as f:
                f.write(data)
        except Exception as e:
            logger.error(f"Failed to save attachment {filename}: {e}")
            return None

        attachment = Attachment(
            attachment_id=attachment_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size,
            file_path=str(file_path),
            checksum=checksum,
            is_safe=is_safe,
            virus_scan_result=scan_result
        )

        return attachment

    def _get_storage_path(self, attachment_id: str, filename: str) -> Path:
        """
        Get storage path for attachment.

        Organizes by year/month for better filesystem performance.
        """
        now = datetime.utcnow()
        year_month = f"{now.year}/{now.month:02d}"

        # Create directory
        dir_path = self.storage_path / year_month
        dir_path.mkdir(parents=True, exist_ok=True)

        # Use ID + filename to avoid collisions
        safe_filename = self._sanitize_filename(filename)
        file_path = dir_path / f"{attachment_id}_{safe_filename}"

        return file_path

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to be filesystem-safe."""
        # Remove dangerous characters
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in '.-_ ':
                safe_chars.append(char)
            else:
                safe_chars.append('_')

        return ''.join(safe_chars)

    async def _scan_for_virus(self, data: bytes) -> tuple[bool, Optional[str]]:
        """
        Scan data for viruses.

        Args:
            data: File data

        Returns:
            tuple: (is_safe, scan_result)
        """
        # This is a placeholder implementation
        # In production, integrate with ClamAV or similar

        # Simple heuristics
        if len(data) < 10:
            return False, "File too small"

        # Check for executable signatures
        if data[:2] == b'MZ':  # DOS/Windows executable
            return False, "Executable file detected"

        # For now, assume safe
        return True, "Clean"

    async def get_attachment(self, attachment_id: str) -> Optional[bytes]:
        """
        Retrieve attachment data.

        Args:
            attachment_id: Attachment ID

        Returns:
            Optional[bytes]: Attachment data
        """
        # Search for file (we don't know the exact path without metadata)
        # In production, use database to track file paths

        for root, _, files in os.walk(self.storage_path):
            for file in files:
                if file.startswith(attachment_id):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'rb') as f:
                            return f.read()
                    except Exception as e:
                        logger.error(f"Failed to read attachment {attachment_id}: {e}")
                        return None

        return None

    async def delete_attachment(self, attachment_id: str) -> bool:
        """
        Delete an attachment.

        Args:
            attachment_id: Attachment ID

        Returns:
            bool: Success status
        """
        for root, _, files in os.walk(self.storage_path):
            for file in files:
                if file.startswith(attachment_id):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted attachment: {attachment_id}")
                        return True
                    except Exception as e:
                        logger.error(f"Failed to delete attachment {attachment_id}: {e}")
                        return False

        return False

    def get_file_icon(self, filename: str) -> str:
        """
        Get icon name for file type.

        Args:
            filename: Filename

        Returns:
            str: Icon identifier
        """
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        icon_map = {
            '.pdf': 'file-pdf',
            '.doc': 'file-word',
            '.docx': 'file-word',
            '.xls': 'file-excel',
            '.xlsx': 'file-excel',
            '.ppt': 'file-powerpoint',
            '.pptx': 'file-powerpoint',
            '.jpg': 'file-image',
            '.jpeg': 'file-image',
            '.png': 'file-image',
            '.gif': 'file-image',
            '.zip': 'file-archive',
            '.rar': 'file-archive',
            '.7z': 'file-archive',
            '.txt': 'file-text',
            '.csv': 'file-csv',
        }

        return icon_map.get(ext, 'file')

    def format_file_size(self, size_bytes: int) -> str:
        """
        Format file size for display.

        Args:
            size_bytes: Size in bytes

        Returns:
            str: Formatted size
        """
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        unit_idx = 0

        while size >= 1024 and unit_idx < len(units) - 1:
            size /= 1024
            unit_idx += 1

        return f"{size:.2f} {units[unit_idx]}"

    def guess_content_type(self, filename: str) -> str:
        """
        Guess content type from filename.

        Args:
            filename: Filename

        Returns:
            str: Content type
        """
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'

    async def create_thumbnail(
        self,
        attachment_id: str,
        size: tuple[int, int] = (150, 150)
    ) -> Optional[bytes]:
        """
        Create thumbnail for image attachment.

        Args:
            attachment_id: Attachment ID
            size: Thumbnail size (width, height)

        Returns:
            Optional[bytes]: Thumbnail data
        """
        data = await self.get_attachment(attachment_id)
        if not data:
            return None

        try:
            from PIL import Image
            from io import BytesIO

            # Open image
            img = Image.open(BytesIO(data))

            # Create thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # Save to bytes
            output = BytesIO()
            img.save(output, format='PNG')
            return output.getvalue()

        except Exception as e:
            logger.error(f"Failed to create thumbnail: {e}")
            return None

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dict: Storage stats
        """
        total_files = 0
        total_size = 0

        for root, _, files in os.walk(self.storage_path):
            for file in files:
                total_files += 1
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                except Exception:
                    pass

        return {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_formatted': self.format_file_size(total_size),
            'storage_path': str(self.storage_path)
        }

    async def cleanup_old_attachments(self, days: int = 30) -> int:
        """
        Clean up attachments older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            int: Number of files deleted
        """
        import time

        threshold = time.time() - (days * 24 * 60 * 60)
        deleted_count = 0

        for root, _, files in os.walk(self.storage_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if os.path.getmtime(file_path) < threshold:
                        os.remove(file_path)
                        deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete old file {file}: {e}")

        logger.info(f"Cleaned up {deleted_count} old attachments")
        return deleted_count
