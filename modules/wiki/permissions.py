"""
Wiki Permissions Service

Comprehensive access control for the NEXUS Wiki System including:
- Page-level permissions
- Category-level permissions
- Namespace access control
- Role-based permissions
- Permission inheritance
- Read/write/admin controls

Author: NEXUS Platform Team
"""

from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.utils import get_logger
from modules.wiki.models import WikiPage, WikiCategory, WikiPermission
from modules.wiki.wiki_types import PermissionLevel, ChangeType

logger = get_logger(__name__)


class PermissionService:
    """Manages access control and permissions for wiki content."""

    def __init__(self, db: Session):
        """
        Initialize PermissionService.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    # ========================================================================
    # PAGE PERMISSIONS
    # ========================================================================

    def grant_page_permission(
        self,
        page_id: int,
        user_id: Optional[int] = None,
        role: Optional[str] = None,
        permission_level: PermissionLevel = PermissionLevel.READ,
        granted_by: int = 1,
        expires_at: Optional[datetime] = None
    ) -> Optional[WikiPermission]:
        """
        Grant permission to a page for a user or role.

        Args:
            page_id: Page ID
            user_id: User ID (mutually exclusive with role)
            role: Role name (mutually exclusive with user_id)
            permission_level: Permission level to grant
            granted_by: User ID who granted the permission
            expires_at: Optional expiration datetime

        Returns:
            Created WikiPermission instance

        Example:
            >>> service = PermissionService(db)
            >>> perm = service.grant_page_permission(
            ...     page_id=123,
            ...     user_id=5,
            ...     permission_level=PermissionLevel.EDIT,
            ...     granted_by=1
            ... )
        """
        try:
            # Validate that either user_id or role is provided, not both
            if (user_id is None and role is None) or (user_id is not None and role is not None):
                raise ValueError("Must provide either user_id or role, not both")

            # Check if permission already exists
            existing = self.db.query(WikiPermission).filter(
                WikiPermission.page_id == page_id
            )

            if user_id:
                existing = existing.filter(WikiPermission.user_id == user_id)
            else:
                existing = existing.filter(WikiPermission.role == role)

            existing_perm = existing.first()

            if existing_perm:
                # Update existing permission
                existing_perm.permission_level = permission_level
                existing_perm.granted_by = granted_by
                existing_perm.granted_at = datetime.utcnow()
                existing_perm.expires_at = expires_at
                self.db.commit()
                self.db.refresh(existing_perm)
                logger.info(f"Updated permission for page {page_id}")
                return existing_perm

            # Create new permission
            permission = WikiPermission(
                page_id=page_id,
                user_id=user_id,
                role=role,
                permission_level=permission_level,
                granted_by=granted_by,
                expires_at=expires_at,
                is_inherited=False
            )

            self.db.add(permission)
            self.db.commit()
            self.db.refresh(permission)

            logger.info(
                f"Granted {permission_level.value} permission on page {page_id} "
                f"to {'user ' + str(user_id) if user_id else 'role ' + role}"
            )
            return permission

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error granting page permission: {str(e)}")
            raise

    def revoke_page_permission(
        self,
        page_id: int,
        user_id: Optional[int] = None,
        role: Optional[str] = None
    ) -> bool:
        """
        Revoke permission from a page.

        Args:
            page_id: Page ID
            user_id: User ID
            role: Role name

        Returns:
            True if successful

        Example:
            >>> success = service.revoke_page_permission(123, user_id=5)
        """
        try:
            query = self.db.query(WikiPermission).filter(
                WikiPermission.page_id == page_id
            )

            if user_id:
                query = query.filter(WikiPermission.user_id == user_id)
            elif role:
                query = query.filter(WikiPermission.role == role)
            else:
                return False

            deleted = query.delete()
            self.db.commit()

            logger.info(f"Revoked permission from page {page_id}")
            return deleted > 0

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error revoking page permission: {str(e)}")
            return False

    def get_page_permissions(
        self,
        page_id: int,
        include_inherited: bool = True
    ) -> List[WikiPermission]:
        """
        Get all permissions for a page.

        Args:
            page_id: Page ID
            include_inherited: Include inherited permissions

        Returns:
            List of WikiPermission instances

        Example:
            >>> perms = service.get_page_permissions(123)
        """
        try:
            query = self.db.query(WikiPermission).filter(
                WikiPermission.page_id == page_id
            )

            if not include_inherited:
                query = query.filter(WikiPermission.is_inherited == False)

            permissions = query.all()
            return permissions

        except SQLAlchemyError as e:
            logger.error(f"Error getting page permissions: {str(e)}")
            return []

    def check_page_permission(
        self,
        page_id: int,
        user_id: int,
        required_level: PermissionLevel,
        user_roles: Optional[List[str]] = None
    ) -> bool:
        """
        Check if a user has required permission level for a page.

        Args:
            page_id: Page ID
            user_id: User ID
            required_level: Required permission level
            user_roles: Optional list of user's roles

        Returns:
            True if user has required permission

        Example:
            >>> can_edit = service.check_page_permission(
            ...     page_id=123,
            ...     user_id=5,
            ...     required_level=PermissionLevel.EDIT,
            ...     user_roles=['editor', 'member']
            ... )
        """
        try:
            user_roles = user_roles or []

            # Get user's effective permission level
            effective_level = self.get_effective_permission(
                page_id,
                user_id,
                user_roles
            )

            # Define permission hierarchy
            hierarchy = {
                PermissionLevel.NONE: 0,
                PermissionLevel.READ: 1,
                PermissionLevel.COMMENT: 2,
                PermissionLevel.EDIT: 3,
                PermissionLevel.ADMIN: 4,
                PermissionLevel.OWNER: 5
            }

            return hierarchy.get(effective_level, 0) >= hierarchy.get(required_level, 0)

        except Exception as e:
            logger.error(f"Error checking page permission: {str(e)}")
            return False

    def get_effective_permission(
        self,
        page_id: int,
        user_id: int,
        user_roles: Optional[List[str]] = None
    ) -> PermissionLevel:
        """
        Get the effective permission level for a user on a page.

        Args:
            page_id: Page ID
            user_id: User ID
            user_roles: Optional list of user's roles

        Returns:
            Effective PermissionLevel

        Example:
            >>> level = service.get_effective_permission(123, user_id=5)
        """
        try:
            user_roles = user_roles or []

            # Check direct user permission
            user_perm = self.db.query(WikiPermission).filter(
                WikiPermission.page_id == page_id,
                WikiPermission.user_id == user_id,
                or_(
                    WikiPermission.expires_at.is_(None),
                    WikiPermission.expires_at > datetime.utcnow()
                )
            ).first()

            if user_perm:
                return user_perm.permission_level

            # Check role permissions
            if user_roles:
                role_perm = self.db.query(WikiPermission).filter(
                    WikiPermission.page_id == page_id,
                    WikiPermission.role.in_(user_roles),
                    or_(
                        WikiPermission.expires_at.is_(None),
                        WikiPermission.expires_at > datetime.utcnow()
                    )
                ).order_by(WikiPermission.permission_level.desc()).first()

                if role_perm:
                    return role_perm.permission_level

            # Check category permissions
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if page and page.category_id:
                cat_level = self.get_category_permission(
                    page.category_id,
                    user_id,
                    user_roles
                )
                if cat_level != PermissionLevel.NONE:
                    return cat_level

            # Default to READ for public pages, NONE otherwise
            # This could be configurable based on page settings
            return PermissionLevel.READ

        except Exception as e:
            logger.error(f"Error getting effective permission: {str(e)}")
            return PermissionLevel.NONE

    # ========================================================================
    # CATEGORY PERMISSIONS
    # ========================================================================

    def grant_category_permission(
        self,
        category_id: int,
        user_id: Optional[int] = None,
        role: Optional[str] = None,
        permission_level: PermissionLevel = PermissionLevel.READ,
        granted_by: int = 1,
        expires_at: Optional[datetime] = None
    ) -> Optional[WikiPermission]:
        """
        Grant permission to a category for a user or role.

        Args:
            category_id: Category ID
            user_id: User ID
            role: Role name
            permission_level: Permission level
            granted_by: User who granted permission
            expires_at: Optional expiration

        Returns:
            Created WikiPermission instance

        Example:
            >>> perm = service.grant_category_permission(
            ...     category_id=10,
            ...     role='editors',
            ...     permission_level=PermissionLevel.EDIT
            ... )
        """
        try:
            if (user_id is None and role is None) or (user_id is not None and role is not None):
                raise ValueError("Must provide either user_id or role, not both")

            # Check if permission exists
            existing = self.db.query(WikiPermission).filter(
                WikiPermission.category_id == category_id
            )

            if user_id:
                existing = existing.filter(WikiPermission.user_id == user_id)
            else:
                existing = existing.filter(WikiPermission.role == role)

            existing_perm = existing.first()

            if existing_perm:
                existing_perm.permission_level = permission_level
                existing_perm.granted_by = granted_by
                existing_perm.granted_at = datetime.utcnow()
                existing_perm.expires_at = expires_at
                self.db.commit()
                self.db.refresh(existing_perm)
                return existing_perm

            permission = WikiPermission(
                category_id=category_id,
                user_id=user_id,
                role=role,
                permission_level=permission_level,
                granted_by=granted_by,
                expires_at=expires_at,
                is_inherited=False
            )

            self.db.add(permission)
            self.db.commit()
            self.db.refresh(permission)

            logger.info(f"Granted {permission_level.value} on category {category_id}")
            return permission

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error granting category permission: {str(e)}")
            raise

    def get_category_permission(
        self,
        category_id: int,
        user_id: int,
        user_roles: Optional[List[str]] = None
    ) -> PermissionLevel:
        """
        Get effective permission for a category.

        Args:
            category_id: Category ID
            user_id: User ID
            user_roles: User's roles

        Returns:
            Effective PermissionLevel

        Example:
            >>> level = service.get_category_permission(10, user_id=5)
        """
        try:
            user_roles = user_roles or []

            # Check direct user permission
            user_perm = self.db.query(WikiPermission).filter(
                WikiPermission.category_id == category_id,
                WikiPermission.user_id == user_id,
                or_(
                    WikiPermission.expires_at.is_(None),
                    WikiPermission.expires_at > datetime.utcnow()
                )
            ).first()

            if user_perm:
                return user_perm.permission_level

            # Check role permissions
            if user_roles:
                role_perm = self.db.query(WikiPermission).filter(
                    WikiPermission.category_id == category_id,
                    WikiPermission.role.in_(user_roles),
                    or_(
                        WikiPermission.expires_at.is_(None),
                        WikiPermission.expires_at > datetime.utcnow()
                    )
                ).order_by(WikiPermission.permission_level.desc()).first()

                if role_perm:
                    return role_perm.permission_level

            # Check parent category permissions (inheritance)
            category = self.db.query(WikiCategory).filter(
                WikiCategory.id == category_id
            ).first()

            if category and category.parent_id:
                return self.get_category_permission(
                    category.parent_id,
                    user_id,
                    user_roles
                )

            return PermissionLevel.NONE

        except Exception as e:
            logger.error(f"Error getting category permission: {str(e)}")
            return PermissionLevel.NONE

    # ========================================================================
    # NAMESPACE PERMISSIONS
    # ========================================================================

    def check_namespace_permission(
        self,
        namespace: str,
        user_id: int,
        required_level: PermissionLevel,
        user_roles: Optional[List[str]] = None
    ) -> bool:
        """
        Check if user has permission for a namespace.

        Args:
            namespace: Namespace identifier
            user_id: User ID
            required_level: Required permission level
            user_roles: User's roles

        Returns:
            True if user has required permission

        Example:
            >>> can_access = service.check_namespace_permission(
            ...     'private',
            ...     user_id=5,
            ...     required_level=PermissionLevel.READ
            ... )
        """
        # This could be extended to support namespace-specific permissions
        # For now, implement basic logic
        user_roles = user_roles or []

        # Example: 'private' namespace requires 'admin' role
        if namespace == 'private':
            return 'admin' in user_roles or required_level == PermissionLevel.OWNER

        # Public namespaces are accessible to all
        return True

    # ========================================================================
    # BULK OPERATIONS
    # ========================================================================

    def copy_permissions(
        self,
        source_page_id: int,
        target_page_id: int,
        granted_by: int
    ) -> int:
        """
        Copy permissions from one page to another.

        Args:
            source_page_id: Source page ID
            target_page_id: Target page ID
            granted_by: User performing the copy

        Returns:
            Number of permissions copied

        Example:
            >>> count = service.copy_permissions(123, 456, granted_by=1)
        """
        try:
            source_perms = self.get_page_permissions(source_page_id, include_inherited=False)
            copied = 0

            for perm in source_perms:
                self.grant_page_permission(
                    page_id=target_page_id,
                    user_id=perm.user_id,
                    role=perm.role,
                    permission_level=perm.permission_level,
                    granted_by=granted_by,
                    expires_at=perm.expires_at
                )
                copied += 1

            logger.info(f"Copied {copied} permissions from page {source_page_id} to {target_page_id}")
            return copied

        except Exception as e:
            logger.error(f"Error copying permissions: {str(e)}")
            return 0

    def get_user_accessible_pages(
        self,
        user_id: int,
        user_roles: Optional[List[str]] = None,
        min_level: PermissionLevel = PermissionLevel.READ,
        limit: int = 100
    ) -> List[WikiPage]:
        """
        Get all pages accessible to a user.

        Args:
            user_id: User ID
            user_roles: User's roles
            min_level: Minimum permission level
            limit: Maximum pages to return

        Returns:
            List of accessible WikiPage instances

        Example:
            >>> pages = service.get_user_accessible_pages(5, min_level=PermissionLevel.EDIT)
        """
        try:
            user_roles = user_roles or []

            # Get pages with direct user permissions
            user_page_perms = self.db.query(WikiPermission.page_id).filter(
                WikiPermission.user_id == user_id,
                WikiPermission.page_id.isnot(None),
                or_(
                    WikiPermission.expires_at.is_(None),
                    WikiPermission.expires_at > datetime.utcnow()
                )
            ).all()

            page_ids = [p[0] for p in user_page_perms]

            # Get pages with role permissions
            if user_roles:
                role_page_perms = self.db.query(WikiPermission.page_id).filter(
                    WikiPermission.role.in_(user_roles),
                    WikiPermission.page_id.isnot(None),
                    or_(
                        WikiPermission.expires_at.is_(None),
                        WikiPermission.expires_at > datetime.utcnow()
                    )
                ).all()

                page_ids.extend([p[0] for p in role_page_perms])

            # Remove duplicates
            page_ids = list(set(page_ids))

            if not page_ids:
                return []

            # Get the actual pages
            pages = self.db.query(WikiPage).filter(
                WikiPage.id.in_(page_ids),
                WikiPage.is_deleted == False
            ).limit(limit).all()

            return pages

        except SQLAlchemyError as e:
            logger.error(f"Error getting accessible pages: {str(e)}")
            return []

    def audit_permissions(
        self,
        page_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Generate permission audit report.

        Args:
            page_id: Optional page to audit
            user_id: Optional user to audit

        Returns:
            List of audit record dictionaries

        Example:
            >>> audit = service.audit_permissions(page_id=123)
        """
        try:
            query = self.db.query(WikiPermission)

            if page_id:
                query = query.filter(WikiPermission.page_id == page_id)
            if user_id:
                query = query.filter(WikiPermission.user_id == user_id)

            permissions = query.all()

            audit_records = []
            for perm in permissions:
                record = {
                    'id': perm.id,
                    'page_id': perm.page_id,
                    'category_id': perm.category_id,
                    'user_id': perm.user_id,
                    'role': perm.role,
                    'permission_level': perm.permission_level.value,
                    'granted_by': perm.granted_by,
                    'granted_at': perm.granted_at,
                    'expires_at': perm.expires_at,
                    'is_inherited': perm.is_inherited,
                    'is_expired': perm.expires_at and perm.expires_at < datetime.utcnow()
                }
                audit_records.append(record)

            return audit_records

        except Exception as e:
            logger.error(f"Error generating permission audit: {str(e)}")
            return []

    def cleanup_expired_permissions(self) -> int:
        """
        Remove expired permissions.

        Returns:
            Number of permissions removed

        Example:
            >>> removed = service.cleanup_expired_permissions()
        """
        try:
            deleted = self.db.query(WikiPermission).filter(
                WikiPermission.expires_at.isnot(None),
                WikiPermission.expires_at < datetime.utcnow()
            ).delete()

            self.db.commit()

            logger.info(f"Cleaned up {deleted} expired permissions")
            return deleted

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error cleaning up permissions: {str(e)}")
            return 0
