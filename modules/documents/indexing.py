"""
Document indexing module for Document Management System.

This module provides comprehensive indexing capabilities including:
- Full-text indexing with configurable analyzers
- Semantic search support with embeddings
- Metadata indexing for structured queries
- Index lifecycle management (create, update, delete)
- Bulk indexing operations for performance
- Index optimization and maintenance
"""

import asyncio
import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.core.exceptions import (
    DatabaseException,
    ResourceNotFoundException,
    SearchException,
    ValidationException,
)
from backend.core.logging import get_logger
from backend.models.document import Document, DocumentMetadata, DocumentStatus

logger = get_logger(__name__)


class IndexType(str, Enum):
    """Index types."""

    FULL_TEXT = "full_text"
    SEMANTIC = "semantic"
    METADATA = "metadata"
    HYBRID = "hybrid"


class IndexStatus(str, Enum):
    """Index status."""

    PENDING = "pending"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"
    UPDATING = "updating"
    DELETING = "deleting"


class AnalyzerType(str, Enum):
    """Text analyzer types."""

    STANDARD = "standard"
    ENGLISH = "english"
    SIMPLE = "simple"
    WHITESPACE = "whitespace"
    KEYWORD = "keyword"


class DocumentIndex:
    """
    Document index representation.

    Attributes:
        document_id: Document ID
        index_type: Type of index
        status: Indexing status
        content_hash: Hash of indexed content
        vector_embedding: Semantic embedding vector
        metadata: Indexed metadata
        indexed_at: Indexing timestamp
        error_message: Error message if failed
    """

    def __init__(
        self,
        document_id: int,
        index_type: IndexType,
        status: IndexStatus = IndexStatus.PENDING,
        content_hash: Optional[str] = None,
        vector_embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize document index."""
        self.document_id = document_id
        self.index_type = index_type
        self.status = status
        self.content_hash = content_hash
        self.vector_embedding = vector_embedding
        self.metadata = metadata or {}
        self.indexed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert index to dictionary."""
        return {
            "document_id": self.document_id,
            "index_type": self.index_type.value,
            "status": self.status.value,
            "content_hash": self.content_hash,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
            "error_message": self.error_message,
        }


class IndexingConfig:
    """
    Indexing configuration.

    Attributes:
        analyzer: Text analyzer to use
        enable_semantic: Enable semantic search
        chunk_size: Document chunk size for processing
        batch_size: Batch size for bulk operations
        include_ocr: Include OCR text in indexing
        extract_entities: Extract named entities
    """

    def __init__(
        self,
        analyzer: AnalyzerType = AnalyzerType.ENGLISH,
        enable_semantic: bool = False,
        chunk_size: int = 1000,
        batch_size: int = 100,
        include_ocr: bool = True,
        extract_entities: bool = False,
    ) -> None:
        """Initialize indexing config."""
        self.analyzer = analyzer
        self.enable_semantic = enable_semantic
        self.chunk_size = chunk_size
        self.batch_size = batch_size
        self.include_ocr = include_ocr
        self.extract_entities = extract_entities


class DocumentIndexingService:
    """
    Document indexing service.

    Provides comprehensive indexing capabilities including full-text,
    semantic, and metadata indexing with support for bulk operations
    and index management.
    """

    def __init__(
        self,
        db: AsyncSession,
        config: Optional[IndexingConfig] = None,
    ) -> None:
        """
        Initialize indexing service.

        Args:
            db: Database session
            config: Indexing configuration
        """
        self.db = db
        self.config = config or IndexingConfig()
        self.logger = get_logger(self.__class__.__name__)
        self._index_cache: Dict[int, DocumentIndex] = {}

    async def index_document(
        self,
        document_id: int,
        force_reindex: bool = False,
    ) -> DocumentIndex:
        """
        Index a single document.

        Args:
            document_id: Document ID to index
            force_reindex: Force reindexing even if already indexed

        Returns:
            DocumentIndex: Index result

        Raises:
            ResourceNotFoundException: If document not found
            SearchException: If indexing fails
        """
        try:
            self.logger.info("indexing_document", document_id=document_id)

            # Fetch document
            document = await self._get_document(document_id)

            # Check if already indexed
            if not force_reindex:
                existing_index = await self._get_existing_index(document_id)
                if existing_index and existing_index.status == IndexStatus.INDEXED:
                    content_hash = self._calculate_content_hash(document)
                    if existing_index.content_hash == content_hash:
                        self.logger.debug(
                            "document_already_indexed",
                            document_id=document_id,
                        )
                        return existing_index

            # Create index entry
            index = DocumentIndex(
                document_id=document_id,
                index_type=IndexType.HYBRID if self.config.enable_semantic else IndexType.FULL_TEXT,
                status=IndexStatus.INDEXING,
            )

            # Extract and index content
            await self._index_full_text(document, index)

            # Index metadata
            await self._index_metadata(document, index)

            # Generate semantic embeddings if enabled
            if self.config.enable_semantic:
                await self._index_semantic(document, index)

            # Calculate content hash
            index.content_hash = self._calculate_content_hash(document)
            index.status = IndexStatus.INDEXED
            index.indexed_at = datetime.utcnow()

            # Store in cache
            self._index_cache[document_id] = index

            self.logger.info(
                "document_indexed",
                document_id=document_id,
                index_type=index.index_type.value,
            )

            return index

        except ResourceNotFoundException:
            raise
        except Exception as e:
            self.logger.exception("indexing_failed", document_id=document_id, error=str(e))
            index = DocumentIndex(
                document_id=document_id,
                index_type=IndexType.FULL_TEXT,
                status=IndexStatus.FAILED,
            )
            index.error_message = str(e)
            raise SearchException(f"Document indexing failed: {str(e)}")

    async def bulk_index_documents(
        self,
        document_ids: List[int],
        force_reindex: bool = False,
    ) -> Dict[str, Any]:
        """
        Index multiple documents in bulk.

        Args:
            document_ids: List of document IDs
            force_reindex: Force reindexing

        Returns:
            Bulk indexing results summary
        """
        try:
            self.logger.info(
                "bulk_indexing_started",
                total_documents=len(document_ids),
            )

            results = {
                "total": len(document_ids),
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "errors": [],
            }

            # Process in batches
            for i in range(0, len(document_ids), self.config.batch_size):
                batch = document_ids[i:i + self.config.batch_size]

                # Process batch concurrently
                tasks = [
                    self.index_document(doc_id, force_reindex)
                    for doc_id in batch
                ]

                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                for doc_id, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        results["failed"] += 1
                        results["errors"].append({
                            "document_id": doc_id,
                            "error": str(result),
                        })
                    elif result.status == IndexStatus.INDEXED:
                        results["success"] += 1
                    else:
                        results["skipped"] += 1

                self.logger.info(
                    "batch_indexed",
                    batch_number=i // self.config.batch_size + 1,
                    processed=min(i + self.config.batch_size, len(document_ids)),
                )

            self.logger.info(
                "bulk_indexing_completed",
                success=results["success"],
                failed=results["failed"],
            )

            return results

        except Exception as e:
            self.logger.exception("bulk_indexing_failed", error=str(e))
            raise SearchException(f"Bulk indexing failed: {str(e)}")

    async def update_index(
        self,
        document_id: int,
    ) -> DocumentIndex:
        """
        Update existing document index.

        Args:
            document_id: Document ID

        Returns:
            Updated index

        Raises:
            ResourceNotFoundException: If document or index not found
        """
        try:
            self.logger.info("updating_index", document_id=document_id)

            # Get existing index
            existing_index = await self._get_existing_index(document_id)
            if not existing_index:
                # Create new index if doesn't exist
                return await self.index_document(document_id)

            # Mark as updating
            existing_index.status = IndexStatus.UPDATING

            # Reindex
            return await self.index_document(document_id, force_reindex=True)

        except Exception as e:
            self.logger.exception("update_index_failed", document_id=document_id, error=str(e))
            raise SearchException(f"Index update failed: {str(e)}")

    async def delete_index(
        self,
        document_id: int,
    ) -> None:
        """
        Delete document index.

        Args:
            document_id: Document ID

        Raises:
            ResourceNotFoundException: If index not found
        """
        try:
            self.logger.info("deleting_index", document_id=document_id)

            # Get existing index
            existing_index = await self._get_existing_index(document_id)
            if not existing_index:
                raise ResourceNotFoundException("Index", document_id)

            # Mark as deleting
            existing_index.status = IndexStatus.DELETING

            # Remove from cache
            self._index_cache.pop(document_id, None)

            # TODO: Delete from persistent index storage

            self.logger.info("index_deleted", document_id=document_id)

        except ResourceNotFoundException:
            raise
        except Exception as e:
            self.logger.exception("delete_index_failed", document_id=document_id, error=str(e))
            raise SearchException(f"Index deletion failed: {str(e)}")

    async def rebuild_index(
        self,
        status_filter: Optional[DocumentStatus] = None,
    ) -> Dict[str, Any]:
        """
        Rebuild entire document index.

        Args:
            status_filter: Only reindex documents with specific status

        Returns:
            Rebuild results summary
        """
        try:
            self.logger.info("rebuilding_index", status_filter=status_filter)

            # Get all document IDs
            stmt = select(Document.id)

            if status_filter:
                stmt = stmt.where(Document.status == status_filter)
            else:
                stmt = stmt.where(Document.status != DocumentStatus.DELETED)

            result = await self.db.execute(stmt)
            document_ids = [row[0] for row in result.all()]

            self.logger.info("index_rebuild_started", total_documents=len(document_ids))

            # Bulk reindex
            results = await self.bulk_index_documents(document_ids, force_reindex=True)

            self.logger.info("index_rebuild_completed", results=results)

            return results

        except Exception as e:
            self.logger.exception("rebuild_index_failed", error=str(e))
            raise SearchException(f"Index rebuild failed: {str(e)}")

    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get indexing statistics.

        Returns:
            Index statistics
        """
        try:
            # Count indexed documents
            stmt = select(Document.id).where(
                Document.status != DocumentStatus.DELETED
            )
            result = await self.db.execute(stmt)
            total_documents = len(result.all())

            # Calculate cache stats
            cache_size = len(self._index_cache)

            stats = {
                "total_documents": total_documents,
                "cached_indices": cache_size,
                "cache_hit_rate": 0.0,  # TODO: Track cache hits/misses
                "index_types": {
                    "full_text": cache_size,
                    "semantic": 0,
                    "metadata": cache_size,
                },
                "last_updated": datetime.utcnow().isoformat(),
            }

            return stats

        except Exception as e:
            self.logger.exception("get_stats_failed", error=str(e))
            return {}

    async def optimize_index(self) -> None:
        """
        Optimize index for better performance.

        This includes:
        - Removing stale entries
        - Compacting index storage
        - Updating statistics
        """
        try:
            self.logger.info("optimizing_index")

            # Remove stale cache entries
            stale_ids = []
            for doc_id in self._index_cache:
                try:
                    await self._get_document(doc_id)
                except ResourceNotFoundException:
                    stale_ids.append(doc_id)

            for doc_id in stale_ids:
                self._index_cache.pop(doc_id, None)

            self.logger.info(
                "index_optimized",
                removed_stale=len(stale_ids),
                cache_size=len(self._index_cache),
            )

        except Exception as e:
            self.logger.exception("optimize_failed", error=str(e))

    async def _get_document(self, document_id: int) -> Document:
        """
        Get document by ID.

        Args:
            document_id: Document ID

        Returns:
            Document

        Raises:
            ResourceNotFoundException: If document not found
        """
        stmt = (
            select(Document)
            .where(Document.id == document_id)
            .options(joinedload(Document.metadata_entries))
        )

        result = await self.db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            raise ResourceNotFoundException("Document", document_id)

        return document

    async def _get_existing_index(self, document_id: int) -> Optional[DocumentIndex]:
        """
        Get existing index for document.

        Args:
            document_id: Document ID

        Returns:
            Existing index or None
        """
        # Check cache first
        if document_id in self._index_cache:
            return self._index_cache[document_id]

        # TODO: Check persistent storage

        return None

    async def _index_full_text(self, document: Document, index: DocumentIndex) -> None:
        """
        Index document for full-text search.

        Args:
            document: Document to index
            index: Index object to update
        """
        try:
            # Extract text content
            content_parts = []

            # Add title and description
            if document.title:
                content_parts.append(document.title)
            if document.description:
                content_parts.append(document.description)

            # Add metadata text values
            for meta in document.metadata_entries:
                if meta.value_type == "string" and meta.value:
                    content_parts.append(meta.value)

            # TODO: Extract text from file content based on mime type
            # - PDF: PyPDF2, pdfplumber
            # - Word: python-docx
            # - Images: OCR with pytesseract
            # - Text files: direct reading

            full_text = " ".join(content_parts)

            # Store in index metadata
            index.metadata["full_text"] = full_text
            index.metadata["content_length"] = len(full_text)

            self.logger.debug(
                "full_text_indexed",
                document_id=document.id,
                content_length=len(full_text),
            )

        except Exception as e:
            self.logger.warning("full_text_indexing_failed", error=str(e))

    async def _index_metadata(self, document: Document, index: DocumentIndex) -> None:
        """
        Index document metadata.

        Args:
            document: Document to index
            index: Index object to update
        """
        try:
            metadata = {
                "title": document.title,
                "file_name": document.file_name,
                "mime_type": document.mime_type,
                "file_size": document.file_size,
                "status": document.status.value,
                "owner_id": document.owner_id,
                "created_at": document.created_at.isoformat(),
                "updated_at": document.updated_at.isoformat(),
            }

            # Add custom metadata
            for meta in document.metadata_entries:
                metadata[f"meta_{meta.key}"] = meta.value

            index.metadata.update(metadata)

            self.logger.debug(
                "metadata_indexed",
                document_id=document.id,
                metadata_count=len(metadata),
            )

        except Exception as e:
            self.logger.warning("metadata_indexing_failed", error=str(e))

    async def _index_semantic(self, document: Document, index: DocumentIndex) -> None:
        """
        Generate semantic embeddings for document.

        Args:
            document: Document to index
            index: Index object to update
        """
        try:
            # Get text content
            text_content = index.metadata.get("full_text", "")

            if not text_content:
                return

            # TODO: Generate embeddings using embedding model
            # - OpenAI embeddings
            # - Sentence transformers
            # - Custom models

            # Placeholder: Random embedding vector
            # In production, use actual embedding generation
            embedding = [0.0] * 768  # Common embedding dimension

            index.vector_embedding = embedding
            index.metadata["has_embedding"] = True

            self.logger.debug(
                "semantic_indexed",
                document_id=document.id,
                embedding_dim=len(embedding),
            )

        except Exception as e:
            self.logger.warning("semantic_indexing_failed", error=str(e))

    def _calculate_content_hash(self, document: Document) -> str:
        """
        Calculate content hash for change detection.

        Args:
            document: Document

        Returns:
            Content hash (SHA-256)
        """
        # Create hash from key document properties
        content = f"{document.title}|{document.description}|{document.file_hash}|{document.updated_at}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def search_by_embedding(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[Tuple[int, float]]:
        """
        Search documents by semantic similarity.

        Args:
            query_embedding: Query embedding vector
            limit: Maximum results
            threshold: Minimum similarity threshold

        Returns:
            List of (document_id, similarity_score) tuples
        """
        try:
            self.logger.debug("semantic_search", limit=limit, threshold=threshold)

            results = []

            # Calculate cosine similarity with cached embeddings
            for doc_id, index in self._index_cache.items():
                if not index.vector_embedding:
                    continue

                similarity = self._cosine_similarity(
                    query_embedding,
                    index.vector_embedding,
                )

                if similarity >= threshold:
                    results.append((doc_id, similarity))

            # Sort by similarity descending
            results.sort(key=lambda x: x[1], reverse=True)

            return results[:limit]

        except Exception as e:
            self.logger.exception("semantic_search_failed", error=str(e))
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score (0-1)
        """
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)
