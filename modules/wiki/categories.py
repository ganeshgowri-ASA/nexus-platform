"""
Wiki Categories Service

Hierarchical category management and intelligent tagging for the NEXUS Wiki System.
Includes category trees, tag management, auto-categorization, and analytics.

Author: NEXUS Platform Team
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.utils import get_logger
from modules.wiki.models import WikiCategory, WikiTag, WikiPage, page_tags
from modules.wiki.wiki_types import WikiCategory as WikiCategorySchema

logger = get_logger(__name__)


class CategoryService:
    """Manages hierarchical categories and tagging for wiki pages."""

    def __init__(self, db: Session):
        """
        Initialize CategoryService.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_category(
        self,
        name: str,
        slug: str,
        description: Optional[str] = None,
        parent_id: Optional[int] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        order: int = 0
    ) -> Optional[WikiCategory]:
        """
        Create a new category.

        Args:
            name: Category name
            slug: URL-safe category slug
            description: Category description
            parent_id: Parent category ID for hierarchy
            icon: Icon identifier
            color: Hex color code
            order: Display order

        Returns:
            Created WikiCategory instance

        Raises:
            ValueError: If slug already exists or parent not found

        Example:
            >>> service = CategoryService(db)
            >>> cat = service.create_category(
            ...     name="Documentation",
            ...     slug="docs",
            ...     color="#3498db"
            ... )
        """
        try:
            # Check for duplicate slug
            existing = self.db.query(WikiCategory).filter(
                WikiCategory.slug == slug
            ).first()

            if existing:
                raise ValueError(f"Category with slug '{slug}' already exists")

            # Verify parent exists if specified
            if parent_id:
                parent = self.get_category(parent_id)
                if not parent:
                    raise ValueError(f"Parent category {parent_id} not found")

            # Create category
            category = WikiCategory(
                name=name,
                slug=slug,
                description=description,
                parent_id=parent_id,
                icon=icon,
                color=color or '#2c3e50',
                order=order,
                is_active=True
            )

            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)

            logger.info(f"Created category: {category.id} - '{category.name}'")
            return category

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating category: {str(e)}")
            raise ValueError(f"Failed to create category: {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating category: {str(e)}")
            raise

    def get_category(
        self,
        category_id: int,
        load_children: bool = False
    ) -> Optional[WikiCategory]:
        """
        Get a category by ID.

        Args:
            category_id: Category ID
            load_children: Load child categories

        Returns:
            WikiCategory instance or None

        Example:
            >>> category = service.get_category(5, load_children=True)
        """
        try:
            query = self.db.query(WikiCategory).filter(
                WikiCategory.id == category_id
            )

            if load_children:
                query = query.options(joinedload(WikiCategory.children))

            return query.first()

        except SQLAlchemyError as e:
            logger.error(f"Error getting category {category_id}: {str(e)}")
            return None

    def get_category_by_slug(self, slug: str) -> Optional[WikiCategory]:
        """
        Get a category by slug.

        Args:
            slug: Category slug

        Returns:
            WikiCategory instance or None

        Example:
            >>> category = service.get_category_by_slug("documentation")
        """
        try:
            return self.db.query(WikiCategory).filter(
                WikiCategory.slug == slug
            ).first()

        except SQLAlchemyError as e:
            logger.error(f"Error getting category by slug '{slug}': {str(e)}")
            return None

    def update_category(
        self,
        category_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parent_id: Optional[int] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        order: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Optional[WikiCategory]:
        """
        Update a category.

        Args:
            category_id: Category ID
            name: New name
            description: New description
            parent_id: New parent ID
            icon: New icon
            color: New color
            order: New order
            is_active: Active status

        Returns:
            Updated WikiCategory instance

        Example:
            >>> cat = service.update_category(5, name="New Name", color="#ff0000")
        """
        try:
            category = self.get_category(category_id)
            if not category:
                logger.warning(f"Category {category_id} not found")
                return None

            # Update fields
            if name is not None:
                category.name = name
            if description is not None:
                category.description = description
            if parent_id is not None:
                # Check for circular reference
                if self._would_create_cycle(category_id, parent_id):
                    raise ValueError("Update would create circular reference")
                category.parent_id = parent_id
            if icon is not None:
                category.icon = icon
            if color is not None:
                category.color = color
            if order is not None:
                category.order = order
            if is_active is not None:
                category.is_active = is_active

            category.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(category)

            logger.info(f"Updated category: {category.id}")
            return category

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating category: {str(e)}")
            raise

    def delete_category(
        self,
        category_id: int,
        move_pages_to: Optional[int] = None,
        delete_children: bool = False
    ) -> bool:
        """
        Delete a category.

        Args:
            category_id: Category ID
            move_pages_to: Optional category ID to move pages to
            delete_children: Delete child categories too

        Returns:
            True if successful

        Example:
            >>> success = service.delete_category(5, move_pages_to=1)
        """
        try:
            category = self.get_category(category_id)
            if not category:
                return False

            # Handle pages in this category
            if move_pages_to:
                self.db.query(WikiPage).filter(
                    WikiPage.category_id == category_id
                ).update({'category_id': move_pages_to})
            else:
                self.db.query(WikiPage).filter(
                    WikiPage.category_id == category_id
                ).update({'category_id': None})

            # Handle child categories
            if delete_children:
                # Recursively delete children
                children = self.db.query(WikiCategory).filter(
                    WikiCategory.parent_id == category_id
                ).all()
                for child in children:
                    self.delete_category(child.id, move_pages_to, delete_children)
            else:
                # Move children to parent's parent
                self.db.query(WikiCategory).filter(
                    WikiCategory.parent_id == category_id
                ).update({'parent_id': category.parent_id})

            # Delete the category
            self.db.delete(category)
            self.db.commit()

            logger.info(f"Deleted category: {category_id}")
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting category: {str(e)}")
            return False

    def get_category_tree(
        self,
        parent_id: Optional[int] = None,
        include_inactive: bool = False,
        max_depth: int = 10
    ) -> List[Dict]:
        """
        Get hierarchical category tree.

        Args:
            parent_id: Root category ID (None for top level)
            include_inactive: Include inactive categories
            max_depth: Maximum tree depth

        Returns:
            List of category tree dictionaries

        Example:
            >>> tree = service.get_category_tree()
            >>> for node in tree:
            ...     print(f"{node['name']} has {len(node['children'])} children")
        """
        try:
            def build_tree(parent_id: Optional[int], current_depth: int) -> List[Dict]:
                if current_depth >= max_depth:
                    return []

                query = self.db.query(WikiCategory).filter(
                    WikiCategory.parent_id == parent_id
                )

                if not include_inactive:
                    query = query.filter(WikiCategory.is_active == True)

                categories = query.order_by(
                    WikiCategory.order,
                    WikiCategory.name
                ).all()

                result = []
                for cat in categories:
                    node = {
                        'id': cat.id,
                        'name': cat.name,
                        'slug': cat.slug,
                        'description': cat.description,
                        'icon': cat.icon,
                        'color': cat.color,
                        'page_count': cat.page_count,
                        'is_active': cat.is_active,
                        'children': build_tree(cat.id, current_depth + 1),
                        'depth': current_depth
                    }
                    result.append(node)

                return result

            return build_tree(parent_id, 0)

        except SQLAlchemyError as e:
            logger.error(f"Error building category tree: {str(e)}")
            return []

    def get_category_breadcrumbs(self, category_id: int) -> List[WikiCategory]:
        """
        Get breadcrumb trail for a category.

        Args:
            category_id: Category ID

        Returns:
            List of categories from root to current

        Example:
            >>> breadcrumbs = service.get_category_breadcrumbs(10)
            >>> path = ' > '.join([c.name for c in breadcrumbs])
        """
        try:
            breadcrumbs = []
            current = self.get_category(category_id)

            while current:
                breadcrumbs.insert(0, current)
                if current.parent_id:
                    current = self.get_category(current.parent_id)
                else:
                    break

            return breadcrumbs

        except Exception as e:
            logger.error(f"Error getting breadcrumbs: {str(e)}")
            return []

    def update_page_counts(self) -> int:
        """
        Update page counts for all categories.

        Returns:
            Number of categories updated

        Example:
            >>> updated = service.update_page_counts()
        """
        try:
            categories = self.db.query(WikiCategory).all()
            updated = 0

            for category in categories:
                count = self.db.query(func.count(WikiPage.id)).filter(
                    WikiPage.category_id == category.id,
                    WikiPage.is_deleted == False
                ).scalar()

                category.page_count = count
                updated += 1

            self.db.commit()

            logger.info(f"Updated page counts for {updated} categories")
            return updated

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating page counts: {str(e)}")
            return 0

    # ========================================================================
    # TAG MANAGEMENT
    # ========================================================================

    def create_tag(
        self,
        name: str,
        color: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[WikiTag]:
        """
        Create a new tag.

        Args:
            name: Tag name (will be normalized)
            color: Hex color code
            description: Tag description

        Returns:
            Created WikiTag instance

        Example:
            >>> tag = service.create_tag("python", color="#3776ab")
        """
        try:
            # Normalize tag name
            normalized_name = name.strip().lower()

            # Check if tag exists
            existing = self.get_tag_by_name(normalized_name)
            if existing:
                return existing

            tag = WikiTag(
                name=normalized_name,
                color=color or '#3498db',
                description=description
            )

            self.db.add(tag)
            self.db.commit()
            self.db.refresh(tag)

            logger.info(f"Created tag: '{tag.name}'")
            return tag

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating tag: {str(e)}")
            return None

    def get_tag_by_name(self, name: str) -> Optional[WikiTag]:
        """
        Get a tag by name.

        Args:
            name: Tag name

        Returns:
            WikiTag instance or None

        Example:
            >>> tag = service.get_tag_by_name("python")
        """
        try:
            normalized = name.strip().lower()
            return self.db.query(WikiTag).filter(
                WikiTag.name == normalized
            ).first()

        except SQLAlchemyError as e:
            logger.error(f"Error getting tag: {str(e)}")
            return None

    def get_all_tags(
        self,
        min_usage: int = 0,
        limit: int = 100
    ) -> List[WikiTag]:
        """
        Get all tags.

        Args:
            min_usage: Minimum usage count
            limit: Maximum results

        Returns:
            List of WikiTag instances

        Example:
            >>> popular_tags = service.get_all_tags(min_usage=5)
        """
        try:
            query = self.db.query(WikiTag)

            if min_usage > 0:
                query = query.filter(WikiTag.usage_count >= min_usage)

            tags = query.order_by(desc(WikiTag.usage_count)).limit(limit).all()
            return tags

        except SQLAlchemyError as e:
            logger.error(f"Error getting tags: {str(e)}")
            return []

    def get_tag_cloud(self, max_tags: int = 50) -> List[Dict]:
        """
        Get tag cloud data for visualization.

        Args:
            max_tags: Maximum number of tags

        Returns:
            List of tag dictionaries with weights

        Example:
            >>> cloud = service.get_tag_cloud(max_tags=30)
        """
        try:
            tags = self.get_all_tags(min_usage=1, limit=max_tags)

            if not tags:
                return []

            # Calculate weights
            max_usage = max(t.usage_count for t in tags)
            min_usage = min(t.usage_count for t in tags)
            usage_range = max_usage - min_usage or 1

            cloud = []
            for tag in tags:
                # Weight from 1 to 5
                weight = 1 + int(4 * (tag.usage_count - min_usage) / usage_range)
                cloud.append({
                    'name': tag.name,
                    'count': tag.usage_count,
                    'weight': weight,
                    'color': tag.color
                })

            return cloud

        except Exception as e:
            logger.error(f"Error generating tag cloud: {str(e)}")
            return []

    def suggest_tags(
        self,
        content: str,
        title: str,
        max_suggestions: int = 5
    ) -> List[str]:
        """
        Suggest tags based on content and title.

        Args:
            content: Page content
            title: Page title
            max_suggestions: Maximum number of suggestions

        Returns:
            List of suggested tag names

        Example:
            >>> tags = service.suggest_tags(content, title)
        """
        try:
            # Extract keywords from title and content
            text = f"{title} {content}".lower()

            # Remove common words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
                'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were'
            }

            # Extract words
            words = re.findall(r'\b\w+\b', text)
            word_freq = defaultdict(int)

            for word in words:
                if len(word) > 3 and word not in stop_words:
                    word_freq[word] += 1

            # Get existing tags that match
            suggestions = []
            existing_tags = self.get_all_tags(limit=500)

            for tag in existing_tags:
                if tag.name in text:
                    # Calculate relevance score
                    score = word_freq.get(tag.name, 0) * tag.usage_count
                    suggestions.append((tag.name, score))

            # Sort by score and return top suggestions
            suggestions.sort(key=lambda x: x[1], reverse=True)
            return [tag for tag, _ in suggestions[:max_suggestions]]

        except Exception as e:
            logger.error(f"Error suggesting tags: {str(e)}")
            return []

    def auto_categorize(
        self,
        page_id: int,
        content: str,
        title: str
    ) -> Optional[WikiCategory]:
        """
        Automatically categorize a page based on content.

        Args:
            page_id: Page ID
            content: Page content
            title: Page title

        Returns:
            Suggested WikiCategory or None

        Example:
            >>> category = service.auto_categorize(123, content, title)
        """
        try:
            # Get all categories
            categories = self.db.query(WikiCategory).filter(
                WikiCategory.is_active == True
            ).all()

            if not categories:
                return None

            # Score each category
            scores = []
            text = f"{title} {content}".lower()

            for category in categories:
                score = 0

                # Check if category name appears in text
                if category.name.lower() in text:
                    score += 10

                # Check if category slug appears
                if category.slug in text:
                    score += 5

                # Check description keywords
                if category.description:
                    desc_words = set(category.description.lower().split())
                    text_words = set(text.split())
                    common = desc_words & text_words
                    score += len(common)

                if score > 0:
                    scores.append((category, score))

            if not scores:
                return None

            # Return highest scoring category
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[0][0]

        except Exception as e:
            logger.error(f"Error auto-categorizing: {str(e)}")
            return None

    def merge_tags(
        self,
        source_tag_id: int,
        target_tag_id: int
    ) -> bool:
        """
        Merge one tag into another.

        Args:
            source_tag_id: Tag to merge from (will be deleted)
            target_tag_id: Tag to merge into

        Returns:
            True if successful

        Example:
            >>> success = service.merge_tags(source_tag_id=5, target_tag_id=3)
        """
        try:
            source = self.db.query(WikiTag).filter(WikiTag.id == source_tag_id).first()
            target = self.db.query(WikiTag).filter(WikiTag.id == target_tag_id).first()

            if not source or not target:
                logger.warning("Source or target tag not found")
                return False

            # Move all pages from source to target
            self.db.execute(
                page_tags.update().where(
                    page_tags.c.tag_id == source_tag_id
                ).values(tag_id=target_tag_id)
            )

            # Update target usage count
            target.usage_count += source.usage_count

            # Delete source tag
            self.db.delete(source)
            self.db.commit()

            logger.info(f"Merged tag {source_tag_id} into {target_tag_id}")
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error merging tags: {str(e)}")
            return False

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _would_create_cycle(self, category_id: int, new_parent_id: int) -> bool:
        """Check if setting parent would create circular reference."""
        current_id = new_parent_id
        visited = set()

        while current_id is not None:
            if current_id == category_id:
                return True
            if current_id in visited:
                return True

            visited.add(current_id)
            parent = self.get_category(current_id)
            current_id = parent.parent_id if parent else None

        return False
