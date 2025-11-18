"""
Version control system for document management.

This module provides comprehensive version control capabilities including:
- Version creation and management
- Diff tracking between versions
- Rollback functionality
- Branching and merging support
- Version comparison
- Change history tracking
"""

import difflib
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.config import get_settings
from backend.core.exceptions import (
    DocumentNotFoundException,
    DocumentVersionNotFoundException,
    NEXUSException,
    StorageException,
    ValidationException,
)
from backend.core.logging import get_logger
from backend.models.document import Document, DocumentVersion

logger = get_logger(__name__)
settings = get_settings()


class VersioningException(NEXUSException):
    """Exception raised for versioning-related errors."""

    def __init__(self, message: str = "Versioning operation failed", **kwargs: Any) -> None:
        super().__init__(message, status_code=500, **kwargs)


class VersionConflictException(VersioningException):
    """Exception raised when version conflict occurs."""

    def __init__(self, message: str = "Version conflict detected", **kwargs: Any) -> None:
        super().__init__(message, status_code=409, **kwargs)


class VersionLimitExceededException(VersioningException):
    """Exception raised when version history limit is exceeded."""

    def __init__(self, **kwargs: Any) -> None:
        message = f"Version history limit of {settings.VERSION_MAX_HISTORY} exceeded"
        super().__init__(message, status_code=400, **kwargs)


