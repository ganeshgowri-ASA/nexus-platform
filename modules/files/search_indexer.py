"""Search indexer module for NEXUS Platform.

This module handles file search indexing and full-text search capabilities.
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from database.models import File, User, Tag, Folder, file_tags


class SearchIndexer:
    """Handles file search and indexing."""

    def __init__(self):
        """Initialize the search indexer."""
        pass

    def index_file(self,
                   session: Session,
                   file_id: int,
                   extracted_text: Optional[str] = None) -> bool:
        """Index a file for search.

        Args:
            session: Database session
            file_id: ID of the file to index
            extracted_text: Extracted text content

        Returns:
            True if successful, False otherwise
        """
        try:
            file = session.query(File).filter(File.id == file_id).first()
            if not file:
                return False

            # Update extracted text
            if extracted_text:
                file.extracted_text = extracted_text

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error indexing file: {e}")
            return False

    def search(self,
              session: Session,
              query: str,
              user_id: int,
              filters: Optional[Dict] = None,
              limit: int = 50,
              offset: int = 0) -> List[Dict]:
        """Search for files.

        Args:
            session: Database session
            query: Search query
            user_id: ID of the user performing the search
            filters: Optional filters (category, mime_type, size, date_range)
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of file dictionaries matching the search
        """
        # Build base query - only files the user can access
        base_query = session.query(File).filter(
            File.is_deleted == False
        )

        # Apply search query if provided
        if query and query.strip():
            search_term = f"%{query}%"

            # Search in filename, original_filename, description, and extracted_text
            base_query = base_query.filter(
                or_(
                    File.filename.ilike(search_term),
                    File.original_filename.ilike(search_term),
                    File.description.ilike(search_term),
                    File.extracted_text.ilike(search_term)
                )
            )

        # Apply filters
        if filters:
            # Category filter
            if 'category' in filters and filters['category']:
                base_query = base_query.filter(File.category == filters['category'])

            # MIME type filter
            if 'mime_type' in filters and filters['mime_type']:
                base_query = base_query.filter(File.mime_type == filters['mime_type'])

            # File size filter (min, max)
            if 'min_size' in filters and filters['min_size']:
                base_query = base_query.filter(File.file_size >= filters['min_size'])
            if 'max_size' in filters and filters['max_size']:
                base_query = base_query.filter(File.file_size <= filters['max_size'])

            # Date range filter
            if 'start_date' in filters and filters['start_date']:
                base_query = base_query.filter(File.uploaded_at >= filters['start_date'])
            if 'end_date' in filters and filters['end_date']:
                base_query = base_query.filter(File.uploaded_at <= filters['end_date'])

            # Owner filter
            if 'owner_id' in filters and filters['owner_id']:
                base_query = base_query.filter(File.owner_id == filters['owner_id'])

            # Folder filter
            if 'folder_id' in filters and filters['folder_id'] is not None:
                base_query = base_query.filter(File.folder_id == filters['folder_id'])

            # Tag filter
            if 'tags' in filters and filters['tags']:
                tag_names = filters['tags'] if isinstance(filters['tags'], list) else [filters['tags']]
                tags = session.query(Tag).filter(Tag.name.in_(tag_names)).all()
                tag_ids = [tag.id for tag in tags]

                if tag_ids:
                    base_query = base_query.join(File.tags).filter(Tag.id.in_(tag_ids))

            # Favorites filter
            if 'is_favorite' in filters and filters['is_favorite']:
                base_query = base_query.filter(File.is_favorite == True)

        # Sort by relevance (for now, last modified)
        # TODO: Implement proper relevance scoring
        base_query = base_query.order_by(File.last_modified_at.desc())

        # Apply pagination
        files = base_query.limit(limit).offset(offset).all()

        # Format results
        results = []
        for file in files:
            # Check if user has access
            from .sharing_manager import SharingManager
            sharing_manager = SharingManager()
            if not sharing_manager.can_view(session, file.id, user_id):
                continue

            owner = session.query(User).filter(User.id == file.owner_id).first()
            tags = [{'id': tag.id, 'name': tag.name, 'color': tag.color} for tag in file.tags]

            results.append({
                'id': file.id,
                'filename': file.filename,
                'original_filename': file.original_filename,
                'file_path': file.file_path,
                'file_size': file.file_size,
                'mime_type': file.mime_type,
                'category': file.category,
                'description': file.description,
                'owner': owner.username if owner else 'Unknown',
                'owner_id': file.owner_id,
                'folder_id': file.folder_id,
                'version_number': file.version_number,
                'is_favorite': file.is_favorite,
                'thumbnail_path': file.thumbnail_path,
                'tags': tags,
                'download_count': file.download_count,
                'view_count': file.view_count,
                'uploaded_at': file.uploaded_at,
                'last_modified_at': file.last_modified_at,
                'last_accessed_at': file.last_accessed_at,
            })

        return results

    def search_by_tags(self,
                      session: Session,
                      tags: List[str],
                      user_id: int,
                      match_all: bool = False) -> List[Dict]:
        """Search files by tags.

        Args:
            session: Database session
            tags: List of tag names
            user_id: ID of the user
            match_all: If True, match all tags; if False, match any tag

        Returns:
            List of file dictionaries
        """
        # Get tag IDs
        tag_objects = session.query(Tag).filter(Tag.name.in_(tags)).all()
        tag_ids = [tag.id for tag in tag_objects]

        if not tag_ids:
            return []

        query = session.query(File).filter(File.is_deleted == False)

        if match_all:
            # Match all tags (intersection)
            for tag_id in tag_ids:
                query = query.join(File.tags).filter(Tag.id == tag_id)
        else:
            # Match any tag (union)
            query = query.join(File.tags).filter(Tag.id.in_(tag_ids))

        files = query.distinct().all()

        # Format and filter results
        from .sharing_manager import SharingManager
        sharing_manager = SharingManager()

        results = []
        for file in files:
            if sharing_manager.can_view(session, file.id, user_id):
                owner = session.query(User).filter(User.id == file.owner_id).first()
                results.append({
                    'id': file.id,
                    'filename': file.filename,
                    'file_size': file.file_size,
                    'category': file.category,
                    'owner': owner.username if owner else 'Unknown',
                    'uploaded_at': file.uploaded_at,
                })

        return results

    def get_recent_files(self,
                        session: Session,
                        user_id: int,
                        limit: int = 20) -> List[Dict]:
        """Get recently accessed/modified files.

        Args:
            session: Database session
            user_id: ID of the user
            limit: Maximum number of files

        Returns:
            List of recent file dictionaries
        """
        files = session.query(File).filter(
            or_(
                File.owner_id == user_id,
                File.last_modified_by == user_id
            ),
            File.is_deleted == False
        ).order_by(File.last_modified_at.desc()).limit(limit).all()

        results = []
        for file in files:
            owner = session.query(User).filter(User.id == file.owner_id).first()
            results.append({
                'id': file.id,
                'filename': file.filename,
                'file_size': file.file_size,
                'category': file.category,
                'mime_type': file.mime_type,
                'owner': owner.username if owner else 'Unknown',
                'thumbnail_path': file.thumbnail_path,
                'uploaded_at': file.uploaded_at,
                'last_modified_at': file.last_modified_at,
            })

        return results

    def get_popular_files(self,
                         session: Session,
                         user_id: int,
                         limit: int = 20) -> List[Dict]:
        """Get most popular files by download/view count.

        Args:
            session: Database session
            user_id: ID of the user
            limit: Maximum number of files

        Returns:
            List of popular file dictionaries
        """
        files = session.query(File).filter(
            File.is_deleted == False
        ).order_by(
            (File.download_count + File.view_count).desc()
        ).limit(limit).all()

        # Filter by access permission
        from .sharing_manager import SharingManager
        sharing_manager = SharingManager()

        results = []
        for file in files:
            if sharing_manager.can_view(session, file.id, user_id):
                owner = session.query(User).filter(User.id == file.owner_id).first()
                results.append({
                    'id': file.id,
                    'filename': file.filename,
                    'category': file.category,
                    'owner': owner.username if owner else 'Unknown',
                    'download_count': file.download_count,
                    'view_count': file.view_count,
                    'total_interactions': file.download_count + file.view_count,
                })

        return results

    def get_favorites(self,
                     session: Session,
                     user_id: int) -> List[Dict]:
        """Get user's favorite files.

        Args:
            session: Database session
            user_id: ID of the user

        Returns:
            List of favorite file dictionaries
        """
        files = session.query(File).filter(
            File.owner_id == user_id,
            File.is_favorite == True,
            File.is_deleted == False
        ).order_by(File.last_modified_at.desc()).all()

        results = []
        for file in files:
            results.append({
                'id': file.id,
                'filename': file.filename,
                'file_size': file.file_size,
                'category': file.category,
                'mime_type': file.mime_type,
                'thumbnail_path': file.thumbnail_path,
                'uploaded_at': file.uploaded_at,
                'last_modified_at': file.last_modified_at,
            })

        return results

    def get_files_by_category(self,
                             session: Session,
                             category: str,
                             user_id: int,
                             limit: int = 50) -> List[Dict]:
        """Get files by category.

        Args:
            session: Database session
            category: File category
            user_id: ID of the user
            limit: Maximum number of files

        Returns:
            List of file dictionaries
        """
        files = session.query(File).filter(
            File.category == category,
            File.is_deleted == False
        ).order_by(File.uploaded_at.desc()).limit(limit).all()

        # Filter by access permission
        from .sharing_manager import SharingManager
        sharing_manager = SharingManager()

        results = []
        for file in files:
            if sharing_manager.can_view(session, file.id, user_id):
                owner = session.query(User).filter(User.id == file.owner_id).first()
                results.append({
                    'id': file.id,
                    'filename': file.filename,
                    'file_size': file.file_size,
                    'mime_type': file.mime_type,
                    'owner': owner.username if owner else 'Unknown',
                    'uploaded_at': file.uploaded_at,
                })

        return results

    def get_autocomplete_suggestions(self,
                                    session: Session,
                                    query: str,
                                    user_id: int,
                                    limit: int = 10) -> List[str]:
        """Get autocomplete suggestions for search.

        Args:
            session: Database session
            query: Partial search query
            user_id: ID of the user
            limit: Maximum number of suggestions

        Returns:
            List of suggested filenames
        """
        search_term = f"{query}%"

        files = session.query(File.filename).filter(
            File.filename.ilike(search_term),
            File.is_deleted == False
        ).limit(limit).all()

        return [file.filename for file in files]

    def get_search_stats(self, session: Session, user_id: int) -> Dict:
        """Get search statistics for a user.

        Args:
            session: Database session
            user_id: ID of the user

        Returns:
            Dictionary with search statistics
        """
        total_files = session.query(func.count(File.id)).filter(
            File.owner_id == user_id,
            File.is_deleted == False
        ).scalar()

        total_size = session.query(func.sum(File.file_size)).filter(
            File.owner_id == user_id,
            File.is_deleted == False
        ).scalar() or 0

        # Files by category
        category_counts = {}
        categories = session.query(
            File.category,
            func.count(File.id)
        ).filter(
            File.owner_id == user_id,
            File.is_deleted == False
        ).group_by(File.category).all()

        for category, count in categories:
            category_counts[category or 'other'] = count

        return {
            'total_files': total_files,
            'total_size': total_size,
            'category_counts': category_counts,
        }
