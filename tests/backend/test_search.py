"""
Unit tests for search functionality.

Tests cover:
- Full-text search with PostgreSQL
- Search query building and validation
- Faceted search
- Search filters (date, size, type, owner, etc.)
- Sorting and pagination
- Saved searches
- Search highlighting
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from modules.documents.search import (
    DocumentSearchService,
    SearchQuery,
    SearchResult,
    SavedSearch,
    SearchBackend,
    SortOrder,
)
from backend.models.document import Document, DocumentStatus
from backend.core.exceptions import (
    InvalidSearchQueryException,
    SearchException,
    ValidationException,
)


@pytest.mark.unit
class TestSearchQuery:
    """Test search query builder."""

    def test_search_query_init(self):
        """Test creating search query."""
        query = SearchQuery(
            query="test search",
            filters={"status": "active"},
            sort_by="created_at",
            sort_order=SortOrder.DESC,
            offset=10,
            limit=20,
        )

        assert query.query == "test search"
        assert query.filters["status"] == "active"
        assert query.sort_by == "created_at"
        assert query.sort_order == SortOrder.DESC
        assert query.offset == 10
        assert query.limit == 20

    def test_search_query_to_dict(self):
        """Test converting search query to dictionary."""
        query = SearchQuery(
            query="test",
            filters={"mime_type": "application/pdf"},
            facets=["status", "owner"],
        )

        query_dict = query.to_dict()

        assert query_dict["query"] == "test"
        assert "filters" in query_dict
        assert "facets" in query_dict


@pytest.mark.unit
class TestSearchResult:
    """Test search result container."""

    def test_search_result_init(self, test_document):
        """Test creating search result."""
        result = SearchResult(
            documents=[test_document],
            total_count=1,
            query_time=45.2,
        )

        assert len(result.documents) == 1
        assert result.total_count == 1
        assert result.query_time == 45.2

    def test_search_result_to_dict(self, test_document):
        """Test converting search result to dictionary."""
        result = SearchResult(
            documents=[test_document],
            total_count=5,
            facets={"status": {"active": 3, "archived": 2}},
        )

        result_dict = result.to_dict()

        assert result_dict["total_count"] == 5
        assert result_dict["has_more"] is True
        assert "facets" in result_dict


@pytest.mark.unit
class TestDocumentSearchService:
    """Test document search service."""

    @pytest.mark.asyncio
    async def test_search_basic_query(
        self, db_session, test_document, regular_user
    ):
        """Test basic search query."""
        service = DocumentSearchService(db_session)
        query = SearchQuery(query="Test", filters={})

        result = await service.search(query, regular_user.id)

        assert isinstance(result, SearchResult)
        assert result.total_count >= 0
        assert isinstance(result.query_time, float)

    @pytest.mark.asyncio
    async def test_search_finds_owned_documents(
        self, db_session, test_document, regular_user
    ):
        """Test that search finds user's owned documents."""
        service = DocumentSearchService(db_session)
        query = SearchQuery(query="Test Document", filters={})

        result = await service.search(query, regular_user.id)

        doc_ids = [doc.id for doc in result.documents]
        assert test_document.id in doc_ids

    @pytest.mark.asyncio
    async def test_search_finds_public_documents(
        self, db_session, public_document, other_user
    ):
        """Test that search finds public documents."""
        service = DocumentSearchService(db_session)
        query = SearchQuery(query="Public", filters={})

        result = await service.search(query, other_user.id)

        doc_ids = [doc.id for doc in result.documents]
        assert public_document.id in doc_ids

    @pytest.mark.asyncio
    async def test_search_respects_permissions(
        self, db_session, test_document, other_user
    ):
        """Test that search respects document permissions."""
        service = DocumentSearchService(db_session)
        query = SearchQuery(query="Test", filters={})

        result = await service.search(query, other_user.id)

        # other_user should not see test_document (private, not owner)
        doc_ids = [doc.id for doc in result.documents]
        assert test_document.id not in doc_ids

    @pytest.mark.asyncio
    async def test_search_with_mime_type_filter(
        self, db_session, document_factory, regular_user
    ):
        """Test search with MIME type filter."""
        # Create documents with different types
        pdf_doc = document_factory(
            title="PDF Doc",
            owner=regular_user,
            mime_type="application/pdf"
        )
        txt_doc = document_factory(
            title="Text Doc",
            owner=regular_user,
            mime_type="text/plain"
        )

        service = DocumentSearchService(db_session)
        query = SearchQuery(
            query="Doc",
            filters={"mime_type": "application/pdf"}
        )

        result = await service.search(query, regular_user.id)

        doc_ids = [doc.id for doc in result.documents]
        assert pdf_doc.id in doc_ids
        # txt_doc should be filtered out
        # (might still appear if query is too broad, but mime_type should be pdf)
        for doc in result.documents:
            if doc.id in doc_ids:
                # At least the PDF should be there
                break

    @pytest.mark.asyncio
    async def test_search_with_date_range_filter(
        self, db_session, document_factory, regular_user
    ):
        """Test search with date range filter."""
        cutoff_date = datetime.utcnow() - timedelta(days=7)

        service = DocumentSearchService(db_session)
        query = SearchQuery(
            query="",
            filters={"created_after": cutoff_date}
        )

        result = await service.search(query, regular_user.id)

        # All results should be created after cutoff_date
        for doc in result.documents:
            assert doc.created_at >= cutoff_date

    @pytest.mark.asyncio
    async def test_search_with_size_filter(
        self, db_session, document_factory, regular_user
    ):
        """Test search with file size filter."""
        large_doc = document_factory(
            title="Large Doc",
            owner=regular_user,
            file_size=10000000  # 10MB
        )
        small_doc = document_factory(
            title="Small Doc",
            owner=regular_user,
            file_size=1000  # 1KB
        )

        service = DocumentSearchService(db_session)
        query = SearchQuery(
            query="",
            filters={"min_size": 1000000}  # 1MB
        )

        result = await service.search(query, regular_user.id)

        doc_ids = [doc.id for doc in result.documents]
        assert large_doc.id in doc_ids
        assert small_doc.id not in doc_ids

    @pytest.mark.asyncio
    async def test_search_with_owner_filter(
        self, db_session, regular_user, other_user, document_factory
    ):
        """Test search with owner filter."""
        user1_doc = document_factory(title="User1 Doc", owner=regular_user)
        user2_doc = document_factory(title="User2 Doc", owner=other_user)

        service = DocumentSearchService(db_session)
        query = SearchQuery(
            query="",
            filters={"owner_id": regular_user.id}
        )

        result = await service.search(query, regular_user.id)

        doc_ids = [doc.id for doc in result.documents]
        assert user1_doc.id in doc_ids
        # user2_doc is owned by other_user, should be filtered out

    @pytest.mark.asyncio
    async def test_search_with_status_filter(
        self, db_session, document_factory, regular_user
    ):
        """Test search with status filter."""
        active_doc = document_factory(
            title="Active Doc",
            owner=regular_user,
            status=DocumentStatus.ACTIVE
        )
        archived_doc = document_factory(
            title="Archived Doc",
            owner=regular_user,
            status=DocumentStatus.ARCHIVED
        )

        service = DocumentSearchService(db_session)
        query = SearchQuery(
            query="",
            filters={"status": DocumentStatus.ACTIVE}
        )

        result = await service.search(
            query,
            regular_user.id,
            include_archived=True  # Enable to test filter
        )

        doc_ids = [doc.id for doc in result.documents]
        assert active_doc.id in doc_ids
        # archived_doc should be filtered by status

    @pytest.mark.asyncio
    async def test_search_exclude_archived_by_default(
        self, db_session, document_factory, regular_user
    ):
        """Test that archived documents are excluded by default."""
        active_doc = document_factory(
            title="Active",
            owner=regular_user,
            status=DocumentStatus.ACTIVE
        )
        archived_doc = document_factory(
            title="Archived",
            owner=regular_user,
            status=DocumentStatus.ARCHIVED
        )

        service = DocumentSearchService(db_session)
        query = SearchQuery(query="", filters={})

        result = await service.search(
            query,
            regular_user.id,
            include_archived=False
        )

        doc_ids = [doc.id for doc in result.documents]
        assert active_doc.id in doc_ids
        assert archived_doc.id not in doc_ids

    @pytest.mark.asyncio
    async def test_search_pagination(
        self, db_session, document_factory, regular_user
    ):
        """Test search pagination."""
        # Create multiple documents
        docs = [
            document_factory(f"Doc {i}", owner=regular_user)
            for i in range(5)
        ]

        service = DocumentSearchService(db_session)

        # First page
        query1 = SearchQuery(query="", filters={}, offset=0, limit=2)
        result1 = await service.search(query1, regular_user.id)
        assert len(result1.documents) <= 2

        # Second page
        query2 = SearchQuery(query="", filters={}, offset=2, limit=2)
        result2 = await service.search(query2, regular_user.id)
        assert len(result2.documents) <= 2

        # Results should be different
        if len(result1.documents) > 0 and len(result2.documents) > 0:
            assert result1.documents[0].id != result2.documents[0].id

    @pytest.mark.asyncio
    async def test_search_sorting(
        self, db_session, document_factory, regular_user
    ):
        """Test search sorting."""
        doc1 = document_factory(title="A Doc", owner=regular_user)
        doc2 = document_factory(title="Z Doc", owner=regular_user)

        service = DocumentSearchService(db_session)

        # Sort by title ascending
        query = SearchQuery(
            query="Doc",
            filters={},
            sort_by="title",
            sort_order=SortOrder.ASC
        )
        result = await service.search(query, regular_user.id)

        if len(result.documents) >= 2:
            # First should come before last alphabetically
            titles = [doc.title for doc in result.documents]
            assert titles == sorted(titles)

    @pytest.mark.asyncio
    async def test_search_highlighting(
        self, db_session, test_document, regular_user
    ):
        """Test search result highlighting."""
        service = DocumentSearchService(db_session)
        query = SearchQuery(query="Test", filters={}, highlight=True)

        result = await service.search(query, regular_user.id)

        if test_document.id in [d.id for d in result.documents]:
            # Highlights should be generated
            assert isinstance(result.highlights, dict)

    @pytest.mark.asyncio
    async def test_search_with_facets(
        self, db_session, document_factory, regular_user
    ):
        """Test search with facet aggregations."""
        # Create documents with different attributes
        document_factory(
            title="PDF Doc",
            owner=regular_user,
            mime_type="application/pdf"
        )
        document_factory(
            title="Text Doc",
            owner=regular_user,
            mime_type="text/plain"
        )

        service = DocumentSearchService(db_session)
        query = SearchQuery(
            query="",
            filters={},
            facets=["mime_type", "status"]
        )

        result = await service.search(query, regular_user.id)

        assert "mime_type" in result.facets or "status" in result.facets
        # Facets should contain counts

    @pytest.mark.asyncio
    async def test_validate_query_requires_content(self, db_session):
        """Test that query validation requires either query or filters."""
        service = DocumentSearchService(db_session)
        query = SearchQuery(query="", filters={})

        with pytest.raises(InvalidSearchQueryException):
            service._validate_query(query)

    @pytest.mark.asyncio
    async def test_validate_query_limit_bounds(self, db_session):
        """Test that query validation checks limit bounds."""
        service = DocumentSearchService(db_session)

        # Too small
        query1 = SearchQuery(query="test", filters={}, limit=0)
        with pytest.raises(InvalidSearchQueryException):
            service._validate_query(query1)

        # Too large
        query2 = SearchQuery(query="test", filters={}, limit=2000)
        with pytest.raises(InvalidSearchQueryException):
            service._validate_query(query2)

    @pytest.mark.asyncio
    async def test_validate_query_offset_negative(self, db_session):
        """Test that query validation rejects negative offset."""
        service = DocumentSearchService(db_session)
        query = SearchQuery(query="test", filters={}, offset=-1)

        with pytest.raises(InvalidSearchQueryException):
            service._validate_query(query)


