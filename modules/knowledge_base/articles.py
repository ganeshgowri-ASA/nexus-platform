"""
Article Management Module

Comprehensive article management with rich content editing, versioning,
publishing workflows, and SEO optimization.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from .kb_types import Article as ArticleSchema
from .kb_types import AccessLevel, ContentStatus, Language
from .models import Article, ArticleVersion, Author, Category, Tag

logger = logging.getLogger(__name__)


class ArticleManager:
    """
    Manager for KB articles with full CRUD operations, versioning, and publishing.

    This class handles all article operations including:
    - Creating and editing articles with rich content
    - Publishing workflows and status management
    - Versioning and change tracking
    - SEO optimization
    - Categorization and tagging
    - Analytics tracking
    """

    def __init__(self, db_session: Session):
        """
        Initialize the ArticleManager.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session

    async def create_article(
        self,
        title: str,
        content: str,
        author_id: UUID,
        slug: Optional[str] = None,
        summary: Optional[str] = None,
        category_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        status: ContentStatus = ContentStatus.DRAFT,
        access_level: AccessLevel = AccessLevel.PUBLIC,
        language: Language = Language.EN,
        **kwargs,
    ) -> Article:
        """
        Create a new article.

        Args:
            title: Article title
            content: Article content (HTML/Markdown)
            author_id: UUID of the author
            slug: URL slug (auto-generated if not provided)
            summary: Short summary
            category_id: Category UUID
            tags: List of tag names
            status: Publication status
            access_level: Access level
            language: Content language
            **kwargs: Additional article fields

        Returns:
            Created Article object

        Raises:
            ValueError: If required fields are missing or invalid
            Exception: For database errors
        """
        try:
            # Generate slug if not provided
            if not slug:
                slug = self._generate_slug(title)

            # Verify author exists
            author = self.db.query(Author).filter(Author.id == author_id).first()
            if not author:
                raise ValueError(f"Author with ID {author_id} not found")

            # Verify category exists
            if category_id:
                category = self.db.query(Category).filter(Category.id == category_id).first()
                if not category:
                    raise ValueError(f"Category with ID {category_id} not found")

            # Create article
            article = Article(
                title=title,
                slug=slug,
                content=content,
                summary=summary,
                author_id=author_id,
                category_id=category_id,
                status=status.value,
                access_level=access_level.value,
                language=language.value,
                **kwargs,
            )

            # Add tags
            if tags:
                article_tags = self._get_or_create_tags(tags)
                article.tags.extend(article_tags)

            self.db.add(article)
            self.db.commit()
            self.db.refresh(article)

            logger.info(f"Created article: {article.id} - {article.title}")
            return article

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating article: {str(e)}")
            raise

    async def update_article(
        self,
        article_id: UUID,
        updated_by: UUID,
        create_version: bool = True,
        **updates,
    ) -> Article:
        """
        Update an existing article.

        Args:
            article_id: Article UUID
            updated_by: UUID of user making the update
            create_version: Whether to create a version history entry
            **updates: Fields to update

        Returns:
            Updated Article object

        Raises:
            ValueError: If article not found
            Exception: For database errors
        """
        try:
            article = self.db.query(Article).filter(Article.id == article_id).first()
            if not article:
                raise ValueError(f"Article with ID {article_id} not found")

            # Create version history if requested
            if create_version and ("title" in updates or "content" in updates):
                await self._create_version(article, updated_by)

            # Update tags if provided
            if "tags" in updates:
                tag_names = updates.pop("tags")
                article.tags.clear()
                new_tags = self._get_or_create_tags(tag_names)
                article.tags.extend(new_tags)

            # Update fields
            for key, value in updates.items():
                if hasattr(article, key):
                    setattr(article, key, value)

            article.updated_at = datetime.utcnow()

            # Increment version number
            if create_version:
                article.version += 1

            self.db.commit()
            self.db.refresh(article)

            logger.info(f"Updated article: {article.id} - {article.title}")
            return article

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating article: {str(e)}")
            raise

    async def publish_article(self, article_id: UUID) -> Article:
        """
        Publish an article.

        Args:
            article_id: Article UUID

        Returns:
            Published Article object

        Raises:
            ValueError: If article not found or already published
        """
        try:
            article = self.db.query(Article).filter(Article.id == article_id).first()
            if not article:
                raise ValueError(f"Article with ID {article_id} not found")

            if article.status == ContentStatus.PUBLISHED.value:
                raise ValueError("Article is already published")

            article.status = ContentStatus.PUBLISHED.value
            article.published_at = datetime.utcnow()
            article.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(article)

            logger.info(f"Published article: {article.id} - {article.title}")
            return article

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error publishing article: {str(e)}")
            raise

    async def unpublish_article(self, article_id: UUID) -> Article:
        """
        Unpublish (archive) an article.

        Args:
            article_id: Article UUID

        Returns:
            Archived Article object
        """
        try:
            article = self.db.query(Article).filter(Article.id == article_id).first()
            if not article:
                raise ValueError(f"Article with ID {article_id} not found")

            article.status = ContentStatus.ARCHIVED.value
            article.archived_at = datetime.utcnow()
            article.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(article)

            logger.info(f"Archived article: {article.id} - {article.title}")
            return article

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error archiving article: {str(e)}")
            raise

    async def delete_article(self, article_id: UUID, soft_delete: bool = True) -> bool:
        """
        Delete an article.

        Args:
            article_id: Article UUID
            soft_delete: If True, archive instead of hard delete

        Returns:
            True if successful

        Raises:
            ValueError: If article not found
        """
        try:
            article = self.db.query(Article).filter(Article.id == article_id).first()
            if not article:
                raise ValueError(f"Article with ID {article_id} not found")

            if soft_delete:
                article.status = ContentStatus.ARCHIVED.value
                article.archived_at = datetime.utcnow()
                self.db.commit()
            else:
                self.db.delete(article)
                self.db.commit()

            logger.info(f"Deleted article: {article_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting article: {str(e)}")
            raise

    async def get_article(
        self,
        article_id: Optional[UUID] = None,
        slug: Optional[str] = None,
        increment_views: bool = True,
    ) -> Optional[Article]:
        """
        Get an article by ID or slug.

        Args:
            article_id: Article UUID
            slug: Article slug
            increment_views: Whether to increment view count

        Returns:
            Article object or None if not found
        """
        try:
            query = self.db.query(Article)

            if article_id:
                query = query.filter(Article.id == article_id)
            elif slug:
                query = query.filter(Article.slug == slug)
            else:
                raise ValueError("Either article_id or slug must be provided")

            article = query.first()

            if article and increment_views:
                article.view_count += 1
                self.db.commit()

            return article

        except Exception as e:
            logger.error(f"Error getting article: {str(e)}")
            raise

    async def list_articles(
        self,
        status: Optional[ContentStatus] = None,
        category_id: Optional[UUID] = None,
        author_id: Optional[UUID] = None,
        language: Optional[Language] = None,
        tags: Optional[List[str]] = None,
        access_level: Optional[AccessLevel] = None,
        search_query: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, any]:
        """
        List articles with filtering and pagination.

        Args:
            status: Filter by status
            category_id: Filter by category
            author_id: Filter by author
            language: Filter by language
            tags: Filter by tags
            access_level: Filter by access level
            search_query: Text search query
            limit: Number of results
            offset: Offset for pagination
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)

        Returns:
            Dictionary with articles and pagination info
        """
        try:
            query = self.db.query(Article)

            # Apply filters
            if status:
                query = query.filter(Article.status == status.value)

            if category_id:
                query = query.filter(Article.category_id == category_id)

            if author_id:
                query = query.filter(Article.author_id == author_id)

            if language:
                query = query.filter(Article.language == language.value)

            if access_level:
                query = query.filter(Article.access_level == access_level.value)

            if tags:
                query = query.join(Article.tags).filter(Tag.name.in_(tags))

            if search_query:
                search_filter = or_(
                    Article.title.ilike(f"%{search_query}%"),
                    Article.summary.ilike(f"%{search_query}%"),
                    Article.content.ilike(f"%{search_query}%"),
                )
                query = query.filter(search_filter)

            # Get total count
            total = query.count()

            # Apply sorting
            if sort_order == "desc":
                query = query.order_by(desc(getattr(Article, sort_by)))
            else:
                query = query.order_by(getattr(Article, sort_by))

            # Apply pagination
            articles = query.limit(limit).offset(offset).all()

            return {
                "articles": articles,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total,
            }

        except Exception as e:
            logger.error(f"Error listing articles: {str(e)}")
            raise

    async def get_popular_articles(
        self,
        limit: int = 10,
        days: int = 30,
    ) -> List[Article]:
        """
        Get popular articles based on views and ratings.

        Args:
            limit: Number of articles to return
            days: Time period in days

        Returns:
            List of popular articles
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            articles = (
                self.db.query(Article)
                .filter(
                    and_(
                        Article.status == ContentStatus.PUBLISHED.value,
                        Article.created_at >= cutoff_date,
                    )
                )
                .order_by(
                    desc(Article.view_count),
                    desc(Article.average_rating),
                )
                .limit(limit)
                .all()
            )

            return articles

        except Exception as e:
            logger.error(f"Error getting popular articles: {str(e)}")
            raise

    async def get_related_articles(
        self,
        article_id: UUID,
        limit: int = 5,
    ) -> List[Article]:
        """
        Get related articles based on category and tags.

        Args:
            article_id: Article UUID
            limit: Number of articles to return

        Returns:
            List of related articles
        """
        try:
            article = await self.get_article(article_id, increment_views=False)
            if not article:
                return []

            # Find articles with same category or tags
            query = (
                self.db.query(Article)
                .filter(
                    and_(
                        Article.id != article_id,
                        Article.status == ContentStatus.PUBLISHED.value,
                    )
                )
            )

            # Prioritize same category
            if article.category_id:
                query = query.filter(Article.category_id == article.category_id)

            # Or same tags
            if article.tags:
                tag_ids = [tag.id for tag in article.tags]
                query = query.join(Article.tags).filter(Tag.id.in_(tag_ids))

            related = query.order_by(desc(Article.view_count)).limit(limit).all()

            return related

        except Exception as e:
            logger.error(f"Error getting related articles: {str(e)}")
            raise

    def _generate_slug(self, title: str) -> str:
        """
        Generate URL slug from title.

        Args:
            title: Article title

        Returns:
            URL-safe slug
        """
        import re
        from datetime import datetime

        # Convert to lowercase and replace spaces with hyphens
        slug = title.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)

        # Make unique by checking database
        base_slug = slug
        counter = 1
        while self.db.query(Article).filter(Article.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    def _get_or_create_tags(self, tag_names: List[str]) -> List[Tag]:
        """
        Get or create tags by name.

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

            tag.usage_count += 1
            tags.append(tag)

        return tags

    async def _create_version(self, article: Article, changed_by: UUID) -> ArticleVersion:
        """
        Create a version history entry.

        Args:
            article: Article to version
            changed_by: UUID of user making changes

        Returns:
            Created ArticleVersion
        """
        try:
            version = ArticleVersion(
                article_id=article.id,
                version=article.version,
                title=article.title,
                content=article.content,
                changed_by=changed_by,
            )

            self.db.add(version)
            self.db.commit()

            return version

        except Exception as e:
            logger.error(f"Error creating article version: {str(e)}")
            raise
