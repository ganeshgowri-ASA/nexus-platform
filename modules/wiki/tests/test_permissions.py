"""
Unit Tests for Wiki Permissions Service

Tests for access control, permission inheritance, role-based permissions,
and permission management functionality.

Author: NEXUS Platform Team
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from modules.wiki.permissions import PermissionService
from modules.wiki.models import WikiPage, WikiCategory, WikiPermission
from modules.wiki.wiki_types import PermissionLevel


class TestPagePermissions:
    """Tests for page-level permissions."""

    def test_grant_page_permission_to_user(self, db_session: Session, sample_page, mock_user):
        """Test granting page permission to a user."""
        service = PermissionService(db_session)

        perm = service.grant_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )

        assert perm is not None
        assert perm.page_id == sample_page.id
        assert perm.user_id == mock_user['id']
        assert perm.permission_level == PermissionLevel.EDIT

    def test_grant_page_permission_to_role(self, db_session: Session, sample_page, mock_user):
        """Test granting page permission to a role."""
        service = PermissionService(db_session)

        perm = service.grant_page_permission(
            page_id=sample_page.id,
            role='editor',
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )

        assert perm is not None
        assert perm.page_id == sample_page.id
        assert perm.role == 'editor'
        assert perm.permission_level == PermissionLevel.EDIT

    def test_grant_permission_both_user_and_role_fails(self, db_session: Session, sample_page, mock_user):
        """Test that providing both user_id and role raises error."""
        service = PermissionService(db_session)

        with pytest.raises(ValueError, match='either user_id or role'):
            service.grant_page_permission(
                page_id=sample_page.id,
                user_id=mock_user['id'],
                role='editor',
                permission_level=PermissionLevel.EDIT,
                granted_by=mock_user['id']
            )

    def test_grant_permission_neither_user_nor_role_fails(self, db_session: Session, sample_page, mock_user):
        """Test that providing neither user_id nor role raises error."""
        service = PermissionService(db_session)

        with pytest.raises(ValueError, match='either user_id or role'):
            service.grant_page_permission(
                page_id=sample_page.id,
                permission_level=PermissionLevel.EDIT,
                granted_by=mock_user['id']
            )

    def test_update_existing_permission(self, db_session: Session, sample_page, mock_user):
        """Test updating an existing permission."""
        service = PermissionService(db_session)

        # Grant initial permission
        perm1 = service.grant_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.READ,
            granted_by=mock_user['id']
        )

        # Grant again with different level
        perm2 = service.grant_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.ADMIN,
            granted_by=mock_user['id']
        )

        # Should update existing permission
        assert perm2.id == perm1.id
        assert perm2.permission_level == PermissionLevel.ADMIN

    def test_grant_permission_with_expiration(self, db_session: Session, sample_page, mock_user):
        """Test granting permission with expiration date."""
        service = PermissionService(db_session)
        expires_at = datetime.utcnow() + timedelta(days=30)

        perm = service.grant_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id'],
            expires_at=expires_at
        )

        assert perm.expires_at is not None
        assert perm.expires_at == expires_at


class TestPermissionRevocation:
    """Tests for revoking permissions."""

    def test_revoke_user_permission(self, db_session: Session, sample_page, mock_user):
        """Test revoking permission from a user."""
        service = PermissionService(db_session)

        # Grant permission
        service.grant_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )

        # Revoke it
        success = service.revoke_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id']
        )

        assert success

        # Verify it's gone
        perms = service.get_page_permissions(sample_page.id)
        assert not any(p.user_id == mock_user['id'] for p in perms)

    def test_revoke_role_permission(self, db_session: Session, sample_page, mock_user):
        """Test revoking permission from a role."""
        service = PermissionService(db_session)

        # Grant permission
        service.grant_page_permission(
            page_id=sample_page.id,
            role='editor',
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )

        # Revoke it
        success = service.revoke_page_permission(
            page_id=sample_page.id,
            role='editor'
        )

        assert success

    def test_revoke_nonexistent_permission(self, db_session: Session, sample_page, mock_user):
        """Test revoking a non-existent permission."""
        service = PermissionService(db_session)

        success = service.revoke_page_permission(
            page_id=sample_page.id,
            user_id=99999
        )

        assert not success


class TestPermissionChecking:
    """Tests for checking permissions."""

    def test_check_page_permission_user_has_access(self, db_session: Session, sample_page, mock_user):
        """Test checking permission when user has access."""
        service = PermissionService(db_session)

        # Grant permission
        service.grant_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )

        # Check permission
        has_permission = service.check_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            required_level=PermissionLevel.EDIT
        )

        assert has_permission

    def test_check_page_permission_user_lacks_access(self, db_session: Session, sample_page, mock_user):
        """Test checking permission when user lacks sufficient access."""
        service = PermissionService(db_session)

        # Grant READ permission
        service.grant_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.READ,
            granted_by=mock_user['id']
        )

        # Check for ADMIN permission
        has_permission = service.check_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            required_level=PermissionLevel.ADMIN
        )

        assert not has_permission

    def test_check_permission_via_role(self, db_session: Session, sample_page, mock_user):
        """Test checking permission granted via role."""
        service = PermissionService(db_session)

        # Grant permission to role
        service.grant_page_permission(
            page_id=sample_page.id,
            role='editor',
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )

        # Check permission with user having that role
        has_permission = service.check_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            required_level=PermissionLevel.EDIT,
            user_roles=['editor']
        )

        assert has_permission

    def test_permission_hierarchy(self, db_session: Session, sample_page, mock_user):
        """Test that higher permissions grant lower ones."""
        service = PermissionService(db_session)

        # Grant ADMIN permission
        service.grant_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.ADMIN,
            granted_by=mock_user['id']
        )

        # Should also have EDIT and READ permissions
        can_edit = service.check_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            required_level=PermissionLevel.EDIT
        )

        can_read = service.check_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            required_level=PermissionLevel.READ
        )

        assert can_edit
        assert can_read

    def test_expired_permission_not_granted(self, db_session: Session, sample_page, mock_user):
        """Test that expired permissions are not granted."""
        service = PermissionService(db_session)

        # Grant permission that already expired
        expired = datetime.utcnow() - timedelta(days=1)
        service.grant_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id'],
            expires_at=expired
        )

        # Check permission
        has_permission = service.check_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            required_level=PermissionLevel.EDIT
        )

        assert not has_permission


class TestEffectivePermissions:
    """Tests for determining effective permissions."""

    def test_get_effective_permission_user_direct(self, db_session: Session, sample_page, mock_user):
        """Test getting effective permission from direct user grant."""
        service = PermissionService(db_session)

        service.grant_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )

        level = service.get_effective_permission(
            page_id=sample_page.id,
            user_id=mock_user['id']
        )

        assert level == PermissionLevel.EDIT

    def test_get_effective_permission_via_role(self, db_session: Session, sample_page, mock_user):
        """Test getting effective permission via role."""
        service = PermissionService(db_session)

        service.grant_page_permission(
            page_id=sample_page.id,
            role='editor',
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )

        level = service.get_effective_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            user_roles=['editor']
        )

        assert level == PermissionLevel.EDIT

    def test_effective_permission_highest_role(self, db_session: Session, sample_page, mock_user):
        """Test that highest permission from multiple roles is used."""
        service = PermissionService(db_session)

        # Grant different permissions to different roles
        service.grant_page_permission(
            page_id=sample_page.id,
            role='viewer',
            permission_level=PermissionLevel.READ,
            granted_by=mock_user['id']
        )

        service.grant_page_permission(
            page_id=sample_page.id,
            role='editor',
            permission_level=PermissionLevel.ADMIN,
            granted_by=mock_user['id']
        )

        level = service.get_effective_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            user_roles=['viewer', 'editor']
        )

        # Should get highest permission
        assert level == PermissionLevel.ADMIN

    def test_effective_permission_user_overrides_role(self, db_session: Session, sample_page, mock_user):
        """Test that direct user permission takes precedence over role."""
        service = PermissionService(db_session)

        # Grant READ to role
        service.grant_page_permission(
            page_id=sample_page.id,
            role='viewer',
            permission_level=PermissionLevel.READ,
            granted_by=mock_user['id']
        )

        # Grant ADMIN directly to user
        service.grant_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.ADMIN,
            granted_by=mock_user['id']
        )

        level = service.get_effective_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            user_roles=['viewer']
        )

        assert level == PermissionLevel.ADMIN


class TestCategoryPermissions:
    """Tests for category-level permissions."""

    def test_grant_category_permission(self, db_session: Session, sample_category, mock_user):
        """Test granting permission to a category."""
        service = PermissionService(db_session)

        perm = service.grant_category_permission(
            category_id=sample_category.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )

        assert perm is not None
        assert perm.category_id == sample_category.id
        assert perm.permission_level == PermissionLevel.EDIT

    def test_get_category_permission_user(self, db_session: Session, sample_category, mock_user):
        """Test getting category permission for a user."""
        service = PermissionService(db_session)

        service.grant_category_permission(
            category_id=sample_category.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )

        level = service.get_category_permission(
            category_id=sample_category.id,
            user_id=mock_user['id']
        )

        assert level == PermissionLevel.EDIT

    def test_category_permission_inheritance(self, db_session: Session, category_factory, mock_user):
        """Test that category permissions inherit from parent."""
        service = PermissionService(db_session)

        parent = category_factory(name='Parent')
        child = category_factory(name='Child', slug='child', parent_id=parent.id)

        # Grant permission on parent
        service.grant_category_permission(
            category_id=parent.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )

        # Check permission on child
        level = service.get_category_permission(
            category_id=child.id,
            user_id=mock_user['id']
        )

        # Should inherit from parent
        assert level == PermissionLevel.EDIT

    def test_page_inherits_category_permission(self, db_session: Session, page_factory, category_factory, mock_user):
        """Test that pages inherit permissions from their category."""
        service = PermissionService(db_session)

        category = category_factory(name='Category')

        # Grant permission on category
        service.grant_category_permission(
            category_id=category.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )

        # Create page in category
        page = page_factory(
            title='Page',
            content='Content',
            category_id=category.id
        )

        # Check effective permission on page
        level = service.get_effective_permission(
            page_id=page.id,
            user_id=mock_user['id']
        )

        # Should inherit from category
        assert level == PermissionLevel.EDIT


class TestNamespacePermissions:
    """Tests for namespace-based permissions."""

    def test_check_namespace_permission_public(self, db_session: Session, mock_user):
        """Test that public namespaces are accessible."""
        service = PermissionService(db_session)

        has_permission = service.check_namespace_permission(
            namespace='docs',
            user_id=mock_user['id'],
            required_level=PermissionLevel.READ
        )

        assert has_permission

    def test_check_namespace_permission_private(self, db_session: Session, mock_user):
        """Test that private namespaces require admin role."""
        service = PermissionService(db_session)

        # User without admin role
        has_permission = service.check_namespace_permission(
            namespace='private',
            user_id=mock_user['id'],
            required_level=PermissionLevel.READ,
            user_roles=['member']
        )

        assert not has_permission

        # User with admin role
        has_permission_admin = service.check_namespace_permission(
            namespace='private',
            user_id=mock_user['id'],
            required_level=PermissionLevel.READ,
            user_roles=['admin']
        )

        assert has_permission_admin


class TestBulkPermissionOperations:
    """Tests for bulk permission operations."""

    def test_copy_permissions(self, db_session: Session, page_factory, mock_user, mock_admin_user):
        """Test copying permissions from one page to another."""
        service = PermissionService(db_session)

        source = page_factory(title='Source')
        target = page_factory(title='Target', slug='target')

        # Grant permissions on source
        service.grant_page_permission(
            page_id=source.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_admin_user['id']
        )

        service.grant_page_permission(
            page_id=source.id,
            role='viewer',
            permission_level=PermissionLevel.READ,
            granted_by=mock_admin_user['id']
        )

        # Copy to target
        count = service.copy_permissions(
            source_page_id=source.id,
            target_page_id=target.id,
            granted_by=mock_admin_user['id']
        )

        assert count == 2

        # Verify permissions were copied
        target_perms = service.get_page_permissions(target.id)
        assert len(target_perms) == 2

    def test_get_user_accessible_pages(self, db_session: Session, page_factory, mock_user):
        """Test getting all pages accessible to a user."""
        service = PermissionService(db_session)

        # Create pages with permissions
        page1 = page_factory(title='Page 1')
        page2 = page_factory(title='Page 2', slug='page-2')
        page3 = page_factory(title='Page 3', slug='page-3')

        service.grant_page_permission(
            page_id=page1.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.READ,
            granted_by=mock_user['id']
        )

        service.grant_page_permission(
            page_id=page2.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )

        # page3 has no permissions

        pages = service.get_user_accessible_pages(
            user_id=mock_user['id'],
            min_level=PermissionLevel.READ
        )

        page_ids = [p.id for p in pages]
        assert page1.id in page_ids
        assert page2.id in page_ids

    def test_get_user_accessible_pages_via_role(self, db_session: Session, page_factory, mock_user):
        """Test getting accessible pages via role permissions."""
        service = PermissionService(db_session)

        page = page_factory(title='Page')

        service.grant_page_permission(
            page_id=page.id,
            role='editor',
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )

        pages = service.get_user_accessible_pages(
            user_id=mock_user['id'],
            user_roles=['editor']
        )

        assert any(p.id == page.id for p in pages)


class TestPermissionAuditing:
    """Tests for permission auditing."""

    def test_audit_permissions_for_page(self, db_session: Session, sample_page, mock_user, mock_admin_user):
        """Test auditing permissions for a specific page."""
        service = PermissionService(db_session)

        # Create some permissions
        service.grant_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_admin_user['id']
        )

        audit = service.audit_permissions(page_id=sample_page.id)

        assert len(audit) > 0
        assert all('page_id' in record for record in audit)
        assert all(record['page_id'] == sample_page.id for record in audit)

    def test_audit_permissions_for_user(self, db_session: Session, page_factory, mock_user):
        """Test auditing permissions for a specific user."""
        service = PermissionService(db_session)

        page1 = page_factory(title='Page 1')
        page2 = page_factory(title='Page 2', slug='page-2')

        service.grant_page_permission(
            page_id=page1.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )

        service.grant_page_permission(
            page_id=page2.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.READ,
            granted_by=mock_user['id']
        )

        audit = service.audit_permissions(user_id=mock_user['id'])

        assert len(audit) >= 2
        assert all(record['user_id'] == mock_user['id'] for record in audit)

    def test_audit_detects_expired_permissions(self, db_session: Session, sample_page, mock_user):
        """Test that audit detects expired permissions."""
        service = PermissionService(db_session)

        # Create expired permission
        expired = datetime.utcnow() - timedelta(days=1)
        service.grant_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id'],
            expires_at=expired
        )

        audit = service.audit_permissions(page_id=sample_page.id)

        assert any(record['is_expired'] for record in audit)

    def test_cleanup_expired_permissions(self, db_session: Session, page_factory, mock_user):
        """Test cleaning up expired permissions."""
        service = PermissionService(db_session)

        page = page_factory(title='Page')

        # Create expired permission
        expired = datetime.utcnow() - timedelta(days=1)
        service.grant_page_permission(
            page_id=page.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id'],
            expires_at=expired
        )

        # Create non-expired permission
        future = datetime.utcnow() + timedelta(days=30)
        service.grant_page_permission(
            page_id=page.id,
            role='editor',
            permission_level=PermissionLevel.READ,
            granted_by=mock_user['id'],
            expires_at=future
        )

        # Cleanup
        removed = service.cleanup_expired_permissions()

        assert removed >= 1

        # Verify only non-expired remains
        perms = service.get_page_permissions(page.id)
        assert all(p.expires_at is None or p.expires_at > datetime.utcnow() for p in perms)


class TestPermissionRetrievalMarked:
    """Tests for retrieving permissions."""

    @pytest.mark.permissions
    def test_get_page_permissions_all(self, db_session: Session, sample_page, mock_user):
        """Test getting all permissions for a page."""
        service = PermissionService(db_session)

        # Create multiple permissions
        service.grant_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )

        service.grant_page_permission(
            page_id=sample_page.id,
            role='viewer',
            permission_level=PermissionLevel.READ,
            granted_by=mock_user['id']
        )

        perms = service.get_page_permissions(sample_page.id)

        assert len(perms) >= 2

    @pytest.mark.permissions
    def test_get_page_permissions_exclude_inherited(self, db_session: Session, sample_page, mock_user):
        """Test getting only direct permissions (excluding inherited)."""
        service = PermissionService(db_session)

        # Create direct permission
        direct_perm = service.grant_page_permission(
            page_id=sample_page.id,
            user_id=mock_user['id'],
            permission_level=PermissionLevel.EDIT,
            granted_by=mock_user['id']
        )
        direct_perm.is_inherited = False

        # Create inherited permission (simulated)
        inherited_perm = WikiPermission(
            page_id=sample_page.id,
            role='viewer',
            permission_level=PermissionLevel.READ,
            granted_by=mock_user['id'],
            is_inherited=True
        )
        db_session.add(inherited_perm)
        db_session.commit()

        # Get only non-inherited
        perms = service.get_page_permissions(sample_page.id, include_inherited=False)

        assert all(not p.is_inherited for p in perms)
