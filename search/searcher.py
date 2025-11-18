"""Advanced search engine with filters, facets, autocomplete, and highlighting."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .client import es_client
from .config import settings
from .models import (
    DocumentType,
    FacetBucket,
    FacetRequest,
    FacetResult,
    HighlightedText,
    SearchFilters,
    SearchHit,
    SearchRequest,
    SearchResponse,
    SortOrder,
)

logger = logging.getLogger(__name__)


class SearchEngine:
    """Production-ready search engine with advanced features."""

    def __init__(self):
        """Initialize search engine."""
        pass

    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Execute a comprehensive search with all features.

        Features:
        - Full-text search with relevance scoring
        - Filters (document types, dates, owners, tags, etc.)
        - Faceted search
        - Autocomplete
        - Highlighting
        - Pagination
        - Sorting
        """
        start_time = datetime.utcnow()

        # Build the search query
        query = self._build_query(request)

        # Build aggregations for facets
        aggregations = self._build_aggregations(request.facets)

        # Build highlighting configuration
        highlight = self._build_highlight(request)

        # Build sort configuration
        sort = self._build_sort(request)

        # Determine indices to search
        indices = self._get_search_indices(request.filters)

        # Calculate pagination
        from_offset = (request.page - 1) * request.page_size

        try:
            # Execute search
            async with es_client.get_client() as client:
                response = await client.search(
                    index=indices,
                    query=query,
                    aggregations=aggregations,
                    highlight=highlight,
                    sort=sort,
                    from_=from_offset,
                    size=request.page_size,
                    track_total_hits=True,
                )

            # Parse response
            total = response["hits"]["total"]["value"]
            total_pages = (total + request.page_size - 1) // request.page_size

            # Parse hits
            hits = self._parse_hits(response["hits"]["hits"])

            # Parse facets
            facets = self._parse_aggregations(response.get("aggregations", {}))

            # Generate suggestions if autocomplete is enabled
            suggestions = []
            if request.autocomplete and request.query:
                suggestions = await self._get_suggestions(request.query, indices)

            # Calculate elapsed time
            took_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            return SearchResponse(
                query=request.query,
                total=total,
                page=request.page,
                page_size=request.page_size,
                total_pages=total_pages,
                hits=hits,
                facets=facets,
                took_ms=took_ms,
                suggestions=suggestions,
            )

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def _build_query(self, request: SearchRequest) -> Dict[str, Any]:
        """Build Elasticsearch query DSL."""
        must_clauses = []
        filter_clauses = []

        # Main search query
        if request.query.strip():
            if request.autocomplete:
                # Autocomplete query using edge n-grams
                must_clauses.append({
                    "multi_match": {
                        "query": request.query,
                        "fields": [
                            "title.autocomplete^3",
                            "subject.autocomplete^2",
                            "file_name.autocomplete^2",
                        ],
                        "type": "bool_prefix",
                    }
                })
            else:
                # Standard multi-field search with boosting
                must_clauses.append({
                    "multi_match": {
                        "query": request.query,
                        "fields": [
                            "title^3",
                            "subject^2",
                            "file_name^2",
                            "content",
                            "message",
                            "sender",
                            "owner_name",
                        ],
                        "type": "best_fields",
                        "operator": request.operator.value,
                        "fuzziness": "AUTO",
                    }
                })
        else:
            # Match all if no query
            must_clauses.append({"match_all": {}})

        # Apply filters
        if request.filters:
            filter_clauses.extend(self._build_filters(request.filters))

        # Combine queries
        query = {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses,
            }
        }

        return query

    def _build_filters(self, filters: SearchFilters) -> List[Dict[str, Any]]:
        """Build filter clauses from SearchFilters."""
        filter_clauses = []

        # Document type filter
        if filters.document_types:
            filter_clauses.append({
                "terms": {
                    "type": [dt.value for dt in filters.document_types]
                }
            })

        # Owner filter
        if filters.owner_ids:
            filter_clauses.append({
                "terms": {"owner_id": filters.owner_ids}
            })

        # Tags filter
        if filters.tags:
            filter_clauses.append({
                "terms": {"tags": filters.tags}
            })

        # Date range filter
        if filters.date_from or filters.date_to:
            date_range = {}
            if filters.date_from:
                date_range["gte"] = filters.date_from.isoformat()
            if filters.date_to:
                date_range["lte"] = filters.date_to.isoformat()

            filter_clauses.append({
                "range": {"created_at": date_range}
            })

        # File type filter
        if filters.file_types:
            filter_clauses.append({
                "terms": {"file_type": filters.file_types}
            })

        # Folder filter
        if filters.folders:
            filter_clauses.append({
                "terms": {"folder": filters.folders}
            })

        # Attachments filter
        if filters.has_attachments is not None:
            filter_clauses.append({
                "term": {"has_attachments": filters.has_attachments}
            })

        # Custom filters
        for field, value in filters.custom_filters.items():
            if isinstance(value, list):
                filter_clauses.append({"terms": {field: value}})
            else:
                filter_clauses.append({"term": {field: value}})

        return filter_clauses

    def _build_aggregations(
        self,
        facet_requests: Optional[List[FacetRequest]],
    ) -> Optional[Dict[str, Any]]:
        """Build aggregations for faceted search."""
        if not facet_requests:
            return None

        aggregations = {}

        for facet in facet_requests:
            aggregations[facet.field] = {
                "terms": {
                    "field": facet.field,
                    "size": facet.size,
                    "min_doc_count": facet.min_count,
                }
            }

        return aggregations

    def _build_highlight(
        self,
        request: SearchRequest,
    ) -> Optional[Dict[str, Any]]:
        """Build highlighting configuration."""
        if not request.highlight:
            return None

        fields = request.highlight_fields or [
            "title",
            "content",
            "subject",
            "message",
        ]

        highlight_config = {
            "fields": {field: {} for field in fields},
            "pre_tags": ["<mark>"],
            "post_tags": ["</mark>"],
            "number_of_fragments": 3,
            "fragment_size": 150,
        }

        return highlight_config

    def _build_sort(self, request: SearchRequest) -> Optional[List[Dict[str, Any]]]:
        """Build sort configuration."""
        if not request.sort_by:
            # Default sort by relevance score
            return [{"_score": {"order": "desc"}}]

        sort_field = request.sort_by
        sort_order = request.sort_order.value

        # Use keyword field for text fields
        if sort_field in ["title", "owner_name", "sender"]:
            sort_field = f"{sort_field}.keyword"

        return [{sort_field: {"order": sort_order}}]

    def _get_search_indices(
        self,
        filters: Optional[SearchFilters],
    ) -> str:
        """Determine which indices to search based on filters."""
        if filters and filters.document_types:
            # Search specific document types
            indices = [
                settings.get_index_name(dt.value)
                for dt in filters.document_types
            ]
            return ",".join(indices)
        else:
            # Search all indices
            return f"{settings.elasticsearch_index_prefix}_*"

    def _parse_hits(self, hits: List[Dict[str, Any]]) -> List[SearchHit]:
        """Parse search hits from Elasticsearch response."""
        parsed_hits = []

        for hit in hits:
            source = hit["_source"]
            highlights = []

            # Parse highlights
            if "highlight" in hit:
                for field, fragments in hit["highlight"].items():
                    highlights.append(
                        HighlightedText(field=field, fragments=fragments)
                    )

            parsed_hits.append(
                SearchHit(
                    id=source["id"],
                    type=DocumentType(source["type"]),
                    title=source.get("title", ""),
                    content=source.get("content", ""),
                    score=hit["_score"],
                    highlights=highlights,
                    metadata=source.get("metadata", {}),
                    created_at=datetime.fromisoformat(source["created_at"]),
                    updated_at=datetime.fromisoformat(source["updated_at"]),
                )
            )

        return parsed_hits

    def _parse_aggregations(
        self,
        aggregations: Dict[str, Any],
    ) -> List[FacetResult]:
        """Parse aggregations into facet results."""
        facets = []

        for field, agg_data in aggregations.items():
            if "buckets" in agg_data:
                buckets = [
                    FacetBucket(key=bucket["key"], count=bucket["doc_count"])
                    for bucket in agg_data["buckets"]
                ]
                facets.append(FacetResult(field=field, buckets=buckets))

        return facets

    async def _get_suggestions(
        self,
        query: str,
        indices: str,
    ) -> List[str]:
        """Get autocomplete suggestions."""
        try:
            async with es_client.get_client() as client:
                response = await client.search(
                    index=indices,
                    query={
                        "multi_match": {
                            "query": query,
                            "fields": [
                                "title.autocomplete",
                                "subject.autocomplete",
                                "file_name.autocomplete",
                            ],
                            "type": "bool_prefix",
                        }
                    },
                    size=5,
                    _source=["title", "subject", "file_name"],
                )

            suggestions = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                # Extract suggestion from available fields
                suggestion = (
                    source.get("title")
                    or source.get("subject")
                    or source.get("file_name")
                )
                if suggestion and suggestion not in suggestions:
                    suggestions.append(suggestion)

            return suggestions[:5]

        except Exception as e:
            logger.error(f"Failed to get suggestions: {e}")
            return []

    async def get_similar_documents(
        self,
        doc_id: str,
        doc_type: DocumentType,
        limit: int = 10,
    ) -> List[SearchHit]:
        """Find similar documents using More Like This query."""
        index_name = settings.get_index_name(doc_type.value)

        try:
            async with es_client.get_client() as client:
                response = await client.search(
                    index=index_name,
                    query={
                        "more_like_this": {
                            "fields": ["title", "content"],
                            "like": [{"_index": index_name, "_id": doc_id}],
                            "min_term_freq": 1,
                            "min_doc_freq": 1,
                            "max_query_terms": 25,
                        }
                    },
                    size=limit,
                )

            return self._parse_hits(response["hits"]["hits"])

        except Exception as e:
            logger.error(f"Failed to get similar documents: {e}")
            return []

    async def count_documents(
        self,
        filters: Optional[SearchFilters] = None,
    ) -> Dict[DocumentType, int]:
        """Count documents by type with optional filters."""
        counts = {}

        for doc_type in DocumentType:
            index_name = settings.get_index_name(doc_type.value)

            query = {"match_all": {}}
            if filters:
                filter_clauses = self._build_filters(filters)
                if filter_clauses:
                    query = {"bool": {"filter": filter_clauses}}

            try:
                async with es_client.get_client() as client:
                    response = await client.count(index=index_name, query=query)
                    counts[doc_type] = response["count"]
            except Exception as e:
                logger.error(f"Failed to count documents for {doc_type}: {e}")
                counts[doc_type] = 0

        return counts


# Global search engine instance
search_engine = SearchEngine()
