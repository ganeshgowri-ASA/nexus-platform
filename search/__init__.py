"""
Nexus Platform - Elasticsearch Search Module

Production-ready full-text search engine with:
- Document indexing (async)
- Advanced search with filters, facets, autocomplete
- Relevance scoring and highlighting
- Aggregations and analytics
- Support for documents, emails, files, and chat
"""

from .client import ElasticsearchClient
from .indexer import DocumentIndexer, AsyncIndexer
from .searcher import SearchEngine
from .models import (
    SearchRequest,
    SearchResponse,
    SearchFilters,
    DocumentType,
)

__version__ = "1.0.0"

__all__ = [
    "ElasticsearchClient",
    "DocumentIndexer",
    "AsyncIndexer",
    "SearchEngine",
    "SearchRequest",
    "SearchResponse",
    "SearchFilters",
    "DocumentType",
]
