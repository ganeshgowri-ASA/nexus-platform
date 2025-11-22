"""Tests for search functionality."""

import pytest
from datetime import datetime
from search.models import (
    DocumentType,
    SearchRequest,
    SearchFilters,
    FacetRequest,
    EmailDocument,
)
from search.searcher import SearchEngine
from search.indexer import DocumentIndexer


@pytest.fixture
async def search_engine():
    """Create search engine instance."""
    return SearchEngine()


@pytest.fixture
async def document_indexer():
    """Create document indexer instance."""
    indexer = DocumentIndexer()
    await indexer.initialize_indices()
    return indexer


@pytest.mark.asyncio
async def test_search_basic(search_engine, document_indexer):
    """Test basic search functionality."""
    # Index a test document
    email = EmailDocument(
        id="test-1",
        title="Test Email",
        subject="Test Email",
        content="This is a test email for searching",
        sender="test@example.com",
        recipients=["user@example.com"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        owner_id="user-1",
        owner_name="Test User",
    )

    await document_indexer.index_document(email, refresh=True)

    # Search for the document
    request = SearchRequest(query="test email")
    response = await search_engine.search(request)

    assert response.total > 0
    assert len(response.hits) > 0
    assert response.hits[0].title == "Test Email"


@pytest.mark.asyncio
async def test_search_with_filters(search_engine, document_indexer):
    """Test search with filters."""
    # Index test documents
    for i in range(5):
        email = EmailDocument(
            id=f"test-{i}",
            title=f"Email {i}",
            subject=f"Email {i}",
            content=f"Test content {i}",
            sender="test@example.com",
            recipients=["user@example.com"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            owner_id="user-1",
            owner_name="Test User",
            tags=["important"] if i % 2 == 0 else [],
        )
        await document_indexer.index_document(email)

    # Search with filters
    filters = SearchFilters(
        document_types=[DocumentType.EMAIL],
        tags=["important"],
    )
    request = SearchRequest(query="email", filters=filters)
    response = await search_engine.search(request)

    assert response.total >= 3  # Should find emails with "important" tag


@pytest.mark.asyncio
async def test_search_with_facets(search_engine, document_indexer):
    """Test search with facets."""
    request = SearchRequest(
        query="test",
        facets=[
            FacetRequest(field="type"),
            FacetRequest(field="tags"),
        ],
    )

    response = await search_engine.search(request)

    assert len(response.facets) > 0
    # Check that facets have buckets
    for facet in response.facets:
        assert facet.field in ["type", "tags"]


@pytest.mark.asyncio
async def test_search_autocomplete(search_engine):
    """Test autocomplete search."""
    request = SearchRequest(
        query="tes",
        autocomplete=True,
    )

    response = await search_engine.search(request)

    # Should return suggestions
    assert isinstance(response.suggestions, list)


@pytest.mark.asyncio
async def test_search_highlighting(search_engine):
    """Test search result highlighting."""
    request = SearchRequest(
        query="test",
        highlight=True,
        highlight_fields=["title", "content"],
    )

    response = await search_engine.search(request)

    if response.total > 0:
        # Check that hits have highlights
        for hit in response.hits:
            if hit.highlights:
                assert any(
                    "<mark>" in fragment
                    for hl in hit.highlights
                    for fragment in hl.fragments
                )


@pytest.mark.asyncio
async def test_pagination(search_engine):
    """Test search pagination."""
    # First page
    request1 = SearchRequest(query="test", page=1, page_size=5)
    response1 = await search_engine.search(request1)

    # Second page
    request2 = SearchRequest(query="test", page=2, page_size=5)
    response2 = await search_engine.search(request2)

    assert response1.page == 1
    assert response2.page == 2

    if response1.total > 5:
        # Ensure different results on different pages
        assert response1.hits[0].id != response2.hits[0].id


@pytest.mark.asyncio
async def test_bulk_indexing(document_indexer):
    """Test bulk document indexing."""
    documents = [
        EmailDocument(
            id=f"bulk-{i}",
            title=f"Bulk Email {i}",
            subject=f"Bulk Email {i}",
            content=f"Bulk content {i}",
            sender="bulk@example.com",
            recipients=["user@example.com"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            owner_id="user-1",
            owner_name="Test User",
        )
        for i in range(10)
    ]

    result = await document_indexer.index_documents_bulk(documents, refresh=True)

    assert result["success"] == 10
    assert result["failed"] == 0


@pytest.mark.asyncio
async def test_document_update(document_indexer):
    """Test updating a document."""
    # Index initial document
    email = EmailDocument(
        id="update-test",
        title="Original Title",
        subject="Original Title",
        content="Original content",
        sender="test@example.com",
        recipients=["user@example.com"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        owner_id="user-1",
        owner_name="Test User",
    )

    await document_indexer.index_document(email, refresh=True)

    # Update document
    success = await document_indexer.update_document(
        doc_id="update-test",
        doc_type=DocumentType.EMAIL,
        partial_doc={"title": "Updated Title"},
        refresh=True,
    )

    assert success


@pytest.mark.asyncio
async def test_document_deletion(document_indexer):
    """Test deleting a document."""
    # Index document
    email = EmailDocument(
        id="delete-test",
        title="To Be Deleted",
        subject="To Be Deleted",
        content="This will be deleted",
        sender="test@example.com",
        recipients=["user@example.com"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        owner_id="user-1",
        owner_name="Test User",
    )

    await document_indexer.index_document(email, refresh=True)

    # Delete document
    success = await document_indexer.delete_document(
        doc_id="delete-test",
        doc_type=DocumentType.EMAIL,
        refresh=True,
    )

    assert success
