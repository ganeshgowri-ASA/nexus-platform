"""
Wiki Search Service

Comprehensive search functionality for the NEXUS Wiki System including:
- Full-text search with relevance ranking
- Semantic search capabilities
- Tag and category filtering
- Advanced query syntax
- Search analytics and suggestions

Author: NEXUS Platform Team
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from sqlalchemy import and_, or_, func, desc, text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.utils import get_logger
from modules.wiki.models import WikiPage, WikiTag, WikiCategory, page_tags
from modules.wiki.wiki_types import (
    PageStatus, PageSearchRequest, PageSearchResult,
    WikiPage as WikiPageSchema
)

logger = get_logger(__name__)


class SearchService:
    """Provides comprehensive search capabilities for wiki content."""

    def __init__(self, db: Session):
        """
        Initialize SearchService.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 20,
        offset: int = 0,
        order_by: str = 'relevance'
    ) -> Tuple[List[Dict], int]:
        """
        Perform comprehensive search across wiki pages.

        Args:
            query: Search query string
            filters: Optional filters (category, tags, status, author, etc.)
            limit: Maximum results
            offset: Results offset
            order_by: Sort order ('relevance', 'date', 'title', 'views')

        Returns:
            Tuple of (search results, total count)

        Example:
            >>> service = SearchService(db)
            >>> results, total = service.search(
            ...     query="python tutorial",
            ...     filters={'category_id': 5, 'tags': ['beginner']},
            ...     limit=10
            ... )
        """
        try:
            filters = filters or {}

            # Build base query
            query_obj = self.db.query(WikiPage).filter(
                WikiPage.is_deleted == False
            )

            # Apply text search
            if query:
                search_filter = self._build_text_search_filter(query)
                query_obj = query_obj.filter(search_filter)

            # Apply filters
            query_obj = self._apply_filters(query_obj, filters)

            # Get total count
            total_count = query_obj.count()

            # Apply ordering
            query_obj = self._apply_ordering(query_obj, order_by, query)

            # Apply pagination
            query_obj = query_obj.limit(limit).offset(offset)

            # Execute query with eager loading
            pages = query_obj.options(
                joinedload(WikiPage.category),
                joinedload(WikiPage.tags)
            ).all()

            # Build results with scores
            results = []
            for page in pages:
                score = self._calculate_relevance_score(page, query) if query else 0.5
                highlights = self._extract_highlights(page, query) if query else []

                results.append({
                    'page': page,
                    'score': score,
                    'highlights': highlights,
                    'matched_fields': self._get_matched_fields(page, query) if query else []
                })

            logger.debug(f"Search returned {len(results)} results out of {total_count}")
            return results, total_count

        except SQLAlchemyError as e:
            logger.error(f"Error performing search: {str(e)}")
            return [], 0

    def full_text_search(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[WikiPage], int]:
        """
        Perform simple full-text search.

        Args:
            query: Search query
            limit: Maximum results
            offset: Results offset

        Returns:
            Tuple of (pages, total count)

        Example:
            >>> pages, total = service.full_text_search("machine learning")
        """
        try:
            search_terms = query.lower().split()

            # Build search filter
            filters = []
            for term in search_terms:
                term_filter = or_(
                    WikiPage.title.ilike(f'%{term}%'),
                    WikiPage.content.ilike(f'%{term}%'),
                    WikiPage.summary.ilike(f'%{term}%')
                )
                filters.append(term_filter)

            query_obj = self.db.query(WikiPage).filter(
                WikiPage.is_deleted == False,
                and_(*filters) if filters else True
            )

            total_count = query_obj.count()

            pages = query_obj.order_by(
                desc(WikiPage.updated_at)
            ).limit(limit).offset(offset).all()

            return pages, total_count

        except SQLAlchemyError as e:
            logger.error(f"Error in full-text search: {str(e)}")
            return [], 0

    def search_by_tags(
        self,
        tags: List[str],
        match_all: bool = False,
        limit: int = 20
    ) -> List[WikiPage]:
        """
        Search pages by tags.

        Args:
            tags: List of tag names
            match_all: If True, page must have all tags; if False, any tag
            limit: Maximum results

        Returns:
            List of matching WikiPage instances

        Example:
            >>> pages = service.search_by_tags(['python', 'tutorial'], match_all=True)
        """
        try:
            # Normalize tag names
            normalized_tags = [tag.strip().lower() for tag in tags]

            # Get tag IDs
            tag_objs = self.db.query(WikiTag).filter(
                WikiTag.name.in_(normalized_tags)
            ).all()

            if not tag_objs:
                return []

            tag_ids = [t.id for t in tag_objs]

            if match_all:
                # Page must have all tags
                query = self.db.query(WikiPage).join(
                    page_tags
                ).filter(
                    page_tags.c.tag_id.in_(tag_ids),
                    WikiPage.is_deleted == False
                ).group_by(WikiPage.id).having(
                    func.count(page_tags.c.tag_id) == len(tag_ids)
                )
            else:
                # Page must have at least one tag
                query = self.db.query(WikiPage).join(
                    page_tags
                ).filter(
                    page_tags.c.tag_id.in_(tag_ids),
                    WikiPage.is_deleted == False
                ).distinct()

            pages = query.limit(limit).all()

            logger.debug(f"Tag search for {tags} returned {len(pages)} results")
            return pages

        except SQLAlchemyError as e:
            logger.error(f"Error searching by tags: {str(e)}")
            return []

    def search_by_category(
        self,
        category_id: int,
        include_subcategories: bool = True,
        limit: int = 100
    ) -> List[WikiPage]:
        """
        Search pages by category.

        Args:
            category_id: Category ID
            include_subcategories: Include pages from child categories
            limit: Maximum results

        Returns:
            List of WikiPage instances

        Example:
            >>> pages = service.search_by_category(5, include_subcategories=True)
        """
        try:
            category_ids = [category_id]

            if include_subcategories:
                # Get all descendant categories
                category_ids.extend(self._get_descendant_categories(category_id))

            pages = self.db.query(WikiPage).filter(
                WikiPage.category_id.in_(category_ids),
                WikiPage.is_deleted == False
            ).limit(limit).all()

            return pages

        except SQLAlchemyError as e:
            logger.error(f"Error searching by category: {str(e)}")
            return []

    def advanced_search(
        self,
        title: Optional[str] = None,
        content: Optional[str] = None,
        author_id: Optional[int] = None,
        category_ids: Optional[List[int]] = None,
        tags: Optional[List[str]] = None,
        status: Optional[PageStatus] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        namespace: Optional[str] = None,
        has_attachments: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[WikiPage], int]:
        """
        Advanced search with multiple criteria.

        Args:
            title: Search in titles
            content: Search in content
            author_id: Filter by author
            category_ids: Filter by categories
            tags: Filter by tags
            status: Filter by status
            date_from: Created after this date
            date_to: Created before this date
            namespace: Filter by namespace
            has_attachments: Filter pages with/without attachments
            limit: Maximum results
            offset: Results offset

        Returns:
            Tuple of (pages, total count)

        Example:
            >>> pages, total = service.advanced_search(
            ...     title="tutorial",
            ...     tags=["python"],
            ...     date_from=datetime(2024, 1, 1)
            ... )
        """
        try:
            query = self.db.query(WikiPage).filter(
                WikiPage.is_deleted == False
            )

            # Title search
            if title:
                query = query.filter(WikiPage.title.ilike(f'%{title}%'))

            # Content search
            if content:
                query = query.filter(WikiPage.content.ilike(f'%{content}%'))

            # Author filter
            if author_id:
                query = query.filter(WikiPage.author_id == author_id)

            # Category filter
            if category_ids:
                query = query.filter(WikiPage.category_id.in_(category_ids))

            # Tags filter
            if tags:
                tag_objs = self.db.query(WikiTag).filter(
                    WikiTag.name.in_([t.lower() for t in tags])
                ).all()
                if tag_objs:
                    tag_ids = [t.id for t in tag_objs]
                    query = query.join(page_tags).filter(
                        page_tags.c.tag_id.in_(tag_ids)
                    )

            # Status filter
            if status:
                query = query.filter(WikiPage.status == status)

            # Date range filter
            if date_from:
                query = query.filter(WikiPage.created_at >= date_from)
            if date_to:
                query = query.filter(WikiPage.created_at <= date_to)

            # Namespace filter
            if namespace:
                query = query.filter(WikiPage.namespace == namespace)

            # Attachments filter
            if has_attachments is not None:
                if has_attachments:
                    from modules.wiki.models import WikiAttachment
                    query = query.join(WikiAttachment).filter(
                        WikiAttachment.is_deleted == False
                    )
                else:
                    from modules.wiki.models import WikiAttachment
                    query = query.outerjoin(WikiAttachment).filter(
                        WikiAttachment.id.is_(None)
                    )

            total_count = query.count()

            pages = query.order_by(
                desc(WikiPage.updated_at)
            ).limit(limit).offset(offset).all()

            logger.debug(f"Advanced search returned {len(pages)} results")
            return pages, total_count

        except SQLAlchemyError as e:
            logger.error(f"Error in advanced search: {str(e)}")
            return [], 0

    def suggest_similar_pages(
        self,
        page_id: int,
        limit: int = 5
    ) -> List[WikiPage]:
        """
        Find similar pages based on tags, category, and content.

        Args:
            page_id: Reference page ID
            limit: Maximum suggestions

        Returns:
            List of similar WikiPage instances

        Example:
            >>> similar = service.suggest_similar_pages(123, limit=5)
        """
        try:
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                return []

            # Score based on shared tags, same category, content similarity
            candidates = self.db.query(WikiPage).filter(
                WikiPage.id != page_id,
                WikiPage.is_deleted == False
            )

            # Prioritize same category
            if page.category_id:
                candidates = candidates.filter(
                    or_(
                        WikiPage.category_id == page.category_id,
                        WikiPage.category_id.isnot(None)
                    )
                )

            candidates = candidates.limit(50).all()

            # Score each candidate
            scored_pages = []
            page_tag_ids = {t.id for t in page.tags}

            for candidate in candidates:
                score = 0

                # Same category bonus
                if candidate.category_id == page.category_id:
                    score += 10

                # Shared tags
                candidate_tag_ids = {t.id for t in candidate.tags}
                shared_tags = page_tag_ids & candidate_tag_ids
                score += len(shared_tags) * 5

                # Content similarity (simple word overlap)
                page_words = set(page.content.lower().split()[:100])
                candidate_words = set(candidate.content.lower().split()[:100])
                common_words = page_words & candidate_words
                score += len(common_words) * 0.1

                if score > 0:
                    scored_pages.append((candidate, score))

            # Sort by score and return top results
            scored_pages.sort(key=lambda x: x[1], reverse=True)
            similar_pages = [page for page, _ in scored_pages[:limit]]

            logger.debug(f"Found {len(similar_pages)} similar pages")
            return similar_pages

        except Exception as e:
            logger.error(f"Error finding similar pages: {str(e)}")
            return []

    def get_search_suggestions(
        self,
        partial_query: str,
        limit: int = 10
    ) -> List[str]:
        """
        Get search query suggestions based on partial input.

        Args:
            partial_query: Partial search query
            limit: Maximum suggestions

        Returns:
            List of suggested queries

        Example:
            >>> suggestions = service.get_search_suggestions("pyth")
            >>> # Returns: ["python", "python tutorial", "python basics", ...]
        """
        try:
            suggestions = set()

            # Get matching page titles
            titles = self.db.query(WikiPage.title).filter(
                WikiPage.title.ilike(f'%{partial_query}%'),
                WikiPage.is_deleted == False
            ).limit(limit).all()

            for title, in titles:
                suggestions.add(title)

            # Get matching tags
            tags = self.db.query(WikiTag.name).filter(
                WikiTag.name.ilike(f'%{partial_query}%')
            ).limit(limit).all()

            for tag_name, in tags:
                suggestions.add(tag_name)

            # Convert to sorted list
            result = sorted(list(suggestions))[:limit]

            return result

        except SQLAlchemyError as e:
            logger.error(f"Error getting search suggestions: {str(e)}")
            return []

    def get_popular_searches(
        self,
        limit: int = 20,
        days: int = 30
    ) -> List[Dict]:
        """
        Get popular search queries (requires analytics tracking).

        Args:
            limit: Maximum results
            days: Look back this many days

        Returns:
            List of popular search dictionaries

        Example:
            >>> popular = service.get_popular_searches(limit=10)
        """
        # This would integrate with analytics system
        # Placeholder implementation
        return []

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _build_text_search_filter(self, query: str):
        """Build SQLAlchemy filter for text search."""
        search_terms = query.lower().split()

        filters = []
        for term in search_terms:
            term_filter = or_(
                WikiPage.title.ilike(f'%{term}%'),
                WikiPage.content.ilike(f'%{term}%'),
                WikiPage.summary.ilike(f'%{term}%')
            )
            filters.append(term_filter)

        return and_(*filters) if filters else True

    def _apply_filters(self, query, filters: Dict):
        """Apply additional filters to query."""
        if filters.get('category_id'):
            query = query.filter(WikiPage.category_id == filters['category_id'])

        if filters.get('status'):
            query = query.filter(WikiPage.status == filters['status'])

        if filters.get('author_id'):
            query = query.filter(WikiPage.author_id == filters['author_id'])

        if filters.get('namespace'):
            query = query.filter(WikiPage.namespace == filters['namespace'])

        if filters.get('tags'):
            tag_names = [t.lower() for t in filters['tags']]
            tag_ids = self.db.query(WikiTag.id).filter(
                WikiTag.name.in_(tag_names)
            ).all()
            if tag_ids:
                tag_ids = [t[0] for t in tag_ids]
                query = query.join(page_tags).filter(
                    page_tags.c.tag_id.in_(tag_ids)
                )

        return query

    def _apply_ordering(self, query, order_by: str, search_query: str = None):
        """Apply ordering to query."""
        if order_by == 'relevance' and search_query:
            # Order by relevance (simplified - could use full-text search ranking)
            return query.order_by(desc(WikiPage.updated_at))
        elif order_by == 'date':
            return query.order_by(desc(WikiPage.created_at))
        elif order_by == 'title':
            return query.order_by(WikiPage.title)
        elif order_by == 'views':
            return query.order_by(desc(WikiPage.view_count))
        else:
            return query.order_by(desc(WikiPage.updated_at))

    def _calculate_relevance_score(self, page: WikiPage, query: str) -> float:
        """Calculate relevance score for a page."""
        if not query:
            return 0.5

        score = 0.0
        query_lower = query.lower()
        terms = query_lower.split()

        # Title match (highest weight)
        title_lower = page.title.lower()
        for term in terms:
            if term in title_lower:
                score += 0.4

        # Exact title match bonus
        if query_lower in title_lower:
            score += 0.3

        # Content match
        content_lower = page.content.lower()
        for term in terms:
            if term in content_lower:
                score += 0.1

        # Summary match
        if page.summary:
            summary_lower = page.summary.lower()
            for term in terms:
                if term in summary_lower:
                    score += 0.2

        # Normalize to 0-1 range
        return min(score, 1.0)

    def _extract_highlights(
        self,
        page: WikiPage,
        query: str,
        context_chars: int = 100
    ) -> List[str]:
        """Extract highlighted snippets from content."""
        if not query:
            return []

        highlights = []
        terms = query.lower().split()
        content = page.content

        for term in terms[:3]:  # Limit to first 3 terms
            pattern = re.compile(f'.{{0,{context_chars}}}{re.escape(term)}.{{0,{context_chars}}}', re.IGNORECASE)
            matches = pattern.findall(content)

            for match in matches[:2]:  # Max 2 highlights per term
                # Clean up and add ellipsis
                highlight = match.strip()
                if len(highlight) > 0:
                    highlights.append(f"...{highlight}...")

        return highlights[:5]  # Max 5 total highlights

    def _get_matched_fields(self, page: WikiPage, query: str) -> List[str]:
        """Get list of fields that matched the query."""
        if not query:
            return []

        matched = []
        query_lower = query.lower()

        if query_lower in page.title.lower():
            matched.append('title')
        if query_lower in page.content.lower():
            matched.append('content')
        if page.summary and query_lower in page.summary.lower():
            matched.append('summary')

        return matched

    def _get_descendant_categories(self, category_id: int) -> List[int]:
        """Get all descendant category IDs."""
        descendants = []

        def collect_children(parent_id: int):
            children = self.db.query(WikiCategory.id).filter(
                WikiCategory.parent_id == parent_id
            ).all()

            for child_id, in children:
                descendants.append(child_id)
                collect_children(child_id)

        collect_children(category_id)
        return descendants
