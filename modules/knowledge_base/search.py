"""
Semantic Search Module

Advanced search with NLP, vector embeddings, question answering, and filters.
Integrates with Elasticsearch for full-text search and vector databases for semantic search.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from .kb_types import (
    AccessLevel,
    ContentType,
    Language,
    SearchQuery,
    SearchResult,
)
from .models import Article, FAQ, GlossaryTerm, Tutorial, Video

logger = logging.getLogger(__name__)


class SearchEngine:
    """
    Advanced search engine with semantic search, NLP, and filtering.

    Features:
    - Full-text search with Elasticsearch
    - Semantic search with vector embeddings
    - Natural language question answering
    - Autocomplete and suggestions
    - Multi-faceted filtering
    - Search analytics
    """

    def __init__(
        self,
        db_session: Session,
        es_client: Optional[Any] = None,
        vector_db_client: Optional[Any] = None,
        embedding_model: Optional[Any] = None,
    ):
        """
        Initialize the SearchEngine.

        Args:
            db_session: SQLAlchemy database session
            es_client: Elasticsearch client (optional)
            vector_db_client: Vector database client (Pinecone/Weaviate)
            embedding_model: Model for generating embeddings
        """
        self.db = db_session
        self.es = es_client
        self.vector_db = vector_db_client
        self.embedding_model = embedding_model

    async def search(
        self,
        query: str,
        content_types: Optional[List[ContentType]] = None,
        categories: Optional[List[UUID]] = None,
        tags: Optional[List[str]] = None,
        languages: Optional[List[Language]] = None,
        access_levels: Optional[List[AccessLevel]] = None,
        min_rating: Optional[float] = None,
        limit: int = 20,
        offset: int = 0,
        use_semantic: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive search across KB content.

        Args:
            query: Search query
            content_types: Filter by content types
            categories: Filter by categories
            tags: Filter by tags
            languages: Filter by languages
            access_levels: Filter by access levels
            min_rating: Minimum rating filter
            limit: Number of results
            offset: Offset for pagination
            use_semantic: Use semantic search with embeddings

        Returns:
            Dictionary with search results and metadata
        """
        try:
            # Perform semantic search if enabled and available
            if use_semantic and self.embedding_model:
                semantic_results = await self._semantic_search(
                    query,
                    content_types,
                    limit,
                )
            else:
                semantic_results = []

            # Perform traditional full-text search
            if self.es:
                fulltext_results = await self._elasticsearch_search(
                    query,
                    content_types,
                    categories,
                    tags,
                    languages,
                    access_levels,
                    min_rating,
                    limit,
                    offset,
                )
            else:
                fulltext_results = await self._database_search(
                    query,
                    content_types,
                    categories,
                    tags,
                    languages,
                    access_levels,
                    min_rating,
                    limit,
                    offset,
                )

            # Merge and rank results
            merged_results = self._merge_results(semantic_results, fulltext_results)

            return {
                "results": merged_results[:limit],
                "total": len(merged_results),
                "query": query,
                "limit": limit,
                "offset": offset,
            }

        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            raise

    async def question_answering(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Answer questions using KB content with NLP.

        Args:
            question: User's question
            top_k: Number of relevant articles to consider

        Returns:
            Dictionary with answer and source articles
        """
        try:
            # Find relevant articles
            search_results = await self.search(
                question,
                use_semantic=True,
                limit=top_k,
            )

            # Extract answer from top articles (simplified version)
            # In production, use a QA model like BERT or GPT
            answer_snippets = []
            sources = []

            for result in search_results["results"][:3]:
                answer_snippets.append(result.get("snippet", ""))
                sources.append({
                    "id": result["id"],
                    "title": result["title"],
                    "url": result["url"],
                })

            # Combine snippets for answer (simplified)
            answer = " ".join(answer_snippets)

            return {
                "question": question,
                "answer": answer,
                "sources": sources,
                "confidence": 0.8,  # Placeholder
            }

        except Exception as e:
            logger.error(f"Error in question answering: {str(e)}")
            raise

    async def autocomplete(
        self,
        partial_query: str,
        limit: int = 10,
    ) -> List[str]:
        """
        Provide autocomplete suggestions.

        Args:
            partial_query: Partial search query
            limit: Number of suggestions

        Returns:
            List of suggested queries
        """
        try:
            suggestions = []

            # Search article titles
            articles = (
                self.db.query(Article.title)
                .filter(Article.title.ilike(f"%{partial_query}%"))
                .filter(Article.status == "published")
                .limit(limit)
                .all()
            )

            suggestions.extend([a.title for a in articles])

            # Search FAQ questions
            faqs = (
                self.db.query(FAQ.question)
                .filter(FAQ.question.ilike(f"%{partial_query}%"))
                .limit(limit - len(suggestions))
                .all()
            )

            suggestions.extend([f.question for f in faqs])

            return suggestions[:limit]

        except Exception as e:
            logger.error(f"Error in autocomplete: {str(e)}")
            raise

    async def get_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """
        Get search suggestions based on query.

        Args:
            query: Search query
            limit: Number of suggestions

        Returns:
            List of suggested searches
        """
        try:
            # Get popular related searches (simplified)
            suggestions = []

            # Add related terms from glossary
            terms = (
                self.db.query(GlossaryTerm.term)
                .filter(GlossaryTerm.term.ilike(f"%{query}%"))
                .limit(limit)
                .all()
            )

            suggestions.extend([t.term for t in terms])

            return suggestions

        except Exception as e:
            logger.error(f"Error getting suggestions: {str(e)}")
            raise

    async def _semantic_search(
        self,
        query: str,
        content_types: Optional[List[ContentType]],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector embeddings.

        Args:
            query: Search query
            content_types: Filter by content types
            limit: Number of results

        Returns:
            List of search results with relevance scores
        """
        try:
            if not self.embedding_model or not self.vector_db:
                return []

            # Generate query embedding
            query_embedding = await self._generate_embedding(query)

            # Search vector database
            results = await self.vector_db.query(
                vector=query_embedding,
                top_k=limit,
                include_metadata=True,
            )

            # Format results
            search_results = []
            for match in results.get("matches", []):
                metadata = match.get("metadata", {})
                search_results.append({
                    "id": metadata.get("id"),
                    "title": metadata.get("title"),
                    "snippet": metadata.get("snippet"),
                    "content_type": metadata.get("content_type"),
                    "url": metadata.get("url"),
                    "relevance_score": match.get("score", 0.0),
                })

            return search_results

        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return []

    async def _elasticsearch_search(
        self,
        query: str,
        content_types: Optional[List[ContentType]],
        categories: Optional[List[UUID]],
        tags: Optional[List[str]],
        languages: Optional[List[Language]],
        access_levels: Optional[List[AccessLevel]],
        min_rating: Optional[float],
        limit: int,
        offset: int,
    ) -> List[Dict[str, Any]]:
        """
        Perform full-text search using Elasticsearch.

        Args:
            query: Search query
            content_types: Filter by content types
            categories: Filter by categories
            tags: Filter by tags
            languages: Filter by languages
            access_levels: Filter by access levels
            min_rating: Minimum rating
            limit: Number of results
            offset: Offset for pagination

        Returns:
            List of search results
        """
        try:
            if not self.es:
                return []

            # Build Elasticsearch query
            must_clauses = [
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^3", "summary^2", "content"],
                        "fuzziness": "AUTO",
                    }
                }
            ]

            filter_clauses = []

            if content_types:
                filter_clauses.append({
                    "terms": {"content_type": [ct.value for ct in content_types]}
                })

            if categories:
                filter_clauses.append({
                    "terms": {"category_id": [str(c) for c in categories]}
                })

            if tags:
                filter_clauses.append({"terms": {"tags": tags}})

            if languages:
                filter_clauses.append({
                    "terms": {"language": [lang.value for lang in languages]}
                })

            if access_levels:
                filter_clauses.append({
                    "terms": {"access_level": [al.value for al in access_levels]}
                })

            if min_rating:
                filter_clauses.append({
                    "range": {"average_rating": {"gte": min_rating}}
                })

            # Execute search
            es_query = {
                "query": {
                    "bool": {
                        "must": must_clauses,
                        "filter": filter_clauses,
                    }
                },
                "highlight": {
                    "fields": {
                        "title": {},
                        "content": {"fragment_size": 150},
                    }
                },
                "from": offset,
                "size": limit,
            }

            response = await self.es.search(index="kb_content", body=es_query)

            # Format results
            results = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                highlights = hit.get("highlight", {})

                results.append({
                    "id": source["id"],
                    "title": source["title"],
                    "snippet": highlights.get("content", [source.get("summary", "")])[0],
                    "content_type": source["content_type"],
                    "url": f"/kb/{source['content_type']}/{source['slug']}",
                    "relevance_score": hit["_score"],
                    "highlights": highlights,
                })

            return results

        except Exception as e:
            logger.error(f"Error in Elasticsearch search: {str(e)}")
            return []

    async def _database_search(
        self,
        query: str,
        content_types: Optional[List[ContentType]],
        categories: Optional[List[UUID]],
        tags: Optional[List[str]],
        languages: Optional[List[Language]],
        access_levels: Optional[List[AccessLevel]],
        min_rating: Optional[float],
        limit: int,
        offset: int,
    ) -> List[Dict[str, Any]]:
        """
        Perform basic database search (fallback when Elasticsearch unavailable).

        Args:
            Same as _elasticsearch_search

        Returns:
            List of search results
        """
        try:
            results = []

            # Search articles
            if not content_types or ContentType.ARTICLE in content_types:
                article_query = self.db.query(Article).filter(
                    or_(
                        Article.title.ilike(f"%{query}%"),
                        Article.summary.ilike(f"%{query}%"),
                        Article.content.ilike(f"%{query}%"),
                    )
                )

                # Apply filters
                if categories:
                    article_query = article_query.filter(Article.category_id.in_(categories))

                if languages:
                    article_query = article_query.filter(
                        Article.language.in_([lang.value for lang in languages])
                    )

                if access_levels:
                    article_query = article_query.filter(
                        Article.access_level.in_([al.value for al in access_levels])
                    )

                if min_rating:
                    article_query = article_query.filter(Article.average_rating >= min_rating)

                articles = article_query.limit(limit).offset(offset).all()

                for article in articles:
                    results.append({
                        "id": str(article.id),
                        "title": article.title,
                        "snippet": article.summary or article.content[:200],
                        "content_type": "article",
                        "url": f"/kb/article/{article.slug}",
                        "relevance_score": 1.0,
                    })

            return results

        except Exception as e:
            logger.error(f"Error in database search: {str(e)}")
            return []

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate vector embedding for text.

        Args:
            text: Text to embed

        Returns:
            Vector embedding
        """
        try:
            if not self.embedding_model:
                return []

            # Use embedding model (e.g., sentence-transformers)
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return []

    def _merge_results(
        self,
        semantic_results: List[Dict[str, Any]],
        fulltext_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Merge and rank results from different search methods.

        Args:
            semantic_results: Results from semantic search
            fulltext_results: Results from full-text search

        Returns:
            Merged and ranked results
        """
        # Create a dictionary to deduplicate results
        results_dict = {}

        # Add semantic results with boosted scores
        for result in semantic_results:
            result_id = result["id"]
            result["combined_score"] = result.get("relevance_score", 0) * 1.2
            results_dict[result_id] = result

        # Add full-text results
        for result in fulltext_results:
            result_id = result["id"]
            if result_id in results_dict:
                # Boost score if found in both
                results_dict[result_id]["combined_score"] += result.get("relevance_score", 0)
            else:
                result["combined_score"] = result.get("relevance_score", 0)
                results_dict[result_id] = result

        # Sort by combined score
        merged = sorted(
            results_dict.values(),
            key=lambda x: x.get("combined_score", 0),
            reverse=True,
        )

        return merged


