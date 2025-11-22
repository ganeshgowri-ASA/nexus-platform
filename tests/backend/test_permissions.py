"""
Unit tests for permission system.

Tests cover:
- Document permission granting and revoking
- Folder permission management
- Permission inheritance
- Access level hierarchy
- Share link creation and validation
- Permission checking logic
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from modules.documents.permissions import (
    PermissionService,
    ShareLinkService,
    PermissionDeniedException,
    ShareLinkException,
)
from backend.models.document import (
    AccessLevel,
    Document,
    DocumentPermission,
    Folder,
    FolderPermission,
    ShareLink,
    ShareType,
)
from backend.core.exceptions import (
    DocumentNotFoundException,
    FolderNotFoundException,
    ResourceNotFoundException,
)


@pytest.mark.unit
class TestPermissionService:
    """Test permission service functionality."""

    @pytest.mark.asyncio
    async def test_grant_document_permission_success(
        self, db_session, test_document, regular_user, other_user
    ):
        """Test successfully granting document permission."""
        service = PermissionService(db_session)

        permission = await service.grant_document_permission(
            document_id=test_document.id,
            user_id=other_user.id,
            access_level=AccessLevel.EDIT,
            granted_by_id=regular_user.id,
        )

        assert permission.document_id == test_document.id
        assert permission.user_id == other_user.id
        assert permission.access_level == AccessLevel.EDIT
        assert permission.granted_by_id == regular_user.id

    @pytest.mark.asyncio
    async def test_grant_permission_with_expiration(
        self, db_session, test_document, regular_user, other_user
    ):
        """Test granting permission with expiration date."""
        service = PermissionService(db_session)
        expires_at = datetime.utcnow() + timedelta(days=7)

        permission = await service.grant_document_permission(
            document_id=test_document.id,
            user_id=other_user.id,
            access_level=AccessLevel.VIEW,
            granted_by_id=regular_user.id,
            expires_at=expires_at,
        )

        assert permission.expires_at is not None
        assert permission.expires_at > datetime.utcnow()

    @pytest.mark.asyncio
    async def test_grant_permission_updates_existing(
        self, db_session, test_document, regular_user, other_user
    ):
        """Test that granting permission updates existing one."""
        service = PermissionService(db_session)

        # Grant initial permission
        perm1 = await service.grant_document_permission(
            document_id=test_document.id,
            user_id=other_user.id,
            access_level=AccessLevel.VIEW,
            granted_by_id=regular_user.id,
        )

        # Grant again with different level
        perm2 = await service.grant_document_permission(
            document_id=test_document.id,
            user_id=other_user.id,
            access_level=AccessLevel.ADMIN,
            granted_by_id=regular_user.id,
        )

        # Should be same permission, updated
        assert perm1.id == perm2.id
        assert perm2.access_level == AccessLevel.ADMIN

    @pytest.mark.asyncio
    async def test_grant_permission_nonexistent_document(
        self, db_session, regular_user, other_user
    ):
        """Test granting permission to non-existent document fails."""
        service = PermissionService(db_session)

        with pytest.raises(DocumentNotFoundException):
            await service.grant_document_permission(
                document_id=99999,
                user_id=other_user.id,
                access_level=AccessLevel.VIEW,
                granted_by_id=regular_user.id,
            )

    @pytest.mark.asyncio
    async def test_grant_permission_requires_admin_access(
        self, db_session, test_document, other_user
    ):
        """Test that granting permission requires admin access."""
        service = PermissionService(db_session)

        # other_user doesn't have admin access to test_document
        with pytest.raises(PermissionDeniedException):
            await service.grant_document_permission(
                document_id=test_document.id,
                user_id=other_user.id,
                access_level=AccessLevel.VIEW,
                granted_by_id=other_user.id,  # Non-admin trying to grant
            )

    @pytest.mark.asyncio
    async def test_revoke_document_permission_success(
        self, db_session, document_with_permission, regular_user, other_user
    ):
        """Test successfully revoking document permission."""
        test_document, permission = document_with_permission
        service = PermissionService(db_session)

        await service.revoke_document_permission(
            document_id=test_document.id,
            user_id=other_user.id,
            revoked_by_id=regular_user.id,
        )

        # Permission should be deleted
        db_session.expire_all()
        result = await db_session.get(DocumentPermission, permission.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_revoke_permission_requires_admin(
        self, db_session, document_with_permission, other_user
    ):
        """Test that revoking permission requires admin access."""
        test_document, permission = document_with_permission
        service = PermissionService(db_session)

        with pytest.raises(PermissionDeniedException):
            await service.revoke_document_permission(
                document_id=test_document.id,
                user_id=other_user.id,
                revoked_by_id=other_user.id,  # Non-admin trying to revoke
            )

    @pytest.mark.asyncio
    async def test_check_document_permission_owner(
        self, db_session, test_document, regular_user
    ):
        """Test that document owner has all permissions."""
        service = PermissionService(db_session)

        has_permission = await service.check_document_permission(
            document_id=test_document.id,
            user_id=regular_user.id,  # Owner
            required_level=AccessLevel.ADMIN,
        )

        assert has_permission is True

    @pytest.mark.asyncio
    async def test_check_document_permission_public_view(
        self, db_session, public_document, other_user
    ):
        """Test that public documents allow view access."""
        service = PermissionService(db_session)

        has_permission = await service.check_document_permission(
            document_id=public_document.id,
            user_id=other_user.id,
            required_level=AccessLevel.VIEW,
        )

        assert has_permission is True

    @pytest.mark.asyncio
    async def test_check_document_permission_public_no_edit(
        self, db_session, public_document, other_user
    ):
        """Test that public documents don't allow edit without explicit permission."""
        service = PermissionService(db_session)

        has_permission = await service.check_document_permission(
            document_id=public_document.id,
            user_id=other_user.id,
            required_level=AccessLevel.EDIT,
        )

        assert has_permission is False

    @pytest.mark.asyncio
    async def test_check_document_permission_granted(
        self, db_session, document_with_permission, other_user
    ):
        """Test checking explicitly granted permission."""
        test_document, permission = document_with_permission
        service = PermissionService(db_session)

        has_permission = await service.check_document_permission(
            document_id=test_document.id,
            user_id=other_user.id,
            required_level=AccessLevel.EDIT,
        )

        assert has_permission is True

    @pytest.mark.asyncio
    async def test_check_document_permission_expired(
        self, db_session, test_document, regular_user, other_user
    ):
        """Test that expired permissions are not valid."""
        service = PermissionService(db_session)

        # Grant expired permission
        expired_time = datetime.utcnow() - timedelta(days=1)
        await service.grant_document_permission(
            document_id=test_document.id,
            user_id=other_user.id,
            access_level=AccessLevel.EDIT,
            granted_by_id=regular_user.id,
            expires_at=expired_time,
        )

        has_permission = await service.check_document_permission(
            document_id=test_document.id,
            user_id=other_user.id,
            required_level=AccessLevel.EDIT,
        )

        assert has_permission is False

    @pytest.mark.asyncio
    async def test_get_document_access_level_owner(
        self, db_session, test_document, regular_user
    ):
        """Test getting access level for document owner."""
        service = PermissionService(db_session)

        access_level = await service.get_document_access_level(
            document_id=test_document.id,
            user_id=regular_user.id,
        )

        assert access_level == AccessLevel.ADMIN

    @pytest.mark.asyncio
    async def test_get_document_access_level_public(
        self, db_session, public_document, other_user
    ):
        """Test getting access level for public document."""
        service = PermissionService(db_session)

        access_level = await service.get_document_access_level(
            document_id=public_document.id,
            user_id=other_user.id,
        )

        assert access_level == AccessLevel.VIEW

    @pytest.mark.asyncio
    async def test_get_document_access_level_none(
        self, db_session, test_document, other_user
    ):
        """Test getting access level when user has no access."""
        service = PermissionService(db_session)

        access_level = await service.get_document_access_level(
            document_id=test_document.id,
            user_id=other_user.id,
        )

        assert access_level == AccessLevel.NONE

    @pytest.mark.asyncio
    async def test_list_document_permissions(
        self, db_session, document_with_permission, regular_user
    ):
        """Test listing all permissions for a document."""
        test_document, permission = document_with_permission
        service = PermissionService(db_session)

        permissions = await service.list_document_permissions(
            document_id=test_document.id
        )

        assert len(permissions) >= 1
        assert any(p.id == permission.id for p in permissions)

    @pytest.mark.asyncio
    async def test_list_user_documents(
        self, db_session, test_document, public_document, regular_user
    ):
        """Test listing all documents accessible to user."""
        service = PermissionService(db_session)

        documents = await service.list_user_documents(
            user_id=regular_user.id,
            min_access_level=AccessLevel.VIEW,
        )

        # Should include owned and public documents
        doc_ids = [d.id for d in documents]
        assert test_document.id in doc_ids
        assert public_document.id in doc_ids

    @pytest.mark.asyncio
    async def test_access_level_hierarchy(self):
        """Test that access level hierarchy is correctly defined."""
        service = PermissionService(MagicMock())

        assert service.ACCESS_HIERARCHY[AccessLevel.NONE] < \
               service.ACCESS_HIERARCHY[AccessLevel.VIEW]
        assert service.ACCESS_HIERARCHY[AccessLevel.VIEW] < \
               service.ACCESS_HIERARCHY[AccessLevel.COMMENT]
        assert service.ACCESS_HIERARCHY[AccessLevel.COMMENT] < \
               service.ACCESS_HIERARCHY[AccessLevel.EDIT]
        assert service.ACCESS_HIERARCHY[AccessLevel.EDIT] < \
               service.ACCESS_HIERARCHY[AccessLevel.ADMIN]


