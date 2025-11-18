"""
Categories and Tagging Module

Hierarchical categorization, tagging, and topic clustering for KB content.
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from .kb_types import Category as CategorySchema
from .models import Category, Tag

logger = logging.getLogger(__name__)


class CategoryManager:
    """
    Manager for hierarchical categories and tags.

    Features:
    - Hierarchical category structure (parent-child)
    - Topic clustering and organization
    - Tag management with usage tracking
    - Category-based content organization
    """

    def __init__(self, db_session: Session):
        """
        Initialize the CategoryManager.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session

    async def create_category(
        self,
        name: str,
        slug: Optional[str] = None,
        description: Optional[str] = None,
        parent_id: Optional[UUID] = None,
        icon: Optional[str] = None,
        order: int = 0,
    ) -> Category:
        """
        Create a new category.

        Args:
            name: Category name
            slug: URL slug (auto-generated if not provided)
            description: Category description
            parent_id: Parent category UUID for hierarchical structure
            icon: Icon identifier
            order: Display order

        Returns:
            Created Category object

        Raises:
            ValueError: If parent category doesn't exist
            Exception: For database errors
        """
        try:
            # Generate slug if not provided
            if not slug:
                slug = self._generate_slug(name)

            # Verify parent exists
            if parent_id:
                parent = self.db.query(Category).filter(Category.id == parent_id).first()
                if not parent:
                    raise ValueError(f"Parent category with ID {parent_id} not found")

            # Create category
            category = Category(
                name=name,
                slug=slug,
                description=description,
                parent_id=parent_id,
                icon=icon,
                order=order,
            )

            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)

            logger.info(f"Created category: {category.id} - {category.name}")
            return category

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating category: {str(e)}")
            raise

    async def update_category(self, category_id: UUID, **updates) -> Category:
        """
        Update an existing category.

        Args:
            category_id: Category UUID
            **updates: Fields to update

        Returns:
            Updated Category object

        Raises:
            ValueError: If category not found
        """
        try:
            category = self.db.query(Category).filter(Category.id == category_id).first()
            if not category:
                raise ValueError(f"Category with ID {category_id} not found")

            # Update fields
            for key, value in updates.items():
                if hasattr(category, key):
                    setattr(category, key, value)

            self.db.commit()
            self.db.refresh(category)

            logger.info(f"Updated category: {category.id} - {category.name}")
            return category

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating category: {str(e)}")
            raise

    async def delete_category(
        self,
        category_id: UUID,
        move_articles_to: Optional[UUID] = None,
    ) -> bool:
        """
        Delete a category.

        Args:
            category_id: Category UUID
            move_articles_to: UUID of category to move articles to

        Returns:
            True if successful

        Raises:
            ValueError: If category not found or has children
        """
        try:
            category = self.db.query(Category).filter(Category.id == category_id).first()
            if not category:
                raise ValueError(f"Category with ID {category_id} not found")

            # Check for child categories
            children = self.db.query(Category).filter(Category.parent_id == category_id).count()
            if children > 0:
                raise ValueError("Cannot delete category with child categories")

            # Move articles if target category provided
            if move_articles_to:
                from .models import Article

                self.db.query(Article).filter(Article.category_id == category_id).update(
                    {"category_id": move_articles_to}
                )

            self.db.delete(category)
            self.db.commit()

            logger.info(f"Deleted category: {category_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting category: {str(e)}")
            raise

    async def get_category(
        self,
        category_id: Optional[UUID] = None,
        slug: Optional[str] = None,
    ) -> Optional[Category]:
        """
        Get a category by ID or slug.

        Args:
            category_id: Category UUID
            slug: Category slug

        Returns:
            Category object or None
        """
        try:
            query = self.db.query(Category)

            if category_id:
                query = query.filter(Category.id == category_id)
            elif slug:
                query = query.filter(Category.slug == slug)
            else:
                raise ValueError("Either category_id or slug must be provided")

            return query.first()

        except Exception as e:
            logger.error(f"Error getting category: {str(e)}")
            raise

    async def list_categories(
        self,
        parent_id: Optional[UUID] = None,
        is_active: Optional[bool] = True,
        include_children: bool = False,
    ) -> List[Category]:
        """
        List categories with optional filtering.

        Args:
            parent_id: Filter by parent category (None for root categories)
            is_active: Filter by active status
            include_children: Include all descendant categories

        Returns:
            List of Category objects
        """
        try:
            query = self.db.query(Category)

            if is_active is not None:
                query = query.filter(Category.is_active == is_active)

            if not include_children:
                query = query.filter(Category.parent_id == parent_id)

            categories = query.order_by(Category.order, Category.name).all()

            return categories

        except Exception as e:
            logger.error(f"Error listing categories: {str(e)}")
            raise

    async def get_category_tree(self) -> List[Dict]:
        """
        Get hierarchical category tree.

        Returns:
            Nested dictionary representing category hierarchy
        """
        try:
            # Get all active categories
            categories = (
                self.db.query(Category)
                .filter(Category.is_active == True)
                .order_by(Category.order, Category.name)
                .all()
            )

            # Build tree structure
            category_dict = {cat.id: self._category_to_dict(cat) for cat in categories}

            # Organize into tree
            tree = []
            for cat in categories:
                cat_dict = category_dict[cat.id]
                if cat.parent_id and cat.parent_id in category_dict:
                    parent = category_dict[cat.parent_id]
                    if "children" not in parent:
                        parent["children"] = []
                    parent["children"].append(cat_dict)
                else:
                    tree.append(cat_dict)

            return tree

        except Exception as e:
            logger.error(f"Error getting category tree: {str(e)}")
            raise

    async def create_tag(
        self,
        name: str,
        slug: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Tag:
        """
        Create a new tag.

        Args:
            name: Tag name
            slug: URL slug
            description: Tag description
            color: Color code for UI

        Returns:
            Created Tag object
        """
        try:
            if not slug:
                slug = self._generate_slug(name)

            tag = Tag(
                name=name,
                slug=slug,
                description=description,
                color=color,
            )

            self.db.add(tag)
            self.db.commit()
            self.db.refresh(tag)

            logger.info(f"Created tag: {tag.id} - {tag.name}")
            return tag

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating tag: {str(e)}")
            raise

    async def get_popular_tags(self, limit: int = 20) -> List[Tag]:
        """
        Get most used tags.

        Args:
            limit: Number of tags to return

        Returns:
            List of popular tags
        """
        try:
            tags = (
                self.db.query(Tag)
                .order_by(desc(Tag.usage_count))
                .limit(limit)
                .all()
            )

            return tags

        except Exception as e:
            logger.error(f"Error getting popular tags: {str(e)}")
            raise

    async def search_tags(self, query: str, limit: int = 10) -> List[Tag]:
        """
        Search tags by name.

        Args:
            query: Search query
            limit: Number of results

        Returns:
            List of matching tags
        """
        try:
            tags = (
                self.db.query(Tag)
                .filter(Tag.name.ilike(f"%{query}%"))
                .order_by(desc(Tag.usage_count))
                .limit(limit)
                .all()
            )

            return tags

        except Exception as e:
            logger.error(f"Error searching tags: {str(e)}")
            raise

    def _generate_slug(self, name: str) -> str:
        """
        Generate URL slug from name.

        Args:
            name: Category or tag name

        Returns:
            URL-safe slug
        """
        import re

        slug = name.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)

        return slug

    def _category_to_dict(self, category: Category) -> Dict:
        """
        Convert category to dictionary.

        Args:
            category: Category object

        Returns:
            Dictionary representation
        """
        return {
            "id": str(category.id),
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
            "icon": category.icon,
            "article_count": category.article_count,
            "order": category.order,
        }


