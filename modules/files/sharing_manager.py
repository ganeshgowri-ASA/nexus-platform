"""Sharing manager module for NEXUS Platform.

This module handles file sharing, permissions, and public link generation.
"""
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from database.models import File, User, PublicLink, file_shares, PermissionLevel


class SharingManager:
    """Manages file sharing and permissions."""

    def __init__(self):
        """Initialize the sharing manager."""
        pass

    def share_file(self,
                   session: Session,
                   file_id: int,
                   owner_id: int,
                   share_with_user_id: int,
                   permission: str = 'viewer') -> bool:
        """Share a file with another user.

        Args:
            session: Database session
            file_id: ID of the file to share
            owner_id: ID of the file owner
            share_with_user_id: ID of the user to share with
            permission: Permission level ('owner', 'editor', 'commenter', 'viewer')

        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify file exists and user has permission to share
            file = session.query(File).filter(File.id == file_id).first()
            if not file:
                return False

            # Check if requester has permission to share
            if not self.can_share(session, file_id, owner_id):
                return False

            # Validate permission level
            valid_permissions = ['owner', 'editor', 'commenter', 'viewer']
            if permission not in valid_permissions:
                return False

            # Check if already shared
            existing = session.execute(
                file_shares.select().where(
                    and_(
                        file_shares.c.file_id == file_id,
                        file_shares.c.user_id == share_with_user_id
                    )
                )
            ).first()

            if existing:
                # Update existing permission
                session.execute(
                    file_shares.update().where(
                        and_(
                            file_shares.c.file_id == file_id,
                            file_shares.c.user_id == share_with_user_id
                        )
                    ).values(permission=permission, shared_at=datetime.utcnow())
                )
            else:
                # Create new share
                session.execute(
                    file_shares.insert().values(
                        file_id=file_id,
                        user_id=share_with_user_id,
                        permission=permission,
                        shared_at=datetime.utcnow()
                    )
                )

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error sharing file: {e}")
            return False

    def unshare_file(self,
                     session: Session,
                     file_id: int,
                     owner_id: int,
                     user_id: int) -> bool:
        """Remove file sharing for a user.

        Args:
            session: Database session
            file_id: ID of the file
            owner_id: ID of the file owner
            user_id: ID of the user to unshare with

        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify permission to unshare
            if not self.can_share(session, file_id, owner_id):
                return False

            # Remove share
            session.execute(
                file_shares.delete().where(
                    and_(
                        file_shares.c.file_id == file_id,
                        file_shares.c.user_id == user_id
                    )
                )
            )

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error unsharing file: {e}")
            return False

    def get_shared_users(self,
                        session: Session,
                        file_id: int) -> List[Dict]:
        """Get list of users a file is shared with.

        Args:
            session: Database session
            file_id: ID of the file

        Returns:
            List of dictionaries with user info and permissions
        """
        shares = session.execute(
            file_shares.select().where(file_shares.c.file_id == file_id)
        ).all()

        shared_users = []
        for share in shares:
            user = session.query(User).filter(User.id == share.user_id).first()
            if user:
                shared_users.append({
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'permission': share.permission,
                    'shared_at': share.shared_at,
                })

        return shared_users

    def get_user_permission(self,
                           session: Session,
                           file_id: int,
                           user_id: int) -> Optional[str]:
        """Get a user's permission level for a file.

        Args:
            session: Database session
            file_id: ID of the file
            user_id: ID of the user

        Returns:
            Permission level or None
        """
        # Check if user is the owner
        file = session.query(File).filter(File.id == file_id).first()
        if file and file.owner_id == user_id:
            return 'owner'

        # Check shared permissions
        share = session.execute(
            file_shares.select().where(
                and_(
                    file_shares.c.file_id == file_id,
                    file_shares.c.user_id == user_id
                )
            )
        ).first()

        return share.permission if share else None

    def can_view(self, session: Session, file_id: int, user_id: int) -> bool:
        """Check if user can view a file.

        Args:
            session: Database session
            file_id: ID of the file
            user_id: ID of the user

        Returns:
            True if user can view, False otherwise
        """
        permission = self.get_user_permission(session, file_id, user_id)
        return permission in ['owner', 'editor', 'commenter', 'viewer']

    def can_edit(self, session: Session, file_id: int, user_id: int) -> bool:
        """Check if user can edit a file.

        Args:
            session: Database session
            file_id: ID of the file
            user_id: ID of the user

        Returns:
            True if user can edit, False otherwise
        """
        permission = self.get_user_permission(session, file_id, user_id)
        return permission in ['owner', 'editor']

    def can_share(self, session: Session, file_id: int, user_id: int) -> bool:
        """Check if user can share a file.

        Args:
            session: Database session
            file_id: ID of the file
            user_id: ID of the user

        Returns:
            True if user can share, False otherwise
        """
        permission = self.get_user_permission(session, file_id, user_id)
        return permission in ['owner', 'editor']

    def can_delete(self, session: Session, file_id: int, user_id: int) -> bool:
        """Check if user can delete a file.

        Args:
            session: Database session
            file_id: ID of the file
            user_id: ID of the user

        Returns:
            True if user can delete, False otherwise
        """
        permission = self.get_user_permission(session, file_id, user_id)
        return permission == 'owner'

    def create_public_link(self,
                          session: Session,
                          file_id: int,
                          user_id: int,
                          expires_in_days: Optional[int] = None,
                          password: Optional[str] = None,
                          max_downloads: Optional[int] = None,
                          allow_download: bool = True) -> Optional[str]:
        """Create a public link for file sharing.

        Args:
            session: Database session
            file_id: ID of the file
            user_id: ID of the user creating the link
            expires_in_days: Number of days until link expires
            password: Optional password protection
            max_downloads: Maximum number of downloads
            allow_download: Whether to allow downloads

        Returns:
            Link token or None
        """
        try:
            # Verify user has permission to share
            if not self.can_share(session, file_id, user_id):
                return None

            # Generate secure token
            token = secrets.token_urlsafe(32)

            # Calculate expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

            # Hash password if provided
            password_hash = None
            if password:
                import hashlib
                password_hash = hashlib.sha256(password.encode()).hexdigest()

            # Create public link
            public_link = PublicLink(
                file_id=file_id,
                link_token=token,
                password_hash=password_hash,
                max_downloads=max_downloads,
                allow_download=allow_download,
                expires_at=expires_at,
                created_by=user_id,
            )

            session.add(public_link)
            session.commit()

            return token
        except Exception as e:
            session.rollback()
            print(f"Error creating public link: {e}")
            return None

    def get_public_link(self,
                       session: Session,
                       token: str) -> Optional[PublicLink]:
        """Get a public link by token.

        Args:
            session: Database session
            token: Link token

        Returns:
            PublicLink object or None
        """
        return session.query(PublicLink).filter(
            PublicLink.link_token == token,
            PublicLink.is_active == True
        ).first()

    def validate_public_link(self,
                            session: Session,
                            token: str,
                            password: Optional[str] = None) -> bool:
        """Validate a public link.

        Args:
            session: Database session
            token: Link token
            password: Optional password

        Returns:
            True if valid, False otherwise
        """
        link = self.get_public_link(session, token)
        if not link:
            return False

        # Check expiration
        if link.expires_at and link.expires_at < datetime.utcnow():
            return False

        # Check max downloads
        if link.max_downloads and link.download_count >= link.max_downloads:
            return False

        # Check password
        if link.password_hash:
            if not password:
                return False
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash != link.password_hash:
                return False

        return True

    def increment_link_access(self, session: Session, token: str) -> bool:
        """Increment access counter for a public link.

        Args:
            session: Database session
            token: Link token

        Returns:
            True if successful, False otherwise
        """
        try:
            link = self.get_public_link(session, token)
            if not link:
                return False

            link.download_count += 1
            link.last_accessed_at = datetime.utcnow()

            # Deactivate if max downloads reached
            if link.max_downloads and link.download_count >= link.max_downloads:
                link.is_active = False

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error incrementing link access: {e}")
            return False

    def revoke_public_link(self,
                          session: Session,
                          token: str,
                          user_id: int) -> bool:
        """Revoke a public link.

        Args:
            session: Database session
            token: Link token
            user_id: ID of the user revoking the link

        Returns:
            True if successful, False otherwise
        """
        try:
            link = self.get_public_link(session, token)
            if not link:
                return False

            # Verify user has permission
            if link.created_by != user_id:
                file = session.query(File).filter(File.id == link.file_id).first()
                if not file or file.owner_id != user_id:
                    return False

            link.is_active = False
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error revoking public link: {e}")
            return False

    def get_file_public_links(self,
                             session: Session,
                             file_id: int) -> List[Dict]:
        """Get all public links for a file.

        Args:
            session: Database session
            file_id: ID of the file

        Returns:
            List of public link dictionaries
        """
        links = session.query(PublicLink).filter(
            PublicLink.file_id == file_id
        ).all()

        result = []
        for link in links:
            result.append({
                'token': link.link_token,
                'is_active': link.is_active,
                'expires_at': link.expires_at,
                'max_downloads': link.max_downloads,
                'download_count': link.download_count,
                'allow_download': link.allow_download,
                'has_password': bool(link.password_hash),
                'created_at': link.created_at,
                'last_accessed_at': link.last_accessed_at,
            })

        return result

    def get_shared_with_me(self,
                          session: Session,
                          user_id: int) -> List[Dict]:
        """Get files shared with a user.

        Args:
            session: Database session
            user_id: ID of the user

        Returns:
            List of file dictionaries
        """
        shares = session.execute(
            file_shares.select().where(file_shares.c.user_id == user_id)
        ).all()

        files = []
        for share in shares:
            file = session.query(File).filter(
                File.id == share.file_id,
                File.is_deleted == False
            ).first()

            if file:
                owner = session.query(User).filter(User.id == file.owner_id).first()
                files.append({
                    'id': file.id,
                    'filename': file.filename,
                    'file_size': file.file_size,
                    'mime_type': file.mime_type,
                    'category': file.category,
                    'owner': owner.username if owner else 'Unknown',
                    'owner_id': file.owner_id,
                    'permission': share.permission,
                    'shared_at': share.shared_at,
                    'uploaded_at': file.uploaded_at,
                    'last_modified_at': file.last_modified_at,
                })

        return files

    def transfer_ownership(self,
                          session: Session,
                          file_id: int,
                          current_owner_id: int,
                          new_owner_id: int) -> bool:
        """Transfer file ownership to another user.

        Args:
            session: Database session
            file_id: ID of the file
            current_owner_id: Current owner's ID
            new_owner_id: New owner's ID

        Returns:
            True if successful, False otherwise
        """
        try:
            file = session.query(File).filter(File.id == file_id).first()
            if not file or file.owner_id != current_owner_id:
                return False

            # Update owner
            file.owner_id = new_owner_id
            file.last_modified_by = current_owner_id
            file.last_modified_at = datetime.utcnow()

            # Update shares - remove new owner if they were shared with, add old owner as editor
            session.execute(
                file_shares.delete().where(
                    and_(
                        file_shares.c.file_id == file_id,
                        file_shares.c.user_id == new_owner_id
                    )
                )
            )

            session.execute(
                file_shares.insert().values(
                    file_id=file_id,
                    user_id=current_owner_id,
                    permission='editor',
                    shared_at=datetime.utcnow()
                )
            )

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error transferring ownership: {e}")
            return False
