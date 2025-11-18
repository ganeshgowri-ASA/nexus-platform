"""
Granular permissions system for document management.

This module provides comprehensive permission management including:
- Document and folder permissions
- Access level management (none, view, comment, edit, admin)
- Permission inheritance
- Share link management
- Permission checking functions
- Role-based access control
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from passlib.hash import bcrypt
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.config import get_settings
from backend.core.exceptions import (
    AuthorizationException,
    DocumentNotFoundException,
    FolderNotFoundException,
    NEXUSException,
    ResourceNotFoundException,
    ValidationException,
)
from backend.core.logging import get_logger
from backend.models.document import (
    AccessLevel,
    Document,
    DocumentPermission,
    Folder,
    FolderPermission,
    ShareLink,
    ShareType,
)
from backend.models.user import User

logger = get_logger(__name__)
settings = get_settings()


class PermissionDeniedException(AuthorizationException):
    """Exception raised when permission is denied."""

    def __init__(
        self,
        message: str = "Permission denied",
        required_level: Optional[AccessLevel] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.get("details", {})
        if required_level:
            details["required_level"] = required_level.value
        super().__init__(message, details=details, **kwargs)


class ShareLinkException(NEXUSException):
    """Exception raised for share link errors."""

    def __init__(self, message: str = "Share link error", **kwargs: Any) -> None:
        super().__init__(message, status_code=400, **kwargs)


class PermissionService:
    """
    Service for managing document and folder permissions.

    Provides comprehensive permission management with support for
    inheritance, sharing, and granular access control.
    """

    # Access level hierarchy (higher number = more permissions)
    ACCESS_HIERARCHY = {
        AccessLevel.NONE: 0,
        AccessLevel.VIEW: 1,
        AccessLevel.COMMENT: 2,
        AccessLevel.EDIT: 3,
        AccessLevel.ADMIN: 4,
    }

    def __init__(self, db_session: AsyncSession) -> None:
        """
        Initialize permission service.

        Args:
            db_session: Database session
        """
        self.db = db_session

    async def grant_document_permission(
        self,
        document_id: int,
        user_id: int,
        access_level: AccessLevel,
        granted_by_id: int,
        expires_at: Optional[datetime] = None,
    ) -> DocumentPermission:
        """
        Grant permission to a user for a document.

        Args:
            document_id: Document ID
            user_id: User to grant permission to
            access_level: Access level to grant
            granted_by_id: User granting the permission
            expires_at: Optional expiration datetime

        Returns:
            DocumentPermission: Created permission object

        Raises:
            DocumentNotFoundException: If document not found
            PermissionDeniedException: If granter lacks admin permission
        """
        logger.info(
            "Granting document permission",
            document_id=document_id,
            user_id=user_id,
            access_level=access_level.value,
            granted_by_id=granted_by_id,
        )

        # Verify document exists
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if not document:
            raise DocumentNotFoundException(document_id)

        # Check if granter has admin permission
        if not await self.check_document_permission(document_id, granted_by_id, AccessLevel.ADMIN):
            raise PermissionDeniedException(
                "Only admins can grant permissions",
                required_level=AccessLevel.ADMIN,
            )

        # Check if permission already exists
        result = await self.db.execute(
            select(DocumentPermission).where(
                and_(
                    DocumentPermission.document_id == document_id,
                    DocumentPermission.user_id == user_id,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing permission
            existing.access_level = access_level
            existing.granted_by_id = granted_by_id
            existing.expires_at = expires_at
            existing.updated_at = datetime.utcnow()
            permission = existing
        else:
            # Create new permission
            permission = DocumentPermission(
                document_id=document_id,
                user_id=user_id,
                access_level=access_level,
                granted_by_id=granted_by_id,
                expires_at=expires_at,
            )
            self.db.add(permission)

        await self.db.commit()
        await self.db.refresh(permission)

        logger.info(
            "Document permission granted",
            document_id=document_id,
            user_id=user_id,
            permission_id=permission.id,
        )

        return permission

    async def revoke_document_permission(
        self,
        document_id: int,
        user_id: int,
        revoked_by_id: int,
    ) -> None:
        """
        Revoke a user's permission for a document.

        Args:
            document_id: Document ID
            user_id: User to revoke permission from
            revoked_by_id: User revoking the permission

        Raises:
            DocumentNotFoundException: If document not found
            PermissionDeniedException: If revoker lacks admin permission
            ResourceNotFoundException: If permission not found
        """
        logger.info(
            "Revoking document permission",
            document_id=document_id,
            user_id=user_id,
            revoked_by_id=revoked_by_id,
        )

        # Check if revoker has admin permission
        if not await self.check_document_permission(document_id, revoked_by_id, AccessLevel.ADMIN):
            raise PermissionDeniedException(
                "Only admins can revoke permissions",
                required_level=AccessLevel.ADMIN,
            )

        # Find and delete permission
        result = await self.db.execute(
            select(DocumentPermission).where(
                and_(
                    DocumentPermission.document_id == document_id,
                    DocumentPermission.user_id == user_id,
                )
            )
        )
        permission = result.scalar_one_or_none()

        if not permission:
            raise ResourceNotFoundException("Permission", f"{document_id}:{user_id}")

        await self.db.delete(permission)
        await self.db.commit()

        logger.info("Document permission revoked", document_id=document_id, user_id=user_id)

    async def check_document_permission(
        self,
        document_id: int,
        user_id: int,
        required_level: AccessLevel,
    ) -> bool:
        """
        Check if a user has required permission for a document.

        Args:
            document_id: Document ID
            user_id: User ID
            required_level: Required access level

        Returns:
            bool: True if user has permission, False otherwise
        """
        # Get document
        result = await self.db.execute(
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.folder))
        )
        document = result.scalar_one_or_none()

        if not document:
            return False

        # Owner has all permissions
        if document.owner_id == user_id:
            return True

        # Public documents allow view access
        if document.is_public and required_level == AccessLevel.VIEW:
            return True

        # Check direct document permission
        result = await self.db.execute(
            select(DocumentPermission).where(
                and_(
                    DocumentPermission.document_id == document_id,
                    DocumentPermission.user_id == user_id,
                )
            )
        )
        doc_permission = result.scalar_one_or_none()

        if doc_permission:
            # Check if permission is expired
            if doc_permission.expires_at and doc_permission.expires_at < datetime.utcnow():
                return False

            # Check access level
            if self._has_sufficient_access(doc_permission.access_level, required_level):
                return True

        # Check inherited folder permissions
        if document.folder_id:
            folder_access = await self.get_folder_access_level(document.folder_id, user_id)
            if self._has_sufficient_access(folder_access, required_level):
                return True

        return False

    async def get_document_access_level(
        self,
        document_id: int,
        user_id: int,
    ) -> AccessLevel:
        """
        Get the effective access level a user has for a document.

        Args:
            document_id: Document ID
            user_id: User ID

        Returns:
            AccessLevel: Effective access level
        """
        # Get document
        result = await self.db.execute(
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.folder))
        )
        document = result.scalar_one_or_none()

        if not document:
            return AccessLevel.NONE

        # Owner has admin access
        if document.owner_id == user_id:
            return AccessLevel.ADMIN

        access_levels: List[AccessLevel] = []

        # Public documents
        if document.is_public:
            access_levels.append(AccessLevel.VIEW)

        # Direct document permission
        result = await self.db.execute(
            select(DocumentPermission).where(
                and_(
                    DocumentPermission.document_id == document_id,
                    DocumentPermission.user_id == user_id,
                )
            )
        )
        doc_permission = result.scalar_one_or_none()

        if doc_permission:
            # Check if not expired
            if not doc_permission.expires_at or doc_permission.expires_at >= datetime.utcnow():
                access_levels.append(doc_permission.access_level)

        # Inherited folder permissions
        if document.folder_id:
            folder_access = await self.get_folder_access_level(document.folder_id, user_id)
            access_levels.append(folder_access)

        # Return highest access level
        if not access_levels:
            return AccessLevel.NONE

        return max(access_levels, key=lambda x: self.ACCESS_HIERARCHY[x])

    async def grant_folder_permission(
        self,
        folder_id: int,
        user_id: int,
        access_level: AccessLevel,
        granted_by_id: int,
        is_inherited: bool = False,
    ) -> FolderPermission:
        """
        Grant permission to a user for a folder.

        Args:
            folder_id: Folder ID
            user_id: User to grant permission to
            access_level: Access level to grant
            granted_by_id: User granting the permission
            is_inherited: Whether permission is inherited

        Returns:
            FolderPermission: Created permission object

        Raises:
            FolderNotFoundException: If folder not found
            PermissionDeniedException: If granter lacks admin permission
        """
        logger.info(
            "Granting folder permission",
            folder_id=folder_id,
            user_id=user_id,
            access_level=access_level.value,
            granted_by_id=granted_by_id,
        )

        # Verify folder exists
        result = await self.db.execute(select(Folder).where(Folder.id == folder_id))
        folder = result.scalar_one_or_none()
        if not folder:
            raise FolderNotFoundException(folder_id)

        # Check if granter has admin permission
        if not await self.check_folder_permission(folder_id, granted_by_id, AccessLevel.ADMIN):
            raise PermissionDeniedException(
                "Only admins can grant permissions",
                required_level=AccessLevel.ADMIN,
            )

        # Check if permission already exists
        result = await self.db.execute(
            select(FolderPermission).where(
                and_(
                    FolderPermission.folder_id == folder_id,
                    FolderPermission.user_id == user_id,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing permission
            existing.access_level = access_level
            existing.granted_by_id = granted_by_id
            existing.is_inherited = is_inherited
            existing.updated_at = datetime.utcnow()
            permission = existing
        else:
            # Create new permission
            permission = FolderPermission(
                folder_id=folder_id,
                user_id=user_id,
                access_level=access_level,
                granted_by_id=granted_by_id,
                is_inherited=is_inherited,
            )
            self.db.add(permission)

        await self.db.commit()
        await self.db.refresh(permission)

        logger.info(
            "Folder permission granted",
            folder_id=folder_id,
            user_id=user_id,
            permission_id=permission.id,
        )

        return permission

    async def check_folder_permission(
        self,
        folder_id: int,
        user_id: int,
        required_level: AccessLevel,
    ) -> bool:
        """
        Check if a user has required permission for a folder.

        Args:
            folder_id: Folder ID
            user_id: User ID
            required_level: Required access level

        Returns:
            bool: True if user has permission, False otherwise
        """
        access_level = await self.get_folder_access_level(folder_id, user_id)
        return self._has_sufficient_access(access_level, required_level)

    async def get_folder_access_level(
        self,
        folder_id: int,
        user_id: int,
    ) -> AccessLevel:
        """
        Get the effective access level a user has for a folder.

        Args:
            folder_id: Folder ID
            user_id: User ID

        Returns:
            AccessLevel: Effective access level
        """
        # Get folder
        result = await self.db.execute(select(Folder).where(Folder.id == folder_id))
        folder = result.scalar_one_or_none()

        if not folder:
            return AccessLevel.NONE

        # Owner has admin access
        if folder.owner_id == user_id:
            return AccessLevel.ADMIN

        access_levels: List[AccessLevel] = []

        # Public folders
        if folder.is_public:
            access_levels.append(AccessLevel.VIEW)

        # Direct folder permission
        result = await self.db.execute(
            select(FolderPermission).where(
                and_(
                    FolderPermission.folder_id == folder_id,
                    FolderPermission.user_id == user_id,
                )
            )
        )
        folder_permission = result.scalar_one_or_none()

        if folder_permission:
            access_levels.append(folder_permission.access_level)

        # Check parent folder permissions (inheritance)
        if folder.parent_id:
            parent_access = await self.get_folder_access_level(folder.parent_id, user_id)
            access_levels.append(parent_access)

        # Return highest access level
        if not access_levels:
            return AccessLevel.NONE

        return max(access_levels, key=lambda x: self.ACCESS_HIERARCHY[x])

    async def list_document_permissions(
        self,
        document_id: int,
    ) -> List[DocumentPermission]:
        """
        List all permissions for a document.

        Args:
            document_id: Document ID

        Returns:
            List[DocumentPermission]: List of permissions

        Raises:
            DocumentNotFoundException: If document not found
        """
        # Verify document exists
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        if not result.scalar_one_or_none():
            raise DocumentNotFoundException(document_id)

        # Get permissions
        result = await self.db.execute(
            select(DocumentPermission)
            .where(DocumentPermission.document_id == document_id)
            .options(
                selectinload(DocumentPermission.user),
                selectinload(DocumentPermission.granted_by),
            )
        )
        permissions = result.scalars().all()

        return list(permissions)

    async def list_user_documents(
        self,
        user_id: int,
        min_access_level: AccessLevel = AccessLevel.VIEW,
    ) -> List[Document]:
        """
        List all documents a user has access to.

        Args:
            user_id: User ID
            min_access_level: Minimum access level required

        Returns:
            List[Document]: List of accessible documents
        """
        # Get documents owned by user
        result = await self.db.execute(
            select(Document).where(Document.owner_id == user_id)
        )
        owned_docs = set(result.scalars().all())

        # Get documents with direct permissions
        result = await self.db.execute(
            select(DocumentPermission)
            .where(DocumentPermission.user_id == user_id)
            .options(selectinload(DocumentPermission.document))
        )
        permissions = result.scalars().all()

        permitted_docs = set()
        for perm in permissions:
            # Check if not expired and has sufficient access
            if (
                perm.document
                and (not perm.expires_at or perm.expires_at >= datetime.utcnow())
                and self._has_sufficient_access(perm.access_level, min_access_level)
            ):
                permitted_docs.add(perm.document)

        # Get public documents if VIEW access is sufficient
        public_docs = set()
        if self._has_sufficient_access(AccessLevel.VIEW, min_access_level):
            result = await self.db.execute(
                select(Document).where(Document.is_public == True)
            )
            public_docs = set(result.scalars().all())

        # Combine all accessible documents
        all_docs = owned_docs | permitted_docs | public_docs

        logger.info(
            "Listed user documents",
            user_id=user_id,
            count=len(all_docs),
            min_access_level=min_access_level.value,
        )

        return list(all_docs)

    def _has_sufficient_access(
        self,
        granted_level: AccessLevel,
        required_level: AccessLevel,
    ) -> bool:
        """
        Check if granted access level is sufficient for required level.

        Args:
            granted_level: Access level granted to user
            required_level: Required access level

        Returns:
            bool: True if granted level is sufficient
        """
        return self.ACCESS_HIERARCHY[granted_level] >= self.ACCESS_HIERARCHY[required_level]


class ShareLinkService:
    """
    Service for managing document share links.

    Provides functionality for creating and managing shareable links
    with optional password protection and expiration.
    """

    def __init__(self, db_session: AsyncSession, permission_service: PermissionService) -> None:
        """
        Initialize share link service.

        Args:
            db_session: Database session
            permission_service: Permission service instance
        """
        self.db = db_session
        self.permission_service = permission_service

    async def create_share_link(
        self,
        document_id: int,
        created_by_id: int,
        access_level: AccessLevel = AccessLevel.VIEW,
        share_type: ShareType = ShareType.LINK,
        password: Optional[str] = None,
        expires_in_days: Optional[int] = None,
        max_downloads: Optional[int] = None,
    ) -> ShareLink:
        """
        Create a shareable link for a document.

        Args:
            document_id: Document ID
            created_by_id: User creating the link
            access_level: Access level for link users
            share_type: Type of share
            password: Optional password protection
            expires_in_days: Number of days until expiration
            max_downloads: Maximum number of downloads allowed

        Returns:
            ShareLink: Created share link

        Raises:
            DocumentNotFoundException: If document not found
            PermissionDeniedException: If user lacks permission
        """
        logger.info(
            "Creating share link",
            document_id=document_id,
            created_by_id=created_by_id,
            access_level=access_level.value,
        )

        # Check if user has permission to share
        if not await self.permission_service.check_document_permission(
            document_id, created_by_id, AccessLevel.EDIT
        ):
            raise PermissionDeniedException(
                "Only users with edit permission can create share links",
                required_level=AccessLevel.EDIT,
            )

        # Generate unique token
        token = self._generate_token()

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        elif settings.DEFAULT_SHARE_EXPIRATION_DAYS:
            expires_at = datetime.utcnow() + timedelta(
                days=settings.DEFAULT_SHARE_EXPIRATION_DAYS
            )

        # Hash password if provided
        password_hash = None
        if password:
            password_hash = bcrypt.hash(password)

        # Create share link
        share_link = ShareLink(
            document_id=document_id,
            token=token,
            share_type=share_type,
            access_level=access_level,
            password_hash=password_hash,
            expires_at=expires_at,
            max_downloads=max_downloads,
            created_by_id=created_by_id,
        )

        self.db.add(share_link)
        await self.db.commit()
        await self.db.refresh(share_link)

        logger.info(
            "Share link created",
            document_id=document_id,
            share_link_id=share_link.id,
            token=token,
        )

        return share_link

    async def get_share_link(self, token: str) -> ShareLink:
        """
        Get a share link by token.

        Args:
            token: Share link token

        Returns:
            ShareLink: Share link object

        Raises:
            ResourceNotFoundException: If link not found
            ShareLinkException: If link is expired or exhausted
        """
        result = await self.db.execute(
            select(ShareLink)
            .where(ShareLink.token == token)
            .options(selectinload(ShareLink.document))
        )
        share_link = result.scalar_one_or_none()

        if not share_link:
            raise ResourceNotFoundException("Share link", token)

        # Check expiration
        if share_link.expires_at and share_link.expires_at < datetime.utcnow():
            raise ShareLinkException("Share link has expired")

        # Check download limit
        if share_link.max_downloads and share_link.download_count >= share_link.max_downloads:
            raise ShareLinkException("Share link download limit reached")

        return share_link

    async def verify_share_link_password(
        self,
        token: str,
        password: str,
    ) -> bool:
        """
        Verify password for a share link.

        Args:
            token: Share link token
            password: Password to verify

        Returns:
            bool: True if password is correct or not required

        Raises:
            ResourceNotFoundException: If link not found
        """
        share_link = await self.get_share_link(token)

        # No password required
        if not share_link.password_hash:
            return True

        # Verify password
        return bcrypt.verify(password, share_link.password_hash)

    async def increment_download_count(self, token: str) -> None:
        """
        Increment the download count for a share link.

        Args:
            token: Share link token

        Raises:
            ResourceNotFoundException: If link not found
        """
        share_link = await self.get_share_link(token)
        share_link.download_count += 1
        await self.db.commit()

        logger.info(
            "Incremented share link download count",
            token=token,
            count=share_link.download_count,
        )

    async def revoke_share_link(self, token: str, revoked_by_id: int) -> None:
        """
        Revoke a share link.

        Args:
            token: Share link token
            revoked_by_id: User revoking the link

        Raises:
            ResourceNotFoundException: If link not found
            PermissionDeniedException: If user lacks permission
        """
        logger.info("Revoking share link", token=token, revoked_by_id=revoked_by_id)

        share_link = await self.get_share_link(token)

        # Check if user has permission to revoke
        if not await self.permission_service.check_document_permission(
            share_link.document_id, revoked_by_id, AccessLevel.EDIT
        ):
            raise PermissionDeniedException(
                "Only users with edit permission can revoke share links",
                required_level=AccessLevel.EDIT,
            )

        await self.db.delete(share_link)
        await self.db.commit()

        logger.info("Share link revoked", token=token)

    async def list_document_share_links(self, document_id: int) -> List[ShareLink]:
        """
        List all share links for a document.

        Args:
            document_id: Document ID

        Returns:
            List[ShareLink]: List of share links

        Raises:
            DocumentNotFoundException: If document not found
        """
        # Verify document exists
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        if not result.scalar_one_or_none():
            raise DocumentNotFoundException(document_id)

        # Get share links
        result = await self.db.execute(
            select(ShareLink)
            .where(ShareLink.document_id == document_id)
            .options(selectinload(ShareLink.created_by))
        )
        share_links = result.scalars().all()

        return list(share_links)

    def _generate_token(self, length: int = 32) -> str:
        """
        Generate a random token for share links.

        Args:
            length: Length of token

        Returns:
            str: Random token
        """
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))