class TagManager:
    """Manager for content tagging and tag operations."""

    def __init__(self, db_session: Session):
        """
        Initialize the TagManager.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session

    async def get_or_create_tags(self, tag_names: List[str]) -> List[Tag]:
        """
        Get existing tags or create new ones.

        Args:
            tag_names: List of tag names

        Returns:
            List of Tag objects
        """
        tags = []
        for name in tag_names:
            name = name.strip().lower()
            tag = self.db.query(Tag).filter(Tag.name == name).first()

            if not tag:
                slug = name.replace(" ", "-")
                tag = Tag(name=name, slug=slug)
                self.db.add(tag)

            tags.append(tag)

        self.db.commit()
        return tags

    async def merge_tags(self, source_tag_id: UUID, target_tag_id: UUID) -> bool:
        """
        Merge one tag into another.

        Args:
            source_tag_id: Tag to merge from
            target_tag_id: Tag to merge into

        Returns:
            True if successful

        Raises:
            ValueError: If tags not found
        """
        try:
            source = self.db.query(Tag).filter(Tag.id == source_tag_id).first()
            target = self.db.query(Tag).filter(Tag.id == target_tag_id).first()

            if not source or not target:
                raise ValueError("Source or target tag not found")

            # Update usage count
            target.usage_count += source.usage_count

            # Delete source tag (associations will be updated via cascade)
            self.db.delete(source)
            self.db.commit()

            logger.info(f"Merged tag {source_tag_id} into {target_tag_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error merging tags: {str(e)}")
            raise