@pytest.mark.unit
class TestFolderPermissions:
    """Test folder permission functionality."""

    @pytest.mark.asyncio
    async def test_grant_folder_permission(
        self, db_session, test_folder, regular_user, other_user
    ):
        """Test granting folder permission."""
        service = PermissionService(db_session)

        permission = await service.grant_folder_permission(
            folder_id=test_folder.id,
            user_id=other_user.id,
            access_level=AccessLevel.EDIT,
            granted_by_id=regular_user.id,
        )

        assert permission.folder_id == test_folder.id
        assert permission.user_id == other_user.id
        assert permission.access_level == AccessLevel.EDIT

    @pytest.mark.asyncio
    async def test_check_folder_permission_owner(
        self, db_session, test_folder, regular_user
    ):
        """Test that folder owner has all permissions."""
        service = PermissionService(db_session)

        has_permission = await service.check_folder_permission(
            folder_id=test_folder.id,
            user_id=regular_user.id,
            required_level=AccessLevel.ADMIN,
        )

        assert has_permission is True

    @pytest.mark.asyncio
    async def test_get_folder_access_level(
        self, db_session, test_folder, regular_user
    ):
        """Test getting folder access level."""
        service = PermissionService(db_session)

        access_level = await service.get_folder_access_level(
            folder_id=test_folder.id,
            user_id=regular_user.id,
        )

        assert access_level == AccessLevel.ADMIN