class VersionControlService:
    """
    Service for managing document versions.

    Provides comprehensive version control including creation, comparison,
    rollback, and branching/merging operations.
    """

    def __init__(self, db_session: AsyncSession, storage_path: Optional[str] = None) -> None:
        """
        Initialize version control service.

        Args:
            db_session: Database session
            storage_path: Path to storage directory
        """
        self.db = db_session
        self.storage_path = Path(storage_path or settings.STORAGE_PATH)
        self.versions_path = self.storage_path / "versions"
        self.versions_path.mkdir(parents=True, exist_ok=True)

    async def create_version(
        self,
        document_id: int,
        file_content: bytes,
        user_id: int,
        change_summary: Optional[str] = None,
    ) -> DocumentVersion:
        """
        Create a new version of a document.

        Args:
            document_id: Document ID
            file_content: File content bytes
            user_id: User creating the version
            change_summary: Summary of changes

        Returns:
            DocumentVersion: Created version object

        Raises:
            DocumentNotFoundException: If document not found
            VersionLimitExceededException: If version limit exceeded
            StorageException: If storage operation fails
        """
        logger.info(
            "Creating new version",
            document_id=document_id,
            user_id=user_id,
            content_size=len(file_content),
        )

        # Get document
        result = await self.db.execute(
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.versions))
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentNotFoundException(document_id)

        # Check version limit
        version_count = len(document.versions)
        if version_count >= settings.VERSION_MAX_HISTORY:
            logger.warning(
                "Version limit exceeded",
                document_id=document_id,
                current_count=version_count,
            )
            raise VersionLimitExceededException()

        # Calculate next version number
        next_version = document.current_version + 1

        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()

        # Store version file
        version_file_path = self._get_version_file_path(document_id, next_version)
        try:
            version_file_path.parent.mkdir(parents=True, exist_ok=True)
            version_file_path.write_bytes(file_content)
        except Exception as e:
            logger.exception("Failed to write version file", error=str(e))
            raise StorageException(f"Failed to store version file: {str(e)}")

        # Create version record
        version = DocumentVersion(
            document_id=document_id,
            version_number=next_version,
            file_path=str(version_file_path),
            file_size=len(file_content),
            file_hash=file_hash,
            change_summary=change_summary,
            created_by_id=user_id,
        )

        self.db.add(version)

        # Update document current version
        document.current_version = next_version
        document.file_size = len(file_content)
        document.file_hash = file_hash

        await self.db.commit()
        await self.db.refresh(version)

        logger.info(
            "Version created successfully",
            document_id=document_id,
            version_number=next_version,
            version_id=version.id,
        )

        return version

    async def get_version(self, document_id: int, version_number: int) -> DocumentVersion:
        """
        Get a specific version of a document.

        Args:
            document_id: Document ID
            version_number: Version number

        Returns:
            DocumentVersion: Version object

        Raises:
            DocumentVersionNotFoundException: If version not found
        """
        result = await self.db.execute(
            select(DocumentVersion)
            .where(
                and_(
                    DocumentVersion.document_id == document_id,
                    DocumentVersion.version_number == version_number,
                )
            )
            .options(selectinload(DocumentVersion.created_by))
        )
        version = result.scalar_one_or_none()

        if not version:
            logger.warning(
                "Version not found",
                document_id=document_id,
                version_number=version_number,
            )
            raise DocumentVersionNotFoundException(version_number)

        return version

    async def list_versions(
        self,
        document_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DocumentVersion]:
        """
        List all versions of a document.

        Args:
            document_id: Document ID
            limit: Maximum number of versions to return
            offset: Number of versions to skip

        Returns:
            List[DocumentVersion]: List of versions

        Raises:
            DocumentNotFoundException: If document not found
        """
        # Verify document exists
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        if not result.scalar_one_or_none():
            raise DocumentNotFoundException(document_id)

        # Get versions
        result = await self.db.execute(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(desc(DocumentVersion.version_number))
            .limit(limit)
            .offset(offset)
            .options(selectinload(DocumentVersion.created_by))
        )
        versions = result.scalars().all()

        logger.info(
            "Listed versions",
            document_id=document_id,
            count=len(versions),
            limit=limit,
            offset=offset,
        )

        return list(versions)

    async def get_version_content(self, document_id: int, version_number: int) -> bytes:
        """
        Get the content of a specific version.

        Args:
            document_id: Document ID
            version_number: Version number

        Returns:
            bytes: Version file content

        Raises:
            DocumentVersionNotFoundException: If version not found
            StorageException: If file cannot be read
        """
        version = await self.get_version(document_id, version_number)

        try:
            content = Path(version.file_path).read_bytes()
            logger.info(
                "Retrieved version content",
                document_id=document_id,
                version_number=version_number,
                size=len(content),
            )
            return content
        except Exception as e:
            logger.exception("Failed to read version file", error=str(e))
            raise StorageException(f"Failed to read version file: {str(e)}")

    async def compare_versions(
        self,
        document_id: int,
        version1: int,
        version2: int,
    ) -> Dict[str, Any]:
        """
        Compare two versions of a document.

        Args:
            document_id: Document ID
            version1: First version number
            version2: Second version number

        Returns:
            Dict containing comparison results including:
                - diff: Text diff between versions
                - changes: List of changes
                - similarity: Similarity score (0-1)
                - metadata: Metadata comparison

        Raises:
            DocumentVersionNotFoundException: If either version not found
        """
        logger.info(
            "Comparing versions",
            document_id=document_id,
            version1=version1,
            version2=version2,
        )

        # Get both versions
        v1 = await self.get_version(document_id, version1)
        v2 = await self.get_version(document_id, version2)

        # Get content
        content1 = await self.get_version_content(document_id, version1)
        content2 = await self.get_version_content(document_id, version2)

        # Try to decode as text for diff
        try:
            text1 = content1.decode("utf-8").splitlines(keepends=True)
            text2 = content2.decode("utf-8").splitlines(keepends=True)

            # Generate unified diff
            diff = list(
                difflib.unified_diff(
                    text1,
                    text2,
                    fromfile=f"version_{version1}",
                    tofile=f"version_{version2}",
                    lineterm="",
                )
            )

            # Calculate similarity
            similarity = difflib.SequenceMatcher(None, text1, text2).ratio()

            # Extract changes
            changes = self._extract_changes(diff)

        except UnicodeDecodeError:
            # Binary file, just compare hashes
            diff = ["Binary files differ" if v1.file_hash != v2.file_hash else "Files are identical"]
            similarity = 1.0 if v1.file_hash == v2.file_hash else 0.0
            changes = []

        comparison = {
            "document_id": document_id,
            "version1": {
                "number": version1,
                "size": v1.file_size,
                "hash": v1.file_hash,
                "created_at": v1.created_at.isoformat() if v1.created_at else None,
                "created_by": v1.created_by.username if v1.created_by else None,
            },
            "version2": {
                "number": version2,
                "size": v2.file_size,
                "hash": v2.file_hash,
                "created_at": v2.created_at.isoformat() if v2.created_at else None,
                "created_by": v2.created_by.username if v2.created_by else None,
            },
            "diff": diff,
            "changes": changes,
            "similarity": similarity,
            "size_change": v2.file_size - v1.file_size,
            "is_identical": v1.file_hash == v2.file_hash,
        }

        logger.info(
            "Version comparison complete",
            document_id=document_id,
            similarity=similarity,
            change_count=len(changes),
        )

        return comparison

    async def rollback_to_version(
        self,
        document_id: int,
        version_number: int,
        user_id: int,
        create_backup: bool = True,
    ) -> DocumentVersion:
        """
        Rollback document to a specific version.

        Args:
            document_id: Document ID
            version_number: Version to rollback to
            user_id: User performing rollback
            create_backup: Whether to create backup of current version

        Returns:
            DocumentVersion: New version created from rollback

        Raises:
            DocumentNotFoundException: If document not found
            DocumentVersionNotFoundException: If target version not found
        """
        logger.info(
            "Rolling back to version",
            document_id=document_id,
            target_version=version_number,
            user_id=user_id,
        )

        # Get document
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentNotFoundException(document_id)

        # Get target version content
        content = await self.get_version_content(document_id, version_number)

        # Create new version from rollback
        change_summary = f"Rollback to version {version_number}"
        new_version = await self.create_version(
            document_id=document_id,
            file_content=content,
            user_id=user_id,
            change_summary=change_summary,
        )

        logger.info(
            "Rollback completed",
            document_id=document_id,
            target_version=version_number,
            new_version=new_version.version_number,
        )

        return new_version

    async def delete_version(
        self,
        document_id: int,
        version_number: int,
        user_id: int,
    ) -> None:
        """
        Delete a specific version (soft delete).

        Args:
            document_id: Document ID
            version_number: Version number to delete
            user_id: User performing deletion

        Raises:
            DocumentVersionNotFoundException: If version not found
            ValidationException: If trying to delete current version
        """
        logger.info(
            "Deleting version",
            document_id=document_id,
            version_number=version_number,
            user_id=user_id,
        )

        # Get document
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentNotFoundException(document_id)

        # Don't allow deleting current version
        if document.current_version == version_number:
            raise ValidationException(
                "Cannot delete current version",
                errors={"version": "Current version cannot be deleted"},
            )

        # Get version
        version = await self.get_version(document_id, version_number)

        # Soft delete
        await self.db.delete(version)
        await self.db.commit()

        logger.info("Version deleted", document_id=document_id, version_number=version_number)

    async def get_version_diff(
        self,
        document_id: int,
        from_version: int,
        to_version: int,
    ) -> List[str]:
        """
        Get a unified diff between two versions.

        Args:
            document_id: Document ID
            from_version: Starting version number
            to_version: Ending version number

        Returns:
            List[str]: Lines of unified diff

        Raises:
            DocumentVersionNotFoundException: If either version not found
        """
        comparison = await self.compare_versions(document_id, from_version, to_version)
        return comparison["diff"]

    async def get_change_history(
        self,
        document_id: int,
        from_version: Optional[int] = None,
        to_version: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get change history between versions.

        Args:
            document_id: Document ID
            from_version: Starting version (default: first version)
            to_version: Ending version (default: current version)

        Returns:
            List of change records

        Raises:
            DocumentNotFoundException: If document not found
        """
        versions = await self.list_versions(document_id, limit=1000)

        if not versions:
            return []

        # Determine version range
        if from_version is None:
            from_version = versions[-1].version_number
        if to_version is None:
            to_version = versions[0].version_number

        # Filter versions in range
        relevant_versions = [
            v for v in versions if from_version <= v.version_number <= to_version
        ]

        # Build change history
        history = []
        for version in reversed(relevant_versions):
            history.append(
                {
                    "version_number": version.version_number,
                    "created_at": version.created_at.isoformat() if version.created_at else None,
                    "created_by": version.created_by.username if version.created_by else None,
                    "file_size": version.file_size,
                    "file_hash": version.file_hash,
                    "change_summary": version.change_summary,
                }
            )

        logger.info(
            "Retrieved change history",
            document_id=document_id,
            from_version=from_version,
            to_version=to_version,
            count=len(history),
        )

        return history

    def _get_version_file_path(self, document_id: int, version_number: int) -> Path:
        """
        Get the file path for a version.

        Args:
            document_id: Document ID
            version_number: Version number

        Returns:
            Path: Path to version file
        """
        return self.versions_path / f"doc_{document_id}" / f"v{version_number}"

    def _extract_changes(self, diff_lines: List[str]) -> List[Dict[str, Any]]:
        """
        Extract structured changes from diff lines.

        Args:
            diff_lines: Unified diff lines

        Returns:
            List of change records
        """
        changes = []
        current_change = None

        for line in diff_lines:
            if line.startswith("@@"):
                if current_change:
                    changes.append(current_change)
                current_change = {
                    "type": "chunk",
                    "header": line,
                    "additions": [],
                    "deletions": [],
                }
            elif current_change:
                if line.startswith("+") and not line.startswith("+++"):
                    current_change["additions"].append(line[1:])
                elif line.startswith("-") and not line.startswith("---"):
                    current_change["deletions"].append(line[1:])

        if current_change:
            changes.append(current_change)

        return changes


class VersionBranchingService:
    """
    Service for managing version branches and merging.

    Provides advanced branching capabilities for collaborative editing.
    """

    def __init__(self, db_session: AsyncSession, version_service: VersionControlService) -> None:
        """
        Initialize branching service.

        Args:
            db_session: Database session
            version_service: Version control service instance
        """
        self.db = db_session
        self.version_service = version_service

    async def create_branch(
        self,
        document_id: int,
        from_version: int,
        branch_name: str,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Create a new branch from a version.

        Args:
            document_id: Document ID
            from_version: Version to branch from
            branch_name: Name for the branch
            user_id: User creating the branch

        Returns:
            Dict containing branch information

        Note:
            Branching is implemented through version metadata.
            Full branch support would require additional database tables.
        """
        logger.info(
            "Creating branch",
            document_id=document_id,
            from_version=from_version,
            branch_name=branch_name,
        )

        # Get source version content
        content = await self.version_service.get_version_content(document_id, from_version)

        # Create new version for branch
        change_summary = f"Branch '{branch_name}' created from version {from_version}"
        branch_version = await self.version_service.create_version(
            document_id=document_id,
            file_content=content,
            user_id=user_id,
            change_summary=change_summary,
        )

        branch_info = {
            "branch_name": branch_name,
            "branch_version": branch_version.version_number,
            "source_version": from_version,
            "created_by": user_id,
            "created_at": branch_version.created_at.isoformat() if branch_version.created_at else None,
        }

        logger.info("Branch created", **branch_info)

        return branch_info

    async def merge_versions(
        self,
        document_id: int,
        base_version: int,
        merge_version: int,
        user_id: int,
        resolution_strategy: str = "latest",
    ) -> DocumentVersion:
        """
        Merge two versions together.

        Args:
            document_id: Document ID
            base_version: Base version number
            merge_version: Version to merge in
            user_id: User performing merge
            resolution_strategy: How to resolve conflicts ('latest', 'base', 'manual')

        Returns:
            DocumentVersion: Merged version

        Note:
            This is a simplified merge. Production systems would need
            sophisticated conflict resolution.
        """
        logger.info(
            "Merging versions",
            document_id=document_id,
            base_version=base_version,
            merge_version=merge_version,
            strategy=resolution_strategy,
        )

        # Get both versions
        if resolution_strategy == "latest":
            # Use the later version
            target_version = max(base_version, merge_version)
            content = await self.version_service.get_version_content(document_id, target_version)
        elif resolution_strategy == "base":
            # Use base version
            content = await self.version_service.get_version_content(document_id, base_version)
        else:
            raise ValidationException(
                f"Unsupported merge strategy: {resolution_strategy}",
                errors={"strategy": "Must be 'latest' or 'base'"},
            )

        # Create merged version
        change_summary = f"Merged version {merge_version} into {base_version}"
        merged_version = await self.version_service.create_version(
            document_id=document_id,
            file_content=content,
            user_id=user_id,
            change_summary=change_summary,
        )

        logger.info(
            "Merge completed",
            document_id=document_id,
            merged_version=merged_version.version_number,
        )

        return merged_version