class SearchIndexer:
    """
    Manager for indexing content in search engines.

    Handles indexing for both Elasticsearch and vector databases.
    """

    def __init__(
        self,
        db_session: Session,
        es_client: Optional[Any] = None,
        vector_db_client: Optional[Any] = None,
        embedding_model: Optional[Any] = None,
    ):
        """
        Initialize the SearchIndexer.

        Args:
            db_session: SQLAlchemy database session
            es_client: Elasticsearch client
            vector_db_client: Vector database client
            embedding_model: Embedding model
        """
        self.db = db_session
        self.es = es_client
        self.vector_db = vector_db_client
        self.embedding_model = embedding_model

    async def index_article(self, article: Article) -> bool:
        """
        Index an article in search engines.

        Args:
            article: Article to index

        Returns:
            True if successful
        """
        try:
            # Index in Elasticsearch
            if self.es:
                await self._index_in_elasticsearch(article)

            # Index in vector database
            if self.vector_db and self.embedding_model:
                await self._index_in_vector_db(article)

            logger.info(f"Indexed article: {article.id}")
            return True

        except Exception as e:
            logger.error(f"Error indexing article: {str(e)}")
            return False

    async def _index_in_elasticsearch(self, article: Article) -> None:
        """Index article in Elasticsearch."""
        doc = {
            "id": str(article.id),
            "title": article.title,
            "slug": article.slug,
            "summary": article.summary,
            "content": article.content,
            "content_type": article.content_type,
            "status": article.status,
            "language": article.language,
            "category_id": str(article.category_id) if article.category_id else None,
            "tags": [tag.name for tag in article.tags],
            "average_rating": article.average_rating,
            "created_at": article.created_at.isoformat(),
        }

        await self.es.index(index="kb_content", id=str(article.id), body=doc)

    async def _index_in_vector_db(self, article: Article) -> None:
        """Index article in vector database."""
        # Generate embedding
        text = f"{article.title} {article.summary} {article.content[:500]}"
        embedding = await self._generate_embedding(text)

        # Store in vector DB
        await self.vector_db.upsert(
            vectors=[{
                "id": str(article.id),
                "values": embedding,
                "metadata": {
                    "id": str(article.id),
                    "title": article.title,
                    "snippet": article.summary or article.content[:200],
                    "content_type": article.content_type,
                    "url": f"/kb/article/{article.slug}",
                },
            }]
        )

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if not self.embedding_model:
            return []

        embedding = self.embedding_model.encode(text)
        return embedding.tolist()