@pytest.mark.unit
class TestShareLinkService:
    """Test share link service functionality."""

    @pytest.mark.asyncio
    async def test_create_share_link_success(
        self, db_session, test_document, regular_user
    ):
        """Test creating share link successfully."""
        perm_service = PermissionService(db_session)
        service = ShareLinkService(db_session, perm_service)

        share_link = await service.create_share_link(
            document_id=test_document.id,
            created_by_id=regular_user.id,
            access_level=AccessLevel.VIEW,
        )

        assert share_link.document_id == test_document.id
        assert share_link.created_by_id == regular_user.id
        assert share_link.access_level == AccessLevel.VIEW
        assert len(share_link.token) == 32

    @pytest.mark.asyncio
    async def test_create_share_link_with_password(
        self, db_session, test_document, regular_user
    ):
        """Test creating password-protected share link."""
        perm_service = PermissionService(db_session)
        service = ShareLinkService(db_session, perm_service)

        share_link = await service.create_share_link(
            document_id=test_document.id,
            created_by_id=regular_user.id,
            password="SecurePass123!",
        )

        assert share_link.password_hash is not None
        assert share_link.password_hash != "SecurePass123!"

    @pytest.mark.asyncio
    async def test_create_share_link_with_expiration(
        self, db_session, test_document, regular_user
    ):
        """Test creating share link with expiration."""
        perm_service = PermissionService(db_session)
        service = ShareLinkService(db_session, perm_service)

        share_link = await service.create_share_link(
            document_id=test_document.id,
            created_by_id=regular_user.id,
            expires_in_days=7,
        )

        assert share_link.expires_at is not None
        assert share_link.expires_at > datetime.utcnow()

    @pytest.mark.asyncio
    async def test_create_share_link_with_max_downloads(
        self, db_session, test_document, regular_user
    ):
        """Test creating share link with download limit."""
        perm_service = PermissionService(db_session)
        service = ShareLinkService(db_session, perm_service)

        share_link = await service.create_share_link(
            document_id=test_document.id,
            created_by_id=regular_user.id,
            max_downloads=5,
        )

        assert share_link.max_downloads == 5
        assert share_link.download_count == 0

    @pytest.mark.asyncio
    async def test_create_share_link_requires_edit_permission(
        self, db_session, test_document, other_user
    ):
        """Test that creating share link requires edit permission."""
        perm_service = PermissionService(db_session)
        service = ShareLinkService(db_session, perm_service)

        with pytest.raises(PermissionDeniedException):
            await service.create_share_link(
                document_id=test_document.id,
                created_by_id=other_user.id,  # No permission
            )

    @pytest.mark.asyncio
    async def test_get_share_link(
        self, db_session, test_document, regular_user
    ):
        """Test retrieving share link by token."""
        perm_service = PermissionService(db_session)
        service = ShareLinkService(db_session, perm_service)

        # Create link
        created_link = await service.create_share_link(
            document_id=test_document.id,
            created_by_id=regular_user.id,
        )

        # Retrieve link
        retrieved_link = await service.get_share_link(created_link.token)

        assert retrieved_link.id == created_link.id
        assert retrieved_link.token == created_link.token

    @pytest.mark.asyncio
    async def test_get_share_link_expired(
        self, db_session, test_document, regular_user
    ):
        """Test that expired share links raise exception."""
        perm_service = PermissionService(db_session)
        service = ShareLinkService(db_session, perm_service)

        # Create expired link
        share_link = await service.create_share_link(
            document_id=test_document.id,
            created_by_id=regular_user.id,
            expires_in_days=-1,  # Already expired
        )

        with pytest.raises(ShareLinkException, match="expired"):
            await service.get_share_link(share_link.token)

    @pytest.mark.asyncio
    async def test_get_share_link_download_limit_reached(
        self, db_session, test_document, regular_user
    ):
        """Test that share link with reached download limit raises exception."""
        perm_service = PermissionService(db_session)
        service = ShareLinkService(db_session, perm_service)

        # Create link with limit
        share_link = await service.create_share_link(
            document_id=test_document.id,
            created_by_id=regular_user.id,
            max_downloads=1,
        )

        # Reach limit
        share_link.download_count = 1
        db_session.commit()

        with pytest.raises(ShareLinkException, match="limit reached"):
            await service.get_share_link(share_link.token)

    @pytest.mark.asyncio
    async def test_verify_share_link_password(
        self, db_session, test_document, regular_user
    ):
        """Test verifying share link password."""
        perm_service = PermissionService(db_session)
        service = ShareLinkService(db_session, perm_service)

        password = "MySecurePassword123!"
        share_link = await service.create_share_link(
            document_id=test_document.id,
            created_by_id=regular_user.id,
            password=password,
        )

        # Correct password
        is_valid = await service.verify_share_link_password(
            share_link.token,
            password
        )
        assert is_valid is True

        # Wrong password
        is_valid = await service.verify_share_link_password(
            share_link.token,
            "WrongPassword"
        )
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_increment_download_count(
        self, db_session, test_document, regular_user
    ):
        """Test incrementing share link download count."""
        perm_service = PermissionService(db_session)
        service = ShareLinkService(db_session, perm_service)

        share_link = await service.create_share_link(
            document_id=test_document.id,
            created_by_id=regular_user.id,
        )

        initial_count = share_link.download_count

        await service.increment_download_count(share_link.token)

        db_session.refresh(share_link)
        assert share_link.download_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_revoke_share_link(
        self, db_session, test_document, regular_user
    ):
        """Test revoking share link."""
        perm_service = PermissionService(db_session)
        service = ShareLinkService(db_session, perm_service)

        share_link = await service.create_share_link(
            document_id=test_document.id,
            created_by_id=regular_user.id,
        )

        await service.revoke_share_link(
            share_link.token,
            revoked_by_id=regular_user.id,
        )

        # Link should be deleted
        with pytest.raises(ResourceNotFoundException):
            await service.get_share_link(share_link.token)

    @pytest.mark.asyncio
    async def test_list_document_share_links(
        self, db_session, test_document, regular_user
    ):
        """Test listing all share links for a document."""
        perm_service = PermissionService(db_session)
        service = ShareLinkService(db_session, perm_service)

        # Create multiple links
        link1 = await service.create_share_link(
            document_id=test_document.id,
            created_by_id=regular_user.id,
        )
        link2 = await service.create_share_link(
            document_id=test_document.id,
            created_by_id=regular_user.id,
        )

        links = await service.list_document_share_links(test_document.id)

        assert len(links) >= 2
        tokens = [link.token for link in links]
        assert link1.token in tokens
        assert link2.token in tokens


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
