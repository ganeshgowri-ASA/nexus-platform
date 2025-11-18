"""
Unit tests for version control system.

Tests cover:
- Version creation and management
- Version retrieval and listing
- Version comparison and diff generation
- Rollback functionality
- Version deletion
- Change history tracking
- Version branching and merging
"""

import pytest
import hashlib
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from modules.documents.versioning import (
    VersionControlService,
    VersionBranchingService,
    VersioningException,
    VersionConflictException,
    VersionLimitExceededException,
)
from backend.models.document import Document, DocumentVersion
from backend.core.exceptions import (
    DocumentNotFoundException,
    DocumentVersionNotFoundException,
    ValidationException,
)


@pytest.mark.unit
class TestVersionControlService:
    """Test version control service functionality."""

    @pytest.mark.asyncio
    async def test_create_version_success(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test creating a new document version."""
        service = VersionControlService(db_session, str(temp_storage_path))
        content = b"New version content"

        version = await service.create_version(
            document_id=test_document.id,
            file_content=content,
            user_id=regular_user.id,
            change_summary="Updated content",
        )

        assert version.document_id == test_document.id
        assert version.version_number == 2  # First version is 1
        assert version.file_size == len(content)
        assert version.file_hash == hashlib.sha256(content).hexdigest()
        assert version.change_summary == "Updated content"
        assert version.created_by_id == regular_user.id

    @pytest.mark.asyncio
    async def test_create_version_increments_document_version(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test that creating version increments document current_version."""
        service = VersionControlService(db_session, str(temp_storage_path))
        initial_version = test_document.current_version

        await service.create_version(
            document_id=test_document.id,
            file_content=b"Updated",
            user_id=regular_user.id,
        )

        db_session.refresh(test_document)
        assert test_document.current_version == initial_version + 1

    @pytest.mark.asyncio
    async def test_create_version_stores_file(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test that version file is stored on disk."""
        service = VersionControlService(db_session, str(temp_storage_path))
        content = b"File content for version"

        version = await service.create_version(
            document_id=test_document.id,
            file_content=content,
            user_id=regular_user.id,
        )

        file_path = Path(version.file_path)
        assert file_path.exists()
        assert file_path.read_bytes() == content

    @pytest.mark.asyncio
    async def test_create_version_nonexistent_document(
        self, db_session, regular_user, temp_storage_path
    ):
        """Test creating version for non-existent document fails."""
        service = VersionControlService(db_session, str(temp_storage_path))

        with pytest.raises(DocumentNotFoundException):
            await service.create_version(
                document_id=99999,
                file_content=b"content",
                user_id=regular_user.id,
            )

    @pytest.mark.asyncio
    async def test_create_version_limit_exceeded(
        self, db_session, test_document, regular_user, temp_storage_path, test_settings
    ):
        """Test that version limit is enforced."""
        test_settings.VERSION_MAX_HISTORY = 2
        service = VersionControlService(db_session, str(temp_storage_path))

        # Create versions up to limit
        await service.create_version(
            document_id=test_document.id,
            file_content=b"v2",
            user_id=regular_user.id,
        )
        await service.create_version(
            document_id=test_document.id,
            file_content=b"v3",
            user_id=regular_user.id,
        )

        # Next one should fail
        with pytest.raises(VersionLimitExceededException):
            await service.create_version(
                document_id=test_document.id,
                file_content=b"v4",
                user_id=regular_user.id,
            )

    @pytest.mark.asyncio
    async def test_get_version_success(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test retrieving a specific version."""
        service = VersionControlService(db_session, str(temp_storage_path))

        # Create version
        created_version = await service.create_version(
            document_id=test_document.id,
            file_content=b"version content",
            user_id=regular_user.id,
        )

        # Retrieve version
        version = await service.get_version(
            test_document.id,
            created_version.version_number
        )

        assert version.id == created_version.id
        assert version.version_number == created_version.version_number

    @pytest.mark.asyncio
    async def test_get_version_not_found(
        self, db_session, test_document, temp_storage_path
    ):
        """Test retrieving non-existent version raises exception."""
        service = VersionControlService(db_session, str(temp_storage_path))

        with pytest.raises(DocumentVersionNotFoundException):
            await service.get_version(test_document.id, 999)

    @pytest.mark.asyncio
    async def test_list_versions(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test listing all versions of a document."""
        service = VersionControlService(db_session, str(temp_storage_path))

        # Create multiple versions
        v1 = await service.create_version(
            document_id=test_document.id,
            file_content=b"v1",
            user_id=regular_user.id,
        )
        v2 = await service.create_version(
            document_id=test_document.id,
            file_content=b"v2",
            user_id=regular_user.id,
        )

        versions = await service.list_versions(test_document.id)

        assert len(versions) >= 2
        version_numbers = [v.version_number for v in versions]
        assert v1.version_number in version_numbers
        assert v2.version_number in version_numbers

    @pytest.mark.asyncio
    async def test_list_versions_ordered_desc(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test that versions are listed in descending order."""
        service = VersionControlService(db_session, str(temp_storage_path))

        # Create versions
        for i in range(3):
            await service.create_version(
                document_id=test_document.id,
                file_content=f"v{i}".encode(),
                user_id=regular_user.id,
            )

        versions = await service.list_versions(test_document.id)

        # Should be in descending order
        for i in range(len(versions) - 1):
            assert versions[i].version_number > versions[i + 1].version_number

    @pytest.mark.asyncio
    async def test_list_versions_with_pagination(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test listing versions with pagination."""
        service = VersionControlService(db_session, str(temp_storage_path))

        # Create multiple versions
        for i in range(5):
            await service.create_version(
                document_id=test_document.id,
                file_content=f"v{i}".encode(),
                user_id=regular_user.id,
            )

        # Get first page
        page1 = await service.list_versions(test_document.id, limit=2, offset=0)
        assert len(page1) == 2

        # Get second page
        page2 = await service.list_versions(test_document.id, limit=2, offset=2)
        assert len(page2) == 2

        # Pages should have different versions
        assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_get_version_content(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test retrieving version content."""
        service = VersionControlService(db_session, str(temp_storage_path))
        content = b"Specific version content"

        version = await service.create_version(
            document_id=test_document.id,
            file_content=content,
            user_id=regular_user.id,
        )

        retrieved_content = await service.get_version_content(
            test_document.id,
            version.version_number
        )

        assert retrieved_content == content

    @pytest.mark.asyncio
    async def test_compare_versions_text_files(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test comparing two text file versions."""
        service = VersionControlService(db_session, str(temp_storage_path))

        # Create two versions with different content
        v1 = await service.create_version(
            document_id=test_document.id,
            file_content=b"Line 1\nLine 2\nLine 3",
            user_id=regular_user.id,
        )
        v2 = await service.create_version(
            document_id=test_document.id,
            file_content=b"Line 1\nLine 2 modified\nLine 3",
            user_id=regular_user.id,
        )

        comparison = await service.compare_versions(
            test_document.id,
            v1.version_number,
            v2.version_number
        )

        assert comparison["document_id"] == test_document.id
        assert comparison["version1"]["number"] == v1.version_number
        assert comparison["version2"]["number"] == v2.version_number
        assert "diff" in comparison
        assert "similarity" in comparison
        assert 0 <= comparison["similarity"] <= 1

    @pytest.mark.asyncio
    async def test_compare_versions_identical(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test comparing identical versions."""
        service = VersionControlService(db_session, str(temp_storage_path))
        content = b"Same content"

        v1 = await service.create_version(
            document_id=test_document.id,
            file_content=content,
            user_id=regular_user.id,
        )
        v2 = await service.create_version(
            document_id=test_document.id,
            file_content=content,
            user_id=regular_user.id,
        )

        comparison = await service.compare_versions(
            test_document.id,
            v1.version_number,
            v2.version_number
        )

        assert comparison["is_identical"] is True
        assert comparison["similarity"] == 1.0

    @pytest.mark.asyncio
    async def test_rollback_to_version(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test rolling back to a previous version."""
        service = VersionControlService(db_session, str(temp_storage_path))

        # Create versions
        v1_content = b"Version 1 content"
        v1 = await service.create_version(
            document_id=test_document.id,
            file_content=v1_content,
            user_id=regular_user.id,
        )
        v2 = await service.create_version(
            document_id=test_document.id,
            file_content=b"Version 2 content",
            user_id=regular_user.id,
        )

        # Rollback to v1
        new_version = await service.rollback_to_version(
            document_id=test_document.id,
            version_number=v1.version_number,
            user_id=regular_user.id,
        )

        # New version should have v1 content
        new_content = await service.get_version_content(
            test_document.id,
            new_version.version_number
        )
        assert new_content == v1_content
        assert "Rollback" in new_version.change_summary

    @pytest.mark.asyncio
    async def test_delete_version(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test deleting a version."""
        service = VersionControlService(db_session, str(temp_storage_path))

        # Create versions
        v1 = await service.create_version(
            document_id=test_document.id,
            file_content=b"v1",
            user_id=regular_user.id,
        )
        v2 = await service.create_version(
            document_id=test_document.id,
            file_content=b"v2",
            user_id=regular_user.id,
        )

        # Delete v1 (not current version)
        await service.delete_version(
            document_id=test_document.id,
            version_number=v1.version_number,
            user_id=regular_user.id,
        )

        # v1 should not be retrievable
        with pytest.raises(DocumentVersionNotFoundException):
            await service.get_version(test_document.id, v1.version_number)

    @pytest.mark.asyncio
    async def test_delete_current_version_fails(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test that deleting current version is not allowed."""
        service = VersionControlService(db_session, str(temp_storage_path))

        with pytest.raises(ValidationException, match="current version"):
            await service.delete_version(
                document_id=test_document.id,
                version_number=test_document.current_version,
                user_id=regular_user.id,
            )

    @pytest.mark.asyncio
    async def test_get_version_diff(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test getting diff between versions."""
        service = VersionControlService(db_session, str(temp_storage_path))

        v1 = await service.create_version(
            document_id=test_document.id,
            file_content=b"Original text",
            user_id=regular_user.id,
        )
        v2 = await service.create_version(
            document_id=test_document.id,
            file_content=b"Modified text",
            user_id=regular_user.id,
        )

        diff = await service.get_version_diff(
            test_document.id,
            v1.version_number,
            v2.version_number
        )

        assert isinstance(diff, list)
        assert len(diff) > 0

    @pytest.mark.asyncio
    async def test_get_change_history(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test getting change history."""
        service = VersionControlService(db_session, str(temp_storage_path))

        # Create versions with summaries
        for i in range(3):
            await service.create_version(
                document_id=test_document.id,
                file_content=f"Version {i}".encode(),
                user_id=regular_user.id,
                change_summary=f"Change {i}",
            )

        history = await service.get_change_history(test_document.id)

        assert len(history) >= 3
        assert all("version_number" in h for h in history)
        assert all("change_summary" in h for h in history)


@pytest.mark.unit
class TestVersionBranchingService:
    """Test version branching and merging functionality."""

    @pytest.mark.asyncio
    async def test_create_branch(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test creating a branch from a version."""
        version_service = VersionControlService(db_session, str(temp_storage_path))
        branching_service = VersionBranchingService(db_session, version_service)

        # Create base version
        base_version = await version_service.create_version(
            document_id=test_document.id,
            file_content=b"Base content",
            user_id=regular_user.id,
        )

        # Create branch
        branch_info = await branching_service.create_branch(
            document_id=test_document.id,
            from_version=base_version.version_number,
            branch_name="feature-branch",
            user_id=regular_user.id,
        )

        assert branch_info["branch_name"] == "feature-branch"
        assert branch_info["source_version"] == base_version.version_number
        assert "branch_version" in branch_info

    @pytest.mark.asyncio
    async def test_merge_versions_latest_strategy(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test merging versions with 'latest' strategy."""
        version_service = VersionControlService(db_session, str(temp_storage_path))
        branching_service = VersionBranchingService(db_session, version_service)

        # Create two versions
        v1 = await version_service.create_version(
            document_id=test_document.id,
            file_content=b"Version 1",
            user_id=regular_user.id,
        )
        v2 = await version_service.create_version(
            document_id=test_document.id,
            file_content=b"Version 2",
            user_id=regular_user.id,
        )

        # Merge with latest strategy
        merged_version = await branching_service.merge_versions(
            document_id=test_document.id,
            base_version=v1.version_number,
            merge_version=v2.version_number,
            user_id=regular_user.id,
            resolution_strategy="latest",
        )

        assert "Merged" in merged_version.change_summary
        # Should use content from later version
        content = await version_service.get_version_content(
            test_document.id,
            merged_version.version_number
        )
        assert content == b"Version 2"

    @pytest.mark.asyncio
    async def test_merge_versions_base_strategy(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test merging versions with 'base' strategy."""
        version_service = VersionControlService(db_session, str(temp_storage_path))
        branching_service = VersionBranchingService(db_session, version_service)

        v1 = await version_service.create_version(
            document_id=test_document.id,
            file_content=b"Base version",
            user_id=regular_user.id,
        )
        v2 = await version_service.create_version(
            document_id=test_document.id,
            file_content=b"Merge version",
            user_id=regular_user.id,
        )

        merged_version = await branching_service.merge_versions(
            document_id=test_document.id,
            base_version=v1.version_number,
            merge_version=v2.version_number,
            user_id=regular_user.id,
            resolution_strategy="base",
        )

        content = await version_service.get_version_content(
            test_document.id,
            merged_version.version_number
        )
        assert content == b"Base version"

    @pytest.mark.asyncio
    async def test_merge_versions_invalid_strategy(
        self, db_session, test_document, regular_user, temp_storage_path
    ):
        """Test that invalid merge strategy raises exception."""
        version_service = VersionControlService(db_session, str(temp_storage_path))
        branching_service = VersionBranchingService(db_session, version_service)

        v1 = await version_service.create_version(
            document_id=test_document.id,
            file_content=b"v1",
            user_id=regular_user.id,
        )

        with pytest.raises(ValidationException):
            await branching_service.merge_versions(
                document_id=test_document.id,
                base_version=v1.version_number,
                merge_version=v1.version_number,
                user_id=regular_user.id,
                resolution_strategy="invalid",
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
