"""
Wiki Page Management

Comprehensive CRUD operations and page management for the NEXUS Wiki System.
Includes page creation, editing, deletion, organization, and retrieval.

Author: NEXUS Platform Team
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.utils import get_logger
from modules.wiki.models import (
    WikiPage, WikiTag, WikiCategory, WikiSection,
    WikiHistory, WikiPermission, page_tags
)
from modules.wiki.wiki_types import (
    PageStatus, ContentFormat, ChangeType,
    PageCreateRequest, PageUpdateRequest, PageSearchRequest,
    WikiPage as WikiPageSchema
)

logger = get_logger(__name__)


class PageManager:
    """Manages wiki page operations with comprehensive CRUD functionality."""

    def __init__(self, db: Session):
        """
        Initialize PageManager.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_page(
        self,
        request: PageCreateRequest,
        author_id: int,
        auto_publish: bool = False
    ) -> WikiPage:
        """
        Create a new wiki page.

        Args:
            request: Page creation request with all required data
            author_id: ID of the user creating the page
            auto_publish: Whether to auto-publish the page

        Returns:
            Created WikiPage instance

        Raises:
            ValueError: If page with same slug exists in namespace
            SQLAlchemyError: If database operation fails

        Example:
            >>> manager = PageManager(db)
            >>> request = PageCreateRequest(
            ...     title="Getting Started",
            ...     content="Welcome to our wiki!",
            ...     namespace="docs"
            ... )
            >>> page = manager.create_page(request, author_id=1)
        """
        try:
            # Generate slug from title if not provided
            slug = self._generate_slug(request.title)

            # Check for duplicate slug in namespace
            existing = self.db.query(WikiPage).filter(
                WikiPage.slug == slug,
                WikiPage.namespace == request.namespace,
                WikiPage.is_deleted == False
            ).first()

            if existing:
                raise ValueError(f"Page with slug '{slug}' already exists in namespace '{request.namespace}'")

            # Create page instance
            page = WikiPage(
                title=request.title,
                slug=slug,
                content=request.content,
                content_format=request.content_format,
                summary=request.summary,
                category_id=request.category_id,
                parent_page_id=request.parent_page_id,
                namespace=request.namespace,
                author_id=author_id,
                status=PageStatus.PUBLISHED if auto_publish else request.status,
                current_version=1,
            )

            # Set path based on parent
            if request.parent_page_id:
                parent = self.get_page(request.parent_page_id)
                if parent:
                    page.path = f"{parent.path}{slug}/"
                else:
                    page.path = f"/{slug}/"
            else:
                page.path = f"/{slug}/"

            # Set published_at if auto-publishing
            if auto_publish:
                page.published_at = datetime.utcnow()

            self.db.add(page)
            self.db.flush()  # Get the page ID

            # Handle tags
            if request.tags:
                self._add_tags_to_page(page, request.tags)

            # Create initial history entry
            self._create_history_entry(
                page=page,
                changed_by=author_id,
                change_type=ChangeType.CREATED,
                change_summary="Initial page creation"
            )

            self.db.commit()
            self.db.refresh(page)

            logger.info(f"Created page: {page.id} - '{page.title}' by user {author_id}")
            return page

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating page: {str(e)}")
            raise ValueError(f"Failed to create page: {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating page: {str(e)}")
            raise

    def get_page(
        self,
        page_id: int,
        include_deleted: bool = False,
        load_relations: bool = False
    ) -> Optional[WikiPage]:
        """
        Retrieve a wiki page by ID.

        Args:
            page_id: ID of the page to retrieve
            include_deleted: Whether to include deleted pages
            load_relations: Whether to eager load relationships

        Returns:
            WikiPage instance or None if not found

        Example:
            >>> page = manager.get_page(123, load_relations=True)
        """
        try:
            query = self.db.query(WikiPage).filter(WikiPage.id == page_id)

            if not include_deleted:
                query = query.filter(WikiPage.is_deleted == False)

            if load_relations:
                query = query.options(
                    joinedload(WikiPage.category),
                    joinedload(WikiPage.tags),
                    joinedload(WikiPage.sections),
                    joinedload(WikiPage.attachments),
                )

            return query.first()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving page {page_id}: {str(e)}")
            return None

    def get_page_by_slug(
        self,
        slug: str,
        namespace: Optional[str] = None
    ) -> Optional[WikiPage]:
        """
        Retrieve a wiki page by slug and optional namespace.

        Args:
            slug: Page slug
            namespace: Optional namespace to filter by

        Returns:
            WikiPage instance or None if not found

        Example:
            >>> page = manager.get_page_by_slug("getting-started", namespace="docs")
        """
        try:
            query = self.db.query(WikiPage).filter(
                WikiPage.slug == slug,
                WikiPage.is_deleted == False
            )

            if namespace is not None:
                query = query.filter(WikiPage.namespace == namespace)

            return query.first()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving page by slug '{slug}': {str(e)}")
            return None

    def update_page(
        self,
        page_id: int,
        request: PageUpdateRequest,
        user_id: int
    ) -> Optional[WikiPage]:
        """
        Update an existing wiki page.

        Args:
            page_id: ID of the page to update
            request: Update request with fields to change
            user_id: ID of the user making the update

        Returns:
            Updated WikiPage instance or None if not found

        Raises:
            ValueError: If page is locked or deleted
            SQLAlchemyError: If database operation fails

        Example:
            >>> request = PageUpdateRequest(
            ...     title="Updated Title",
            ...     content="New content",
            ...     change_summary="Fixed typos"
            ... )
            >>> page = manager.update_page(123, request, user_id=1)
        """
        try:
            page = self.get_page(page_id)
            if not page:
                logger.warning(f"Page {page_id} not found for update")
                return None

            if page.is_locked:
                raise ValueError("Cannot update locked page")

            if page.is_deleted:
                raise ValueError("Cannot update deleted page")

            # Track if content changed for versioning
            content_changed = False
            old_content = page.content

            # Update fields
            if request.title is not None:
                page.title = request.title
                # Regenerate slug if title changed
                new_slug = self._generate_slug(request.title)
                if new_slug != page.slug:
                    page.slug = new_slug

            if request.content is not None:
                page.content = request.content
                content_changed = (old_content != request.content)

            if request.content_format is not None:
                page.content_format = request.content_format

            if request.summary is not None:
                page.summary = request.summary

            if request.category_id is not None:
                page.category_id = request.category_id

            if request.status is not None:
                old_status = page.status
                page.status = request.status
                # Set published_at if status changed to published
                if old_status != PageStatus.PUBLISHED and request.status == PageStatus.PUBLISHED:
                    page.published_at = datetime.utcnow()

            if request.tags is not None:
                # Remove existing tags and add new ones
                self._remove_all_tags(page)
                self._add_tags_to_page(page, request.tags)

            # Increment version and create history entry if content changed
            if content_changed:
                page.current_version += 1
                self._create_history_entry(
                    page=page,
                    changed_by=user_id,
                    change_type=ChangeType.EDITED,
                    change_summary=request.change_summary or "Content updated"
                )

            page.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(page)

            logger.info(f"Updated page: {page.id} - '{page.title}' by user {user_id}")
            return page

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating page {page_id}: {str(e)}")
            raise

    def delete_page(
        self,
        page_id: int,
        user_id: int,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete a wiki page (soft delete by default).

        Args:
            page_id: ID of the page to delete
            user_id: ID of the user deleting the page
            hard_delete: If True, permanently delete; otherwise soft delete

        Returns:
            True if successful, False otherwise

        Example:
            >>> success = manager.delete_page(123, user_id=1)
        """
        try:
            page = self.get_page(page_id, include_deleted=True)
            if not page:
                logger.warning(f"Page {page_id} not found for deletion")
                return False

            if hard_delete:
                # Permanently delete
                self.db.delete(page)
                logger.warning(f"Hard deleted page: {page.id} - '{page.title}'")
            else:
                # Soft delete
                page.is_deleted = True
                page.updated_at = datetime.utcnow()
                page.status = PageStatus.DELETED

                # Create history entry
                self._create_history_entry(
                    page=page,
                    changed_by=user_id,
                    change_type=ChangeType.DELETED,
                    change_summary="Page deleted"
                )
                logger.info(f"Soft deleted page: {page.id} - '{page.title}'")

            self.db.commit()
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting page {page_id}: {str(e)}")
            return False

    def restore_page(self, page_id: int, user_id: int) -> Optional[WikiPage]:
        """
        Restore a soft-deleted page.

        Args:
            page_id: ID of the page to restore
            user_id: ID of the user restoring the page

        Returns:
            Restored WikiPage instance or None if not found

        Example:
            >>> page = manager.restore_page(123, user_id=1)
        """
        try:
            page = self.get_page(page_id, include_deleted=True)
            if not page or not page.is_deleted:
                return None

            page.is_deleted = False
            page.status = PageStatus.DRAFT
            page.updated_at = datetime.utcnow()

            self._create_history_entry(
                page=page,
                changed_by=user_id,
                change_type=ChangeType.RESTORED,
                change_summary="Page restored from deletion"
            )

            self.db.commit()
            self.db.refresh(page)

            logger.info(f"Restored page: {page.id} - '{page.title}'")
            return page

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error restoring page {page_id}: {str(e)}")
            return None

    def list_pages(
        self,
        category_id: Optional[int] = None,
        status: Optional[PageStatus] = None,
        namespace: Optional[str] = None,
        author_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
        order_by: str = "updated_at",
        descending: bool = True
    ) -> Tuple[List[WikiPage], int]:
        """
        List wiki pages with filtering and pagination.

        Args:
            category_id: Filter by category
            status: Filter by page status
            namespace: Filter by namespace
            author_id: Filter by author
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field to order by
            descending: Sort in descending order

        Returns:
            Tuple of (list of pages, total count)

        Example:
            >>> pages, total = manager.list_pages(
            ...     category_id=5,
            ...     status=PageStatus.PUBLISHED,
            ...     limit=10
            ... )
        """
        try:
            query = self.db.query(WikiPage).filter(WikiPage.is_deleted == False)

            # Apply filters
            if category_id is not None:
                query = query.filter(WikiPage.category_id == category_id)

            if status is not None:
                query = query.filter(WikiPage.status == status)

            if namespace is not None:
                query = query.filter(WikiPage.namespace == namespace)

            if author_id is not None:
                query = query.filter(WikiPage.author_id == author_id)

            # Get total count
            total_count = query.count()

            # Apply ordering
            order_column = getattr(WikiPage, order_by, WikiPage.updated_at)
            if descending:
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(order_column)

            # Apply pagination
            query = query.limit(limit).offset(offset)

            pages = query.all()

            return pages, total_count

        except SQLAlchemyError as e:
            logger.error(f"Error listing pages: {str(e)}")
            return [], 0

    def get_page_tree(
        self,
        parent_id: Optional[int] = None,
        max_depth: int = 3
    ) -> List[Dict]:
        """
        Get hierarchical tree of pages.

        Args:
            parent_id: ID of parent page (None for root level)
            max_depth: Maximum depth to traverse

        Returns:
            List of page trees with nested children

        Example:
            >>> tree = manager.get_page_tree(max_depth=2)
        """
        try:
            def build_tree(parent_id: Optional[int], current_depth: int) -> List[Dict]:
                if current_depth >= max_depth:
                    return []

                pages = self.db.query(WikiPage).filter(
                    WikiPage.parent_page_id == parent_id,
                    WikiPage.is_deleted == False
                ).order_by(WikiPage.title).all()

                result = []
                for page in pages:
                    node = {
                        "page": page,
                        "children": build_tree(page.id, current_depth + 1),
                        "depth": current_depth
                    }
                    result.append(node)

                return result

            return build_tree(parent_id, 0)

        except SQLAlchemyError as e:
            logger.error(f"Error building page tree: {str(e)}")
            return []

    def move_page(
        self,
        page_id: int,
        new_parent_id: Optional[int],
        user_id: int
    ) -> Optional[WikiPage]:
        """
        Move a page to a different parent.

        Args:
            page_id: ID of the page to move
            new_parent_id: ID of the new parent page (None for root)
            user_id: ID of the user moving the page

        Returns:
            Updated WikiPage instance or None if not found

        Raises:
            ValueError: If move would create circular reference

        Example:
            >>> page = manager.move_page(123, new_parent_id=456, user_id=1)
        """
        try:
            page = self.get_page(page_id)
            if not page:
                return None

            # Check for circular reference
            if new_parent_id is not None:
                if self._would_create_cycle(page_id, new_parent_id):
                    raise ValueError("Move would create circular reference")

            old_parent_id = page.parent_page_id
            page.parent_page_id = new_parent_id

            # Update path
            if new_parent_id:
                parent = self.get_page(new_parent_id)
                if parent:
                    page.path = f"{parent.path}{page.slug}/"
            else:
                page.path = f"/{page.slug}/"

            # Create history entry
            self._create_history_entry(
                page=page,
                changed_by=user_id,
                change_type=ChangeType.MOVED,
                change_summary=f"Moved from parent {old_parent_id} to {new_parent_id}"
            )

            self.db.commit()
            self.db.refresh(page)

            logger.info(f"Moved page {page_id} to parent {new_parent_id}")
            return page

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error moving page {page_id}: {str(e)}")
            return None

    def increment_view_count(self, page_id: int) -> None:
        """
        Increment the view count for a page.

        Args:
            page_id: ID of the page to increment

        Example:
            >>> manager.increment_view_count(123)
        """
        try:
            page = self.get_page(page_id)
            if page:
                page.view_count += 1
                page.last_viewed_at = datetime.utcnow()
                self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error incrementing view count for page {page_id}: {str(e)}")

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _generate_slug(self, title: str) -> str:
        """Generate URL-safe slug from title."""
        slug = title.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_-]+', '-', slug)
        slug = re.sub(r'^-+|-+$', '', slug)
        return slug or "page"

    def _add_tags_to_page(self, page: WikiPage, tag_names: List[str]) -> None:
        """Add tags to a page, creating new tags if needed."""
        for tag_name in tag_names:
            tag_name = tag_name.strip().lower()
            if not tag_name:
                continue

            # Find or create tag
            tag = self.db.query(WikiTag).filter(WikiTag.name == tag_name).first()
            if not tag:
                tag = WikiTag(name=tag_name)
                self.db.add(tag)
                self.db.flush()

            # Add tag to page if not already added
            if tag not in page.tags:
                page.tags.append(tag)
                tag.usage_count += 1

    def _remove_all_tags(self, page: WikiPage) -> None:
        """Remove all tags from a page."""
        for tag in page.tags:
            tag.usage_count = max(0, tag.usage_count - 1)
        page.tags.clear()

    def _create_history_entry(
        self,
        page: WikiPage,
        changed_by: int,
        change_type: ChangeType,
        change_summary: Optional[str] = None
    ) -> WikiHistory:
        """Create a history entry for a page change."""
        history = WikiHistory(
            page_id=page.id,
            version=page.current_version,
            title=page.title,
            content=page.content,
            change_type=change_type,
            change_summary=change_summary,
            changed_by=changed_by,
            content_size=len(page.content.encode('utf-8')),
        )
        self.db.add(history)
        return history

    def _would_create_cycle(self, page_id: int, new_parent_id: int) -> bool:
        """Check if moving a page would create a circular reference."""
        current_id = new_parent_id
        visited = set()

        while current_id is not None:
            if current_id == page_id:
                return True
            if current_id in visited:
                # Circular reference already exists in tree
                return True

            visited.add(current_id)
            parent = self.get_page(current_id)
            current_id = parent.parent_page_id if parent else None

        return False
