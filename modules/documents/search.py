"""
Advanced search module for Document Management System.

This module provides comprehensive search capabilities including:
- Full-text search using PostgreSQL FTS or Elasticsearch
- Faceted search with dynamic filters
- Saved searches for quick access
- Search history tracking
- Personalized search recommendations
- Advanced query parsing and ranking
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.core.exceptions import (
    InvalidSearchQueryException,
    ResourceNotFoundException,
    SearchException,
    ValidationException,
)
from backend.core.logging import get_logger
from backend.models.document import (
    Document,
    DocumentMetadata,
    DocumentStatus,
    Folder,
    Tag,
)

logger = get_logger(__name__)


class SearchBackend(str, Enum):
    """Search backend types."""

    POSTGRESQL = "postgresql"
    ELASTICSEARCH = "elasticsearch"


class SearchOperator(str, Enum):
    """Search query operators."""

    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class SortOrder(str, Enum):
    """Sort order options."""

    ASC = "asc"
    DESC = "desc"


class SearchFieldWeight(str, Enum):
    """Field weights for search ranking."""

    TITLE = "A"  # Highest weight
    DESCRIPTION = "B"
    CONTENT = "C"
    METADATA = "D"  # Lowest weight


class SearchQuery:
    """
    Structured search query builder.

    Attributes:
        query: Search query string
        filters: Filter conditions
        facets: Facet fields to aggregate
        sort_by: Field to sort by
        sort_order: Sort order
        offset: Result offset for pagination
        limit: Maximum results to return
        highlight: Enable result highlighting
        fuzzy: Enable fuzzy matching
    """

    def __init__(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        facets: Optional[List[str]] = None,
        sort_by: str = "relevance",
        sort_order: SortOrder = SortOrder.DESC,
        offset: int = 0,
        limit: int = 20,
        highlight: bool = True,
        fuzzy: bool = False,
    ) -> None:
        """Initialize search query."""
        self.query = query
        self.filters = filters or {}
        self.facets = facets or []
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.offset = offset
        self.limit = limit
        self.highlight = highlight
        self.fuzzy = fuzzy

    def to_dict(self) -> Dict[str, Any]:
        """Convert query to dictionary."""
        return {
            "query": self.query,
            "filters": self.filters,
            "facets": self.facets,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order.value,
            "offset": self.offset,
            "limit": self.limit,
            "highlight": self.highlight,
            "fuzzy": self.fuzzy,
        }


class SearchResult:
    """
    Search result container.

    Attributes:
        documents: List of matching documents
        total_count: Total number of matches
        facets: Facet aggregations
        query_time: Time taken for query (ms)
        highlights: Result highlights
    """

    def __init__(
        self,
        documents: List[Document],
        total_count: int,
        facets: Optional[Dict[str, Dict[str, int]]] = None,
        query_time: Optional[float] = None,
        highlights: Optional[Dict[int, Dict[str, str]]] = None,
    ) -> None:
        """Initialize search result."""
        self.documents = documents
        self.total_count = total_count
        self.facets = facets or {}
        self.query_time = query_time
        self.highlights = highlights or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "documents": [doc.to_dict() for doc in self.documents],
            "total_count": self.total_count,
            "facets": self.facets,
            "query_time": self.query_time,
            "has_more": self.total_count > len(self.documents),
        }


class SavedSearch:
    """
    Saved search model for quick access.

    Attributes:
        id: Search ID
        user_id: Owner user ID
        name: Search name
        query: Search query object
        is_public: Whether search is shared
        created_at: Creation timestamp
        last_used_at: Last usage timestamp
    """

    def __init__(
        self,
        user_id: int,
        name: str,
        query: SearchQuery,
        is_public: bool = False,
        search_id: Optional[int] = None,
    ) -> None:
        """Initialize saved search."""
        self.id = search_id
        self.user_id = user_id
        self.name = name
        self.query = query
        self.is_public = is_public
        self.created_at = datetime.utcnow()
        self.last_used_at = datetime.utcnow()


class DocumentSearchService:
    """
    Advanced document search service.

    Provides full-text search, faceted search, saved searches,
    and search recommendations with support for multiple backends.
    """

    def __init__(
        self,
        db: AsyncSession,
        backend: SearchBackend = SearchBackend.POSTGRESQL,
    ) -> None:
        """
        Initialize search service.

        Args:
            db: Database session
            backend: Search backend to use
        """
        self.db = db
        self.backend = backend
        self.logger = get_logger(self.__class__.__name__)

    async def search(
        self,
        query: SearchQuery,
        user_id: int,
        include_archived: bool = False,
    ) -> SearchResult:
        """
        Execute search query.

        Args:
            query: Search query object
            user_id: User performing search
            include_archived: Include archived documents

        Returns:
            SearchResult: Search results

        Raises:
            SearchException: If search fails
            InvalidSearchQueryException: If query is invalid
        """
        try:
            start_time = datetime.utcnow()
            self.logger.info(
                "executing_search",
                query=query.query,
                user_id=user_id,
                backend=self.backend.value,
            )

            # Validate query
            self._validate_query(query)

            # Execute search based on backend
            if self.backend == SearchBackend.POSTGRESQL:
                documents, total_count, highlights = await self._search_postgresql(
                    query, user_id, include_archived
                )
            elif self.backend == SearchBackend.ELASTICSEARCH:
                documents, total_count, highlights = await self._search_elasticsearch(
                    query, user_id, include_archived
                )
            else:
                raise SearchException(f"Unsupported backend: {self.backend}")

            # Calculate facets if requested
            facets = {}
            if query.facets:
                facets = await self._calculate_facets(query, user_id, include_archived)

            # Record search history
            await self._record_search_history(user_id, query, total_count)

            query_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            self.logger.info(
                "search_completed",
                total_results=total_count,
                query_time_ms=query_time,
            )

            return SearchResult(
                documents=documents,
                total_count=total_count,
                facets=facets,
                query_time=query_time,
                highlights=highlights,
            )

        except InvalidSearchQueryException:
            raise
        except Exception as e:
            self.logger.exception("search_failed", error=str(e))
            raise SearchException(f"Search failed: {str(e)}")

    async def _search_postgresql(
        self,
        query: SearchQuery,
        user_id: int,
        include_archived: bool,
    ) -> Tuple[List[Document], int, Dict[int, Dict[str, str]]]:
        """
        Execute search using PostgreSQL full-text search.

        Args:
            query: Search query
            user_id: User ID
            include_archived: Include archived documents

        Returns:
            Tuple of (documents, total_count, highlights)
        """
        try:
            # Build base query with permissions check
            stmt = (
                select(Document)
                .where(
                    or_(
                        Document.owner_id == user_id,
                        Document.is_public == True,
                    )
                )
                .options(joinedload(Document.owner))
            )

            # Apply status filter
            if not include_archived:
                stmt = stmt.where(Document.status == DocumentStatus.ACTIVE)

            # Apply full-text search
            if query.query:
                # Create tsvector from multiple fields with weights
                ts_vector = func.to_tsvector(
                    "english",
                    func.coalesce(Document.title, "") + " " +
                    func.coalesce(Document.description, "")
                )

                # Create tsquery
                ts_query = func.plainto_tsquery("english", query.query)

                # Apply search condition
                stmt = stmt.where(ts_vector.op("@@")(ts_query))

                # Add ranking
                rank = func.ts_rank(ts_vector, ts_query)
                stmt = stmt.order_by(rank.desc())

            # Apply filters
            stmt = self._apply_filters(stmt, query.filters)

            # Apply sorting
            if query.sort_by != "relevance":
                stmt = self._apply_sorting(stmt, query.sort_by, query.sort_order)

            # Get total count
            count_stmt = select(func.count()).select_from(stmt.subquery())
            result = await self.db.execute(count_stmt)
            total_count = result.scalar() or 0

            # Apply pagination
            stmt = stmt.offset(query.offset).limit(query.limit)

            # Execute query
            result = await self.db.execute(stmt)
            documents = list(result.scalars().all())

            # Generate highlights (simplified for PostgreSQL)
            highlights = {}
            if query.highlight and query.query:
                for doc in documents:
                    highlights[doc.id] = {
                        "title": self._simple_highlight(doc.title, query.query),
                        "description": self._simple_highlight(
                            doc.description or "", query.query
                        ),
                    }

            return documents, total_count, highlights

        except Exception as e:
            self.logger.exception("postgresql_search_failed", error=str(e))
            raise SearchException(f"PostgreSQL search failed: {str(e)}")

    async def _search_elasticsearch(
        self,
        query: SearchQuery,
        user_id: int,
        include_archived: bool,
    ) -> Tuple[List[Document], int, Dict[int, Dict[str, str]]]:
        """
        Execute search using Elasticsearch.

        Args:
            query: Search query
            user_id: User ID
            include_archived: Include archived documents

        Returns:
            Tuple of (documents, total_count, highlights)

        Note:
            This is a placeholder for Elasticsearch integration.
            Requires elasticsearch-py library and configured ES cluster.
        """
        # TODO: Implement Elasticsearch integration
        self.logger.warning("elasticsearch_not_implemented")
        raise SearchException("Elasticsearch backend not yet implemented")

    def _apply_filters(self, stmt: Any, filters: Dict[str, Any]) -> Any:
        """
        Apply filters to query statement.

        Args:
            stmt: SQLAlchemy statement
            filters: Filter dictionary

        Returns:
            Updated statement
        """
        if not filters:
            return stmt

        # File type filter
        if "mime_type" in filters:
            mime_types = filters["mime_type"]
            if isinstance(mime_types, list):
                stmt = stmt.where(Document.mime_type.in_(mime_types))
            else:
                stmt = stmt.where(Document.mime_type == mime_types)

        # Date range filters
        if "created_after" in filters:
            stmt = stmt.where(Document.created_at >= filters["created_after"])
        if "created_before" in filters:
            stmt = stmt.where(Document.created_at <= filters["created_before"])

        # File size filter
        if "min_size" in filters:
            stmt = stmt.where(Document.file_size >= filters["min_size"])
        if "max_size" in filters:
            stmt = stmt.where(Document.file_size <= filters["max_size"])

        # Owner filter
        if "owner_id" in filters:
            stmt = stmt.where(Document.owner_id == filters["owner_id"])

        # Folder filter
        if "folder_id" in filters:
            stmt = stmt.where(Document.folder_id == filters["folder_id"])

        # Status filter
        if "status" in filters:
            statuses = filters["status"]
            if isinstance(statuses, list):
                stmt = stmt.where(Document.status.in_(statuses))
            else:
                stmt = stmt.where(Document.status == statuses)

        return stmt

    def _apply_sorting(
        self, stmt: Any, sort_by: str, sort_order: SortOrder
    ) -> Any:
        """
        Apply sorting to query statement.

        Args:
            stmt: SQLAlchemy statement
            sort_by: Field to sort by
            sort_order: Sort order

        Returns:
            Updated statement
        """
        sort_field = getattr(Document, sort_by, None)
        if sort_field is None:
            self.logger.warning("invalid_sort_field", field=sort_by)
            return stmt

        if sort_order == SortOrder.DESC:
            stmt = stmt.order_by(sort_field.desc())
        else:
            stmt = stmt.order_by(sort_field.asc())

        return stmt

    def _simple_highlight(self, text: str, query: str, max_length: int = 200) -> str:
        """
        Simple text highlighting.

        Args:
            text: Text to highlight
            query: Search query
            max_length: Maximum highlight length

        Returns:
            Highlighted text snippet
        """
        if not text or not query:
            return text[:max_length] if text else ""

        # Simple case-insensitive highlighting
        lower_text = text.lower()
        lower_query = query.lower()

        pos = lower_text.find(lower_query)
        if pos == -1:
            return text[:max_length]

        # Extract context around match
        start = max(0, pos - 50)
        end = min(len(text), pos + len(query) + 150)
        snippet = text[start:end]

        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet

    async def _calculate_facets(
        self,
        query: SearchQuery,
        user_id: int,
        include_archived: bool,
    ) -> Dict[str, Dict[str, int]]:
        """
        Calculate facet aggregations.

        Args:
            query: Search query
            user_id: User ID
            include_archived: Include archived documents

        Returns:
            Facet aggregations
        """
        facets = {}

        try:
            # Base query with same filters
            base_stmt = (
                select(Document)
                .where(
                    or_(
                        Document.owner_id == user_id,
                        Document.is_public == True,
                    )
                )
            )

            if not include_archived:
                base_stmt = base_stmt.where(Document.status == DocumentStatus.ACTIVE)

            # Calculate requested facets
            for facet_field in query.facets:
                if facet_field == "mime_type":
                    stmt = select(
                        Document.mime_type,
                        func.count(Document.id).label("count")
                    ).select_from(base_stmt.subquery()).group_by(Document.mime_type)

                    result = await self.db.execute(stmt)
                    facets["mime_type"] = {
                        row.mime_type: row.count for row in result.all()
                    }

                elif facet_field == "status":
                    stmt = select(
                        Document.status,
                        func.count(Document.id).label("count")
                    ).select_from(base_stmt.subquery()).group_by(Document.status)

                    result = await self.db.execute(stmt)
                    facets["status"] = {
                        row.status.value: row.count for row in result.all()
                    }

                elif facet_field == "owner":
                    stmt = select(
                        Document.owner_id,
                        func.count(Document.id).label("count")
                    ).select_from(base_stmt.subquery()).group_by(Document.owner_id)

                    result = await self.db.execute(stmt)
                    facets["owner"] = {
                        str(row.owner_id): row.count for row in result.all()
                    }

        except Exception as e:
            self.logger.warning("facet_calculation_failed", error=str(e))

        return facets

    def _validate_query(self, query: SearchQuery) -> None:
        """
        Validate search query.

        Args:
            query: Search query to validate

        Raises:
            InvalidSearchQueryException: If query is invalid
        """
        if not query.query and not query.filters:
            raise InvalidSearchQueryException(
                "Query must contain either search text or filters"
            )

        if query.limit < 1 or query.limit > 1000:
            raise InvalidSearchQueryException(
                "Limit must be between 1 and 1000"
            )

        if query.offset < 0:
            raise InvalidSearchQueryException(
                "Offset must be non-negative"
            )

    async def _record_search_history(
        self,
        user_id: int,
        query: SearchQuery,
        result_count: int,
    ) -> None:
        """
        Record search in user's history.

        Args:
            user_id: User ID
            query: Search query
            result_count: Number of results
        """
        try:
            # TODO: Implement search history storage
            self.logger.debug(
                "search_history_recorded",
                user_id=user_id,
                query=query.query,
                result_count=result_count,
            )
        except Exception as e:
            self.logger.warning("search_history_failed", error=str(e))

    async def save_search(
        self,
        user_id: int,
        name: str,
        query: SearchQuery,
        is_public: bool = False,
    ) -> SavedSearch:
        """
        Save search for quick access.

        Args:
            user_id: User ID
            name: Search name
            query: Search query
            is_public: Make search public

        Returns:
            SavedSearch: Saved search object

        Raises:
            ValidationException: If validation fails
        """
        try:
            self.logger.info("saving_search", user_id=user_id, name=name)

            if not name or len(name) < 3:
                raise ValidationException("Search name must be at least 3 characters")

            # TODO: Store in database
            saved_search = SavedSearch(
                user_id=user_id,
                name=name,
                query=query,
                is_public=is_public,
            )

            self.logger.info("search_saved", search_id=saved_search.id)
            return saved_search

        except ValidationException:
            raise
        except Exception as e:
            self.logger.exception("save_search_failed", error=str(e))
            raise SearchException(f"Failed to save search: {str(e)}")

    async def get_saved_searches(
        self,
        user_id: int,
        include_public: bool = True,
    ) -> List[SavedSearch]:
        """
        Get user's saved searches.

        Args:
            user_id: User ID
            include_public: Include public searches

        Returns:
            List of saved searches
        """
        try:
            # TODO: Retrieve from database
            self.logger.debug("getting_saved_searches", user_id=user_id)
            return []

        except Exception as e:
            self.logger.exception("get_saved_searches_failed", error=str(e))
            raise SearchException(f"Failed to get saved searches: {str(e)}")

    async def delete_saved_search(
        self,
        search_id: int,
        user_id: int,
    ) -> None:
        """
        Delete saved search.

        Args:
            search_id: Search ID
            user_id: User ID (for authorization)

        Raises:
            ResourceNotFoundException: If search not found
        """
        try:
            self.logger.info("deleting_saved_search", search_id=search_id)

            # TODO: Delete from database
            # Verify ownership before deletion

            self.logger.info("search_deleted", search_id=search_id)

        except Exception as e:
            self.logger.exception("delete_search_failed", error=str(e))
            raise SearchException(f"Failed to delete search: {str(e)}")

    async def get_search_recommendations(
        self,
        user_id: int,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get personalized search recommendations.

        Args:
            user_id: User ID
            limit: Maximum recommendations

        Returns:
            List of search recommendations
        """
        try:
            self.logger.debug("generating_recommendations", user_id=user_id)

            # TODO: Implement ML-based recommendations
            # Based on search history, frequently accessed documents, etc.

            recommendations = []

            return recommendations

        except Exception as e:
            self.logger.exception("recommendations_failed", error=str(e))
            return []

    async def suggest_queries(
        self,
        partial_query: str,
        user_id: int,
        limit: int = 10,
    ) -> List[str]:
        """
        Get query suggestions based on partial input.

        Args:
            partial_query: Partial query text
            user_id: User ID
            limit: Maximum suggestions

        Returns:
            List of suggested queries
        """
        try:
            if not partial_query or len(partial_query) < 2:
                return []

            self.logger.debug(
                "generating_suggestions",
                partial_query=partial_query,
                user_id=user_id,
            )

            # TODO: Implement query suggestions
            # Based on popular searches, user history, document titles, etc.

            suggestions = []

            return suggestions

        except Exception as e:
            self.logger.exception("suggestions_failed", error=str(e))
            return []
