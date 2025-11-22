"""File validation module for NEXUS Platform.

This module handles file type validation, size limits, and virus scanning integration.
"""
import os
import hashlib
import mimetypes
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import magic  # python-magic for MIME type detection


@dataclass
class ValidationResult:
    """Result of file validation."""
    is_valid: bool
    error_message: Optional[str] = None
    warnings: List[str] = None
    file_info: Optional[Dict] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class FileValidator:
    """Validates files for upload and processing."""

    # Supported file types by category
    SUPPORTED_TYPES = {
        'document': {
            'extensions': ['.doc', '.docx', '.pdf', '.txt', '.rtf', '.md',
                          '.xls', '.xlsx', '.csv', '.ppt', '.pptx',
                          '.json', '.xml', '.yaml', '.yml'],
            'mime_types': [
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/pdf',
                'text/plain',
                'text/markdown',
                'application/rtf',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'text/csv',
                'application/vnd.ms-powerpoint',
                'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'application/json',
                'application/xml',
                'text/xml',
                'application/x-yaml',
                'text/yaml',
            ],
            'max_size': 100 * 1024 * 1024,  # 100MB
        },
        'image': {
            'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico'],
            'mime_types': [
                'image/jpeg',
                'image/png',
                'image/gif',
                'image/bmp',
                'image/svg+xml',
                'image/webp',
                'image/x-icon',
            ],
            'max_size': 50 * 1024 * 1024,  # 50MB
        },
        'video': {
            'extensions': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm'],
            'mime_types': [
                'video/mp4',
                'video/x-msvideo',
                'video/quicktime',
                'video/x-ms-wmv',
                'video/x-flv',
                'video/x-matroska',
                'video/webm',
            ],
            'max_size': 500 * 1024 * 1024,  # 500MB
        },
        'audio': {
            'extensions': ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac'],
            'mime_types': [
                'audio/mpeg',
                'audio/wav',
                'audio/ogg',
                'audio/mp4',
                'audio/flac',
                'audio/aac',
            ],
            'max_size': 100 * 1024 * 1024,  # 100MB
        },
        'archive': {
            'extensions': ['.zip', '.tar', '.gz', '.rar', '.7z', '.bz2'],
            'mime_types': [
                'application/zip',
                'application/x-tar',
                'application/gzip',
                'application/x-rar-compressed',
                'application/x-7z-compressed',
                'application/x-bzip2',
            ],
            'max_size': 1024 * 1024 * 1024,  # 1GB
        },
    }

    # Dangerous file extensions that should be blocked
    BLOCKED_EXTENSIONS = [
        '.exe', '.bat', '.cmd', '.sh', '.dll', '.so', '.dylib',
        '.app', '.deb', '.rpm', '.msi', '.dmg', '.pkg',
        '.scr', '.vbs', '.js', '.jar', '.apk',
    ]

    # Default size limits
    DEFAULT_MAX_SIZE = 100 * 1024 * 1024  # 100MB
    ABSOLUTE_MAX_SIZE = 1024 * 1024 * 1024  # 1GB

    def __init__(self,
                 enable_virus_scan: bool = False,
                 custom_size_limits: Optional[Dict[str, int]] = None):
        """Initialize the file validator.

        Args:
            enable_virus_scan: Whether to enable virus scanning (requires ClamAV)
            custom_size_limits: Custom size limits by category
        """
        self.enable_virus_scan = enable_virus_scan
        self.custom_size_limits = custom_size_limits or {}

        # Initialize magic for MIME type detection
        try:
            self.magic = magic.Magic(mime=True)
        except Exception:
            self.magic = None

    def validate_file(self,
                     file_path: Optional[str] = None,
                     file_content: Optional[bytes] = None,
                     filename: Optional[str] = None,
                     max_size: Optional[int] = None) -> ValidationResult:
        """Validate a file for upload.

        Args:
            file_path: Path to the file on disk
            file_content: File content as bytes
            filename: Original filename
            max_size: Maximum allowed file size

        Returns:
            ValidationResult with validation status and details
        """
        warnings = []

        # Ensure we have either file_path or file_content
        if not file_path and not file_content:
            return ValidationResult(
                is_valid=False,
                error_message="No file provided for validation"
            )

        # Get file size
        if file_path:
            if not os.path.exists(file_path):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"File not found: {file_path}"
                )
            file_size = os.path.getsize(file_path)
            if not filename:
                filename = os.path.basename(file_path)
        else:
            file_size = len(file_content)

        if not filename:
            return ValidationResult(
                is_valid=False,
                error_message="Filename is required"
            )

        # Validate filename
        filename_validation = self._validate_filename(filename)
        if not filename_validation[0]:
            return ValidationResult(
                is_valid=False,
                error_message=filename_validation[1]
            )

        # Get file extension and category
        file_ext = os.path.splitext(filename)[1].lower()
        category = self._get_file_category(file_ext, file_path or file_content)

        # Validate file type
        type_validation = self._validate_file_type(file_ext, category)
        if not type_validation[0]:
            return ValidationResult(
                is_valid=False,
                error_message=type_validation[1]
            )

        # Validate file size
        size_limit = max_size or self._get_size_limit(category)
        size_validation = self._validate_file_size(file_size, size_limit)
        if not size_validation[0]:
            return ValidationResult(
                is_valid=False,
                error_message=size_validation[1]
            )

        # Validate MIME type
        mime_type = self._detect_mime_type(file_path, file_content, filename)
        mime_validation = self._validate_mime_type(mime_type, category)
        if not mime_validation[0]:
            warnings.append(mime_validation[1])

        # Virus scan if enabled
        if self.enable_virus_scan and file_path:
            virus_scan = self._scan_for_viruses(file_path)
            if not virus_scan[0]:
                return ValidationResult(
                    is_valid=False,
                    error_message=virus_scan[1]
                )

        # Calculate file hash
        file_hash = self._calculate_hash(file_path, file_content)

        # Prepare file info
        file_info = {
            'filename': filename,
            'size': file_size,
            'category': category,
            'mime_type': mime_type,
            'extension': file_ext,
            'hash': file_hash,
        }

        return ValidationResult(
            is_valid=True,
            warnings=warnings,
            file_info=file_info
        )

    def _validate_filename(self, filename: str) -> Tuple[bool, Optional[str]]:
        """Validate filename for security issues.

        Args:
            filename: The filename to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename or filename.strip() == '':
            return False, "Filename cannot be empty"

        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False, "Invalid filename: path traversal not allowed"

        # Check for null bytes
        if '\x00' in filename:
            return False, "Invalid filename: null bytes not allowed"

        # Check filename length
        if len(filename) > 255:
            return False, "Filename too long (max 255 characters)"

        return True, None

    def _validate_file_type(self, file_ext: str, category: str) -> Tuple[bool, Optional[str]]:
        """Validate file extension.

        Args:
            file_ext: File extension (e.g., '.pdf')
            category: File category

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if extension is blocked
        if file_ext in self.BLOCKED_EXTENSIONS:
            return False, f"File type '{file_ext}' is not allowed for security reasons"

        # Check if extension is supported
        if category == 'other':
            return False, (
                f"Unsupported file type '{file_ext}'. "
                f"Supported types: {self._get_supported_extensions()}"
            )

        return True, None

    def _validate_file_size(self, file_size: int, max_size: int) -> Tuple[bool, Optional[str]]:
        """Validate file size.

        Args:
            file_size: Size of the file in bytes
            max_size: Maximum allowed size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        if file_size == 0:
            return False, "File is empty"

        if file_size > self.ABSOLUTE_MAX_SIZE:
            return False, (
                f"File size ({self._format_size(file_size)}) exceeds "
                f"absolute maximum ({self._format_size(self.ABSOLUTE_MAX_SIZE)})"
            )

        if file_size > max_size:
            return False, (
                f"File size ({self._format_size(file_size)}) exceeds "
                f"maximum allowed ({self._format_size(max_size)})"
            )

        return True, None

    def _validate_mime_type(self, mime_type: str, category: str) -> Tuple[bool, Optional[str]]:
        """Validate MIME type matches expected category.

        Args:
            mime_type: Detected MIME type
            category: Expected file category

        Returns:
            Tuple of (is_valid, warning_message)
        """
        if category == 'other' or not mime_type:
            return True, None

        category_config = self.SUPPORTED_TYPES.get(category, {})
        allowed_mime_types = category_config.get('mime_types', [])

        if mime_type not in allowed_mime_types:
            return False, (
                f"Warning: MIME type '{mime_type}' doesn't match expected category '{category}'"
            )

        return True, None

    def _get_file_category(self, file_ext: str, file_source) -> str:
        """Determine file category from extension.

        Args:
            file_ext: File extension
            file_source: File path or content (for MIME detection)

        Returns:
            Category name or 'other'
        """
        for category, config in self.SUPPORTED_TYPES.items():
            if file_ext in config['extensions']:
                return category
        return 'other'

    def _get_size_limit(self, category: str) -> int:
        """Get size limit for a file category.

        Args:
            category: File category

        Returns:
            Size limit in bytes
        """
        # Check custom limits first
        if category in self.custom_size_limits:
            return self.custom_size_limits[category]

        # Use default category limit
        category_config = self.SUPPORTED_TYPES.get(category, {})
        return category_config.get('max_size', self.DEFAULT_MAX_SIZE)

    def _detect_mime_type(self,
                         file_path: Optional[str] = None,
                         file_content: Optional[bytes] = None,
                         filename: Optional[str] = None) -> Optional[str]:
        """Detect MIME type of a file.

        Args:
            file_path: Path to file
            file_content: File content
            filename: Filename for fallback detection

        Returns:
            MIME type string or None
        """
        # Try python-magic first (most accurate)
        if self.magic:
            try:
                if file_path:
                    return self.magic.from_file(file_path)
                elif file_content:
                    return magic.from_buffer(file_content, mime=True)
            except Exception:
                pass

        # Fallback to mimetypes module
        if filename:
            mime_type, _ = mimetypes.guess_type(filename)
            return mime_type

        return None

    def _calculate_hash(self,
                       file_path: Optional[str] = None,
                       file_content: Optional[bytes] = None) -> str:
        """Calculate SHA-256 hash of file.

        Args:
            file_path: Path to file
            file_content: File content

        Returns:
            Hex string of file hash
        """
        sha256 = hashlib.sha256()

        if file_path:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
        elif file_content:
            sha256.update(file_content)

        return sha256.hexdigest()

    def _scan_for_viruses(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Scan file for viruses using ClamAV.

        Args:
            file_path: Path to file to scan

        Returns:
            Tuple of (is_clean, error_message)
        """
        # This is a stub for ClamAV integration
        # In production, you would use clamd or pyclamd
        try:
            # Example integration:
            # import clamd
            # cd = clamd.ClamdUnixSocket()
            # scan_result = cd.scan(file_path)
            # if scan_result and 'FOUND' in scan_result.get(file_path, ''):
            #     return False, "Virus detected in file"
            pass
        except Exception as e:
            # Don't fail validation if virus scanner is unavailable
            # Just log the error
            print(f"Virus scan failed: {e}")

        return True, None

    def _get_supported_extensions(self) -> str:
        """Get a formatted string of all supported extensions.

        Returns:
            Comma-separated list of extensions
        """
        all_extensions = []
        for category, config in self.SUPPORTED_TYPES.items():
            all_extensions.extend(config['extensions'])
        return ', '.join(sorted(set(all_extensions)))

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def check_duplicate(self, file_hash: str, session) -> Optional[int]:
        """Check if a file with the same hash already exists.

        Args:
            file_hash: SHA-256 hash of the file
            session: Database session

        Returns:
            File ID if duplicate exists, None otherwise
        """
        from database.models import File

        existing_file = session.query(File).filter(
            File.file_hash == file_hash,
            File.is_deleted == False
        ).first()

        return existing_file.id if existing_file else None