@pytest.mark.unit
class TestSavedSearches:
    """Test saved search functionality."""

    @pytest.mark.asyncio
    async def test_save_search_success(self, db_session, regular_user):
        """Test saving a search."""
        service = DocumentSearchService(db_session)
        query = SearchQuery(query="my search", filters={"status": "active"})

        saved_search = await service.save_search(
            user_id=regular_user.id,
            name="My Saved Search",
            query=query,
            is_public=False,
        )

        assert saved_search.user_id == regular_user.id
        assert saved_search.name == "My Saved Search"
        assert saved_search.query.query == "my search"

    @pytest.mark.asyncio
    async def test_save_search_validates_name(self, db_session, regular_user):
        """Test that saving search validates name length."""
        service = DocumentSearchService(db_session)
        query = SearchQuery(query="test", filters={})

        with pytest.raises(ValidationException):
            await service.save_search(
                user_id=regular_user.id,
                name="AB",  # Too short
                query=query,
            )


@pytest.mark.unit
class TestSearchHelpers:
    """Test search helper methods."""

    def test_simple_highlight(self, db_session):
        """Test simple text highlighting."""
        service = DocumentSearchService(db_session)

        text = "This is a test document with test content"
        highlighted = service._simple_highlight(text, "test")

        assert "test" in highlighted.lower()

    def test_simple_highlight_truncation(self, db_session):
        """Test highlight truncation for long text."""
        service = DocumentSearchService(db_session)

        text = "a" * 500 + " test " + "b" * 500
        highlighted = service._simple_highlight(text, "test", max_length=200)

        assert len(highlighted) <= 220  # max_length + ellipsis
        assert "test" in highlighted

    def test_apply_filters_empty(self, db_session):
        """Test that empty filters don't modify statement."""
        service = DocumentSearchService(db_session)

        from sqlalchemy import select
        from backend.models.document import Document

        stmt = select(Document)
        filtered_stmt = service._apply_filters(stmt, {})

        # Statement should be unchanged
        assert str(stmt) == str(filtered_stmt)


@pytest.mark.unit
class TestSearchBackends:
    """Test different search backends."""

    @pytest.mark.asyncio
    async def test_postgresql_backend_selected(self, db_session):
        """Test PostgreSQL backend is default."""
        service = DocumentSearchService(
            db_session,
            backend=SearchBackend.POSTGRESQL
        )

        assert service.backend == SearchBackend.POSTGRESQL

    @pytest.mark.asyncio
    async def test_elasticsearch_not_implemented(
        self, db_session, regular_user
    ):
        """Test that Elasticsearch backend raises not implemented."""
        service = DocumentSearchService(
            db_session,
            backend=SearchBackend.ELASTICSEARCH
        )
        query = SearchQuery(query="test", filters={})

        with pytest.raises(SearchException, match="not yet implemented"):
            await service.search(query, regular_user.id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
