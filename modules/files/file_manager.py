"""File manager module for NEXUS Platform.

This is the main module that orchestrates file operations including upload,
download, delete, organize, and integrates all other file management modules.
"""
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, BinaryIO, Tuple
from io import BytesIO
from sqlalchemy.orm import Session

from database.models import File, Folder, User, Tag, FileAccessLog, file_tags
from .storage_backend import StorageBackend, LocalStorageBackend
from .validators import FileValidator, ValidationResult
from .file_processor import FileProcessor
from .version_control import VersionControl
from .sharing_manager import SharingManager
from .search_indexer import SearchIndexer


class FileManager:
    """Main file manager orchestrating all file operations."""

    def __init__(self,
                 storage_backend: Optional[StorageBackend] = None,
                 enable_virus_scan: bool = False):
        """Initialize the file manager.

        Args:
            storage_backend: Storage backend to use (defaults to local storage)
            enable_virus_scan: Whether to enable virus scanning
        """
        self.storage = storage_backend or LocalStorageBackend()
        self.validator = FileValidator(enable_virus_scan=enable_virus_scan)
        self.processor = FileProcessor()
        self.version_control = VersionControl(self.storage)
        self.sharing = SharingManager()
        self.search = SearchIndexer()

    def upload_file(self,
                   session: Session,
                   file_content: BinaryIO,
                   filename: str,
                   user_id: int,
                   folder_id: Optional[int] = None,
                   description: Optional[str] = None,
                   tags: Optional[List[str]] = None) -> Tuple[bool, Optional[int], Optional[str]]:
        """Upload a file.

        Args:
            session: Database session
            file_content: File content as file-like object
            filename: Original filename
            user_id: ID of the uploading user
            folder_id: Optional folder ID
            description: Optional file description
            tags: Optional list of tags

        Returns:
            Tuple of (success, file_id, error_message)
        """
        try:
            # Read file content for validation
            content_bytes = file_content.read()
            file_content.seek(0)  # Reset for later use

            # Validate file
            validation = self.validator.validate_file(
                file_content=content_bytes,
                filename=filename
            )

            if not validation.is_valid:
                return False, None, validation.error_message

            file_info = validation.file_info

            # Check for duplicates
            duplicate_id = self.validator.check_duplicate(file_info['hash'], session)
            if duplicate_id:
                return False, None, f"File already exists (ID: {duplicate_id})"

            # Save file to storage
            file_path, file_id = self.storage.save_file(
                file_content,
                filename,
                user_id
            )

            # Get absolute path for processing
            if isinstance(self.storage, LocalStorageBackend):
                abs_path = self.storage.get_absolute_path(file_path)
            else:
                abs_path = None

            # Extract text for search indexing
            extracted_text = None
            if abs_path:
                extracted_text = self.processor.extract_text(abs_path, file_info['mime_type'])

            # Generate thumbnail
            thumbnail_path = None
            if abs_path:
                thumbnail_path = self.processor.generate_thumbnail(abs_path, file_info['mime_type'])

            # Create database record
            file_record = File(
                filename=file_info['filename'],
                original_filename=filename,
                file_path=file_path,
                file_size=file_info['size'],
                mime_type=file_info['mime_type'],
                file_hash=file_info['hash'],
                folder_id=folder_id,
                category=file_info['category'],
                description=description,
                owner_id=user_id,
                last_modified_by=user_id,
                thumbnail_path=thumbnail_path,
                extracted_text=extracted_text,
                version_number=1,
            )

            session.add(file_record)
            session.flush()  # Get the ID

            # Add tags
            if tags:
                self._add_tags_to_file(session, file_record.id, tags)

            # Log access
            self._log_access(session, file_record.id, user_id, 'upload', success=True)

            session.commit()

            return True, file_record.id, None

        except Exception as e:
            session.rollback()
            error_msg = f"Error uploading file: {str(e)}"
            print(error_msg)
            return False, None, error_msg

    def download_file(self,
                     session: Session,
                     file_id: int,
                     user_id: int) -> Optional[Tuple[BinaryIO, str, str]]:
        """Download a file.

        Args:
            session: Database session
            file_id: ID of the file
            user_id: ID of the downloading user

        Returns:
            Tuple of (file_content, filename, mime_type) or None
        """
        try:
            # Get file record
            file = session.query(File).filter(
                File.id == file_id,
                File.is_deleted == False
            ).first()

            if not file:
                return None

            # Check permissions
            if not self.sharing.can_view(session, file_id, user_id):
                return None

            # Get file from storage
            file_content = self.storage.get_file(file.file_path)

            # Update access tracking
            file.download_count += 1
            file.last_accessed_at = datetime.utcnow()

            # Log access
            self._log_access(session, file_id, user_id, 'download', success=True)

            session.commit()

            return file_content, file.original_filename, file.mime_type

        except Exception as e:
            self._log_access(session, file_id, user_id, 'download', success=False, error=str(e))
            print(f"Error downloading file: {e}")
            return None

    def delete_file(self,
                   session: Session,
                   file_id: int,
                   user_id: int,
                   permanent: bool = False) -> bool:
        """Delete a file (soft delete by default).

        Args:
            session: Database session
            file_id: ID of the file
            user_id: ID of the user deleting the file
            permanent: If True, permanently delete; if False, soft delete

        Returns:
            True if successful, False otherwise
        """
        try:
            file = session.query(File).filter(File.id == file_id).first()
            if not file:
                return False

            # Check permissions
            if not self.sharing.can_delete(session, file_id, user_id):
                return False

            if permanent:
                # Permanently delete file from storage
                self.storage.delete_file(file.file_path)

                # Delete thumbnail if exists
                if file.thumbnail_path:
                    try:
                        self.storage.delete_file(file.thumbnail_path)
                    except:
                        pass

                # Delete all versions
                for version in file.versions:
                    try:
                        self.storage.delete_file(version.file_path)
                    except:
                        pass

                # Delete database record
                session.delete(file)
            else:
                # Soft delete
                file.is_deleted = True
                file.deleted_at = datetime.utcnow()

            # Log access
            action = 'delete_permanent' if permanent else 'delete_soft'
            self._log_access(session, file_id, user_id, action, success=True)

            session.commit()
            return True

        except Exception as e:
            session.rollback()
            print(f"Error deleting file: {e}")
            return False

    def restore_file(self,
                    session: Session,
                    file_id: int,
                    user_id: int) -> bool:
        """Restore a soft-deleted file.

        Args:
            session: Database session
            file_id: ID of the file
            user_id: ID of the user restoring the file

        Returns:
            True if successful, False otherwise
        """
        try:
            file = session.query(File).filter(File.id == file_id).first()
            if not file or not file.is_deleted:
                return False

            # Check permissions
            if file.owner_id != user_id:
                return False

            file.is_deleted = False
            file.deleted_at = None

            self._log_access(session, file_id, user_id, 'restore', success=True)
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            print(f"Error restoring file: {e}")
            return False

    def move_file(self,
                 session: Session,
                 file_id: int,
                 user_id: int,
                 target_folder_id: Optional[int]) -> bool:
        """Move a file to a different folder.

        Args:
            session: Database session
            file_id: ID of the file
            user_id: ID of the user
            target_folder_id: Target folder ID (None for root)

        Returns:
            True if successful, False otherwise
        """
        try:
            file = session.query(File).filter(File.id == file_id).first()
            if not file:
                return False

            # Check permissions
            if not self.sharing.can_edit(session, file_id, user_id):
                return False

            # Verify target folder exists if specified
            if target_folder_id:
                folder = session.query(Folder).filter(Folder.id == target_folder_id).first()
                if not folder:
                    return False

            file.folder_id = target_folder_id
            file.last_modified_by = user_id
            file.last_modified_at = datetime.utcnow()

            self._log_access(session, file_id, user_id, 'move', success=True)
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            print(f"Error moving file: {e}")
            return False

    def copy_file(self,
                 session: Session,
                 file_id: int,
                 user_id: int,
                 target_folder_id: Optional[int] = None,
                 new_name: Optional[str] = None) -> Optional[int]:
        """Create a copy of a file.

        Args:
            session: Database session
            file_id: ID of the file to copy
            user_id: ID of the user
            target_folder_id: Target folder ID
            new_name: Optional new name for the copy

        Returns:
            ID of the new file or None
        """
        try:
            original = session.query(File).filter(File.id == file_id).first()
            if not original:
                return None

            # Check permissions
            if not self.sharing.can_view(session, file_id, user_id):
                return None

            # Generate new storage path
            file_content = self.storage.get_file(original.file_path)
            new_path, new_id = self.storage.save_file(
                file_content,
                new_name or original.original_filename,
                user_id
            )
            file_content.close()

            # Create new database record
            new_file = File(
                filename=new_name or f"Copy of {original.filename}",
                original_filename=new_name or original.original_filename,
                file_path=new_path,
                file_size=original.file_size,
                mime_type=original.mime_type,
                file_hash=original.file_hash,
                folder_id=target_folder_id or original.folder_id,
                category=original.category,
                description=original.description,
                owner_id=user_id,
                last_modified_by=user_id,
                extracted_text=original.extracted_text,
                version_number=1,
            )

            session.add(new_file)
            session.flush()

            # Copy tags
            for tag in original.tags:
                new_file.tags.append(tag)

            # Copy thumbnail if exists
            if original.thumbnail_path:
                try:
                    new_thumb_path = original.thumbnail_path.replace(
                        str(original.id),
                        str(new_file.id)
                    )
                    self.storage.copy_file(original.thumbnail_path, new_thumb_path)
                    new_file.thumbnail_path = new_thumb_path
                except:
                    pass

            self._log_access(session, new_file.id, user_id, 'create_copy', success=True)
            session.commit()

            return new_file.id

        except Exception as e:
            session.rollback()
            print(f"Error copying file: {e}")
            return None

    def rename_file(self,
                   session: Session,
                   file_id: int,
                   user_id: int,
                   new_name: str) -> bool:
        """Rename a file.

        Args:
            session: Database session
            file_id: ID of the file
            user_id: ID of the user
            new_name: New filename

        Returns:
            True if successful, False otherwise
        """
        try:
            file = session.query(File).filter(File.id == file_id).first()
            if not file:
                return False

            # Check permissions
            if not self.sharing.can_edit(session, file_id, user_id):
                return False

            file.filename = new_name
            file.last_modified_by = user_id
            file.last_modified_at = datetime.utcnow()

            self._log_access(session, file_id, user_id, 'rename', success=True)
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            print(f"Error renaming file: {e}")
            return False

    def toggle_favorite(self,
                       session: Session,
                       file_id: int,
                       user_id: int) -> bool:
        """Toggle favorite status of a file.

        Args:
            session: Database session
            file_id: ID of the file
            user_id: ID of the user

        Returns:
            True if successful, False otherwise
        """
        try:
            file = session.query(File).filter(
                File.id == file_id,
                File.owner_id == user_id
            ).first()

            if not file:
                return False

            file.is_favorite = not file.is_favorite
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            print(f"Error toggling favorite: {e}")
            return False

    def bulk_download(self,
                     session: Session,
                     file_ids: List[int],
                     user_id: int) -> Optional[BinaryIO]:
        """Download multiple files as a ZIP archive.

        Args:
            session: Database session
            file_ids: List of file IDs
            user_id: ID of the user

        Returns:
            ZIP file content or None
        """
        try:
            # Create ZIP in memory
            zip_buffer = BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_id in file_ids:
                    file = session.query(File).filter(
                        File.id == file_id,
                        File.is_deleted == False
                    ).first()

                    if not file:
                        continue

                    # Check permissions
                    if not self.sharing.can_view(session, file_id, user_id):
                        continue

                    # Get file content
                    file_content = self.storage.get_file(file.file_path)
                    zip_file.writestr(file.original_filename, file_content.read())
                    file_content.close()

                    # Update download count
                    file.download_count += 1

                    # Log access
                    self._log_access(session, file_id, user_id, 'bulk_download', success=True)

            session.commit()

            zip_buffer.seek(0)
            return zip_buffer

        except Exception as e:
            print(f"Error creating bulk download: {e}")
            return None

    def get_file_info(self,
                     session: Session,
                     file_id: int,
                     user_id: int) -> Optional[Dict]:
        """Get detailed information about a file.

        Args:
            session: Database session
            file_id: ID of the file
            user_id: ID of the user

        Returns:
            File information dictionary or None
        """
        file = session.query(File).filter(
            File.id == file_id,
            File.is_deleted == False
        ).first()

        if not file:
            return None

        # Check permissions
        if not self.sharing.can_view(session, file_id, user_id):
            return None

        owner = session.query(User).filter(User.id == file.owner_id).first()
        folder = session.query(Folder).filter(Folder.id == file.folder_id).first()
        tags = [{'id': tag.id, 'name': tag.name, 'color': tag.color} for tag in file.tags]

        # Get permission level
        permission = self.sharing.get_user_permission(session, file_id, user_id)

        # Get sharing info
        shared_users = self.sharing.get_shared_users(session, file_id)

        # Get version info
        version_count = self.version_control.get_version_count(session, file_id)

        return {
            'id': file.id,
            'filename': file.filename,
            'original_filename': file.original_filename,
            'file_size': file.file_size,
            'mime_type': file.mime_type,
            'file_hash': file.file_hash,
            'category': file.category,
            'description': file.description,
            'owner': owner.username if owner else 'Unknown',
            'owner_id': file.owner_id,
            'folder': folder.name if folder else None,
            'folder_id': file.folder_id,
            'version_number': file.version_number,
            'version_count': version_count,
            'is_favorite': file.is_favorite,
            'thumbnail_path': file.thumbnail_path,
            'tags': tags,
            'download_count': file.download_count,
            'view_count': file.view_count,
            'uploaded_at': file.uploaded_at,
            'last_modified_at': file.last_modified_at,
            'last_accessed_at': file.last_accessed_at,
            'permission': permission,
            'shared_with': shared_users,
        }

    def get_trash_files(self, session: Session, user_id: int) -> List[Dict]:
        """Get files in trash for a user.

        Args:
            session: Database session
            user_id: ID of the user

        Returns:
            List of deleted file dictionaries
        """
        files = session.query(File).filter(
            File.owner_id == user_id,
            File.is_deleted == True
        ).order_by(File.deleted_at.desc()).all()

        results = []
        for file in files:
            results.append({
                'id': file.id,
                'filename': file.filename,
                'file_size': file.file_size,
                'category': file.category,
                'deleted_at': file.deleted_at,
                'uploaded_at': file.uploaded_at,
            })

        return results

    def _add_tags_to_file(self, session: Session, file_id: int, tag_names: List[str]) -> None:
        """Add tags to a file, creating new tags if needed.

        Args:
            session: Database session
            file_id: ID of the file
            tag_names: List of tag names
        """
        file = session.query(File).filter(File.id == file_id).first()
        if not file:
            return

        for tag_name in tag_names:
            tag_name = tag_name.strip()
            if not tag_name:
                continue

            # Get or create tag
            tag = session.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                session.add(tag)
                session.flush()

            # Add to file if not already added
            if tag not in file.tags:
                file.tags.append(tag)

    def _log_access(self,
                   session: Session,
                   file_id: int,
                   user_id: int,
                   action: str,
                   success: bool = True,
                   error: Optional[str] = None) -> None:
        """Log file access.

        Args:
            session: Database session
            file_id: ID of the file
            user_id: ID of the user
            action: Action performed
            success: Whether the action succeeded
            error: Optional error message
        """
        try:
            log = FileAccessLog(
                file_id=file_id,
                user_id=user_id,
                action=action,
                success=success,
                error_message=error,
            )
            session.add(log)
        except Exception as e:
            print(f"Error logging access: {e}")
