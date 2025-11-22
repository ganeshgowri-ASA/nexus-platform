"""Version control module for NEXUS Platform.

This module handles file versioning, tracking changes, and restoring previous versions.
"""
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from database.models import File, FileVersion, User
from .storage_backend import StorageBackend


class VersionControl:
    """Manages file versioning and version history."""

    def __init__(self, storage_backend: StorageBackend, max_versions: int = 10):
        """Initialize version control.

        Args:
            storage_backend: Storage backend for file operations
            max_versions: Maximum number of versions to keep per file
        """
        self.storage_backend = storage_backend
        self.max_versions = max_versions

    def create_version(self,
                      session: Session,
                      file_id: int,
                      user_id: int,
                      changes_description: Optional[str] = None) -> Optional[FileVersion]:
        """Create a new version of a file.

        Args:
            session: Database session
            file_id: ID of the file
            user_id: ID of the user making the change
            changes_description: Optional description of changes

        Returns:
            Created FileVersion object or None
        """
        try:
            # Get the current file
            file = session.query(File).filter(File.id == file_id).first()
            if not file:
                return None

            # Get current version number
            current_version = file.version_number
            new_version_number = current_version + 1

            # Copy current file to version storage
            version_path = self._get_version_path(file.file_path, new_version_number)
            success = self.storage_backend.copy_file(file.file_path, version_path)

            if not success:
                return None

            # Get file size
            file_size = self.storage_backend.get_file_size(file.file_path)

            # Create version record
            version = FileVersion(
                file_id=file_id,
                version_number=new_version_number,
                file_path=version_path,
                file_size=file_size,
                file_hash=file.file_hash,
                user_id=user_id,
                changes_description=changes_description,
            )

            session.add(version)

            # Update file's version number
            file.version_number = new_version_number
            file.current_version_id = version.id
            file.last_modified_by = user_id
            file.last_modified_at = datetime.utcnow()

            session.commit()

            # Clean up old versions if exceeded max
            self._cleanup_old_versions(session, file_id)

            return version
        except Exception as e:
            session.rollback()
            print(f"Error creating version: {e}")
            return None

    def get_version_history(self,
                           session: Session,
                           file_id: int) -> List[Dict]:
        """Get version history for a file.

        Args:
            session: Database session
            file_id: ID of the file

        Returns:
            List of version dictionaries
        """
        versions = session.query(FileVersion).filter(
            FileVersion.file_id == file_id
        ).order_by(FileVersion.version_number.desc()).all()

        history = []
        for version in versions:
            user = session.query(User).filter(User.id == version.user_id).first()
            history.append({
                'id': version.id,
                'version_number': version.version_number,
                'file_size': version.file_size,
                'file_hash': version.file_hash,
                'user': user.username if user else 'Unknown',
                'user_id': version.user_id,
                'changes_description': version.changes_description,
                'created_at': version.created_at,
            })

        return history

    def restore_version(self,
                       session: Session,
                       file_id: int,
                       version_number: int,
                       user_id: int) -> bool:
        """Restore a file to a previous version.

        Args:
            session: Database session
            file_id: ID of the file
            version_number: Version number to restore
            user_id: ID of the user performing the restore

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the file and version
            file = session.query(File).filter(File.id == file_id).first()
            if not file:
                return False

            version = session.query(FileVersion).filter(
                FileVersion.file_id == file_id,
                FileVersion.version_number == version_number
            ).first()

            if not version:
                return False

            # Create a version of the current state before restoring
            self.create_version(
                session,
                file_id,
                user_id,
                f"Auto-saved before restoring to version {version_number}"
            )

            # Copy the version file to current location
            success = self.storage_backend.copy_file(version.file_path, file.file_path)

            if not success:
                return False

            # Update file metadata
            file.file_size = version.file_size
            file.file_hash = version.file_hash
            file.last_modified_by = user_id
            file.last_modified_at = datetime.utcnow()

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error restoring version: {e}")
            return False

    def get_version(self,
                   session: Session,
                   file_id: int,
                   version_number: int) -> Optional[FileVersion]:
        """Get a specific version of a file.

        Args:
            session: Database session
            file_id: ID of the file
            version_number: Version number to retrieve

        Returns:
            FileVersion object or None
        """
        return session.query(FileVersion).filter(
            FileVersion.file_id == file_id,
            FileVersion.version_number == version_number
        ).first()

    def compare_versions(self,
                        session: Session,
                        file_id: int,
                        version1: int,
                        version2: int) -> Optional[Dict]:
        """Compare two versions of a file.

        Args:
            session: Database session
            file_id: ID of the file
            version1: First version number
            version2: Second version number

        Returns:
            Dictionary with comparison details or None
        """
        v1 = self.get_version(session, file_id, version1)
        v2 = self.get_version(session, file_id, version2)

        if not v1 or not v2:
            return None

        user1 = session.query(User).filter(User.id == v1.user_id).first()
        user2 = session.query(User).filter(User.id == v2.user_id).first()

        return {
            'version1': {
                'number': v1.version_number,
                'size': v1.file_size,
                'hash': v1.file_hash,
                'user': user1.username if user1 else 'Unknown',
                'created_at': v1.created_at,
                'changes': v1.changes_description,
            },
            'version2': {
                'number': v2.version_number,
                'size': v2.file_size,
                'hash': v2.file_hash,
                'user': user2.username if user2 else 'Unknown',
                'created_at': v2.created_at,
                'changes': v2.changes_description,
            },
            'size_diff': v2.file_size - v1.file_size,
            'same_content': v1.file_hash == v2.file_hash,
        }

    def delete_version(self,
                      session: Session,
                      file_id: int,
                      version_number: int) -> bool:
        """Delete a specific version.

        Args:
            session: Database session
            file_id: ID of the file
            version_number: Version number to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Don't allow deleting the current version
            file = session.query(File).filter(File.id == file_id).first()
            if not file or file.version_number == version_number:
                return False

            version = session.query(FileVersion).filter(
                FileVersion.file_id == file_id,
                FileVersion.version_number == version_number
            ).first()

            if not version:
                return False

            # Delete the version file from storage
            self.storage_backend.delete_file(version.file_path)

            # Delete the version record
            session.delete(version)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error deleting version: {e}")
            return False

    def _cleanup_old_versions(self, session: Session, file_id: int) -> None:
        """Clean up old versions exceeding max_versions.

        Args:
            session: Database session
            file_id: ID of the file
        """
        try:
            # Get all versions ordered by version number (newest first)
            versions = session.query(FileVersion).filter(
                FileVersion.file_id == file_id
            ).order_by(FileVersion.version_number.desc()).all()

            # If we have more than max_versions, delete the oldest ones
            if len(versions) > self.max_versions:
                versions_to_delete = versions[self.max_versions:]
                for version in versions_to_delete:
                    # Delete file from storage
                    try:
                        self.storage_backend.delete_file(version.file_path)
                    except Exception as e:
                        print(f"Error deleting version file: {e}")

                    # Delete from database
                    session.delete(version)

                session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error cleaning up old versions: {e}")

    def _get_version_path(self, original_path: str, version_number: int) -> str:
        """Generate storage path for a version.

        Args:
            original_path: Original file path
            version_number: Version number

        Returns:
            Path for the version file
        """
        from pathlib import Path
        path = Path(original_path)
        version_dir = path.parent / 'versions'
        return str(version_dir / f"{path.stem}_v{version_number}{path.suffix}")

    def get_latest_version_number(self, session: Session, file_id: int) -> int:
        """Get the latest version number for a file.

        Args:
            session: Database session
            file_id: ID of the file

        Returns:
            Latest version number
        """
        file = session.query(File).filter(File.id == file_id).first()
        return file.version_number if file else 0

    def has_versions(self, session: Session, file_id: int) -> bool:
        """Check if a file has multiple versions.

        Args:
            session: Database session
            file_id: ID of the file

        Returns:
            True if file has versions, False otherwise
        """
        count = session.query(FileVersion).filter(
            FileVersion.file_id == file_id
        ).count()
        return count > 0

    def get_version_count(self, session: Session, file_id: int) -> int:
        """Get the number of versions for a file.

        Args:
            session: Database session
            file_id: ID of the file

        Returns:
            Number of versions
        """
        return session.query(FileVersion).filter(
            FileVersion.file_id == file_id
        ).count()

    def get_version_file_path(self,
                             session: Session,
                             file_id: int,
                             version_number: int) -> Optional[str]:
        """Get the file path for a specific version.

        Args:
            session: Database session
            file_id: ID of the file
            version_number: Version number

        Returns:
            File path or None
        """
        version = self.get_version(session, file_id, version_number)
        return version.file_path if version else None
