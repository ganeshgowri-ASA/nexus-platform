"""Document indexing with async support and queue management."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from queue import Queue
from threading import Thread

from .client import es_client
from .config import settings
from .models import (
    BaseDocument,
    DocumentDocument,
    EmailDocument,
    FileDocument,
    ChatDocument,
    DocumentType,
)
from .schemas import SchemaManager

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """Synchronous document indexer with schema management."""

    def __init__(self):
        """Initialize document indexer."""
        self.schema_manager = SchemaManager()

    async def initialize_indices(self) -> None:
        """Create all required indices with proper mappings."""
        logger.info("Initializing Elasticsearch indices...")

        for doc_type in DocumentType:
            index_name = settings.get_index_name(doc_type.value)
            mapping = self.schema_manager.get_mapping(doc_type)

            try:
                created = await es_client.create_index(
                    index_name=index_name,
                    mappings=mapping,
                )
                if created:
                    logger.info(f"Created index: {index_name}")
                else:
                    logger.info(f"Index already exists: {index_name}")
            except Exception as e:
                logger.error(f"Failed to create index {index_name}: {e}")
                raise

        logger.info("All indices initialized successfully")

    async def delete_indices(self, confirm: bool = False) -> None:
        """Delete all indices (use with caution!)."""
        if not confirm:
            raise ValueError("Must confirm index deletion")

        logger.warning("Deleting all Elasticsearch indices...")

        for doc_type in DocumentType:
            index_name = settings.get_index_name(doc_type.value)
            try:
                await es_client.delete_index(index_name)
                logger.info(f"Deleted index: {index_name}")
            except Exception as e:
                logger.error(f"Failed to delete index {index_name}: {e}")

    async def index_document(
        self,
        document: Union[BaseDocument, Dict[str, Any]],
        refresh: bool = False,
    ) -> bool:
        """Index a single document."""
        try:
            # Convert to dict if needed
            if isinstance(document, BaseDocument):
                doc_dict = document.model_dump(mode="json")
                doc_type = document.type
                doc_id = document.id
            else:
                doc_dict = document
                doc_type = DocumentType(document["type"])
                doc_id = document["id"]

            index_name = settings.get_index_name(doc_type.value)

            await es_client.index_document(
                index_name=index_name,
                doc_id=doc_id,
                document=doc_dict,
                refresh=refresh,
            )

            return True

        except Exception as e:
            logger.error(f"Failed to index document: {e}")
            raise

    async def index_documents_bulk(
        self,
        documents: List[Union[BaseDocument, Dict[str, Any]]],
        refresh: bool = False,
    ) -> Dict[str, int]:
        """Bulk index multiple documents."""
        try:
            # Group documents by type
            docs_by_type: Dict[DocumentType, List[Dict[str, Any]]] = {}

            for doc in documents:
                if isinstance(doc, BaseDocument):
                    doc_dict = doc.model_dump(mode="json")
                    doc_type = doc.type
                else:
                    doc_dict = doc
                    doc_type = DocumentType(doc["type"])

                if doc_type not in docs_by_type:
                    docs_by_type[doc_type] = []
                docs_by_type[doc_type].append(doc_dict)

            # Bulk index each type
            total_success = 0
            total_failed = 0

            for doc_type, doc_list in docs_by_type.items():
                index_name = settings.get_index_name(doc_type.value)
                result = await es_client.bulk_index(
                    index_name=index_name,
                    documents=doc_list,
                    refresh=refresh,
                )
                total_success += result["success"]
                total_failed += result["failed"]

            logger.info(
                f"Bulk indexed {total_success} documents, {total_failed} failed"
            )

            return {"success": total_success, "failed": total_failed}

        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            raise

    async def update_document(
        self,
        doc_id: str,
        doc_type: DocumentType,
        partial_doc: Dict[str, Any],
        refresh: bool = False,
    ) -> bool:
        """Update a document partially."""
        try:
            index_name = settings.get_index_name(doc_type.value)
            return await es_client.update_document(
                index_name=index_name,
                doc_id=doc_id,
                partial_doc=partial_doc,
                refresh=refresh,
            )
        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            raise

    async def delete_document(
        self,
        doc_id: str,
        doc_type: DocumentType,
        refresh: bool = False,
    ) -> bool:
        """Delete a document."""
        try:
            index_name = settings.get_index_name(doc_type.value)
            return await es_client.delete_document(
                index_name=index_name,
                doc_id=doc_id,
                refresh=refresh,
            )
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise

    async def reindex_all(
        self,
        data_source_callback,
        batch_size: int = 500,
    ) -> Dict[str, int]:
        """Reindex all documents from a data source."""
        logger.info("Starting full reindex...")

        total_indexed = 0
        total_failed = 0

        for doc_type in DocumentType:
            logger.info(f"Reindexing {doc_type.value}...")

            # Get documents from data source
            documents = await data_source_callback(doc_type)

            # Index in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                result = await self.index_documents_bulk(batch)
                total_indexed += result["success"]
                total_failed += result["failed"]

                logger.info(
                    f"Indexed batch {i // batch_size + 1} for {doc_type.value}"
                )

        logger.info(
            f"Reindex complete: {total_indexed} indexed, {total_failed} failed"
        )

        return {"success": total_indexed, "failed": total_failed}


class AsyncIndexer:
    """Async document indexer with queue support for high-throughput indexing."""

    def __init__(self, queue_size: Optional[int] = None):
        """Initialize async indexer with queue."""
        self.queue_size = queue_size or settings.elasticsearch_queue_size
        self.queue: Queue = Queue(maxsize=self.queue_size)
        self.indexer = DocumentIndexer()
        self.worker_task: Optional[asyncio.Task] = None
        self.running = False

    async def start(self) -> None:
        """Start the async indexing worker."""
        if self.running:
            logger.warning("Async indexer already running")
            return

        self.running = True
        self.worker_task = asyncio.create_task(self._process_queue())
        logger.info("Async indexer started")

    async def stop(self, wait: bool = True) -> None:
        """Stop the async indexing worker."""
        if not self.running:
            return

        self.running = False

        if wait and self.worker_task:
            # Wait for queue to drain
            while not self.queue.empty():
                await asyncio.sleep(0.1)

            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

        logger.info("Async indexer stopped")

    async def queue_document(
        self,
        document: Union[BaseDocument, Dict[str, Any]],
        priority: int = 0,
    ) -> bool:
        """Add a document to the indexing queue."""
        try:
            self.queue.put_nowait((priority, document))
            return True
        except Exception as e:
            logger.error(f"Failed to queue document: {e}")
            return False

    async def queue_documents(
        self,
        documents: List[Union[BaseDocument, Dict[str, Any]]],
    ) -> int:
        """Queue multiple documents for indexing."""
        queued = 0
        for doc in documents:
            if await self.queue_document(doc):
                queued += 1
        return queued

    async def _process_queue(self) -> None:
        """Process documents from the queue."""
        batch: List[Union[BaseDocument, Dict[str, Any]]] = []
        batch_size = settings.elasticsearch_bulk_size

        while self.running:
            try:
                # Collect batch
                while len(batch) < batch_size and not self.queue.empty():
                    try:
                        _, document = self.queue.get_nowait()
                        batch.append(document)
                    except Exception:
                        break

                # Index batch if we have documents
                if batch:
                    try:
                        await self.indexer.index_documents_bulk(batch)
                        logger.debug(f"Processed batch of {len(batch)} documents")
                        batch.clear()
                    except Exception as e:
                        logger.error(f"Batch indexing error: {e}")
                        batch.clear()

                # Small delay to avoid tight loop
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await asyncio.sleep(1)

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self.queue.qsize()

    def is_running(self) -> bool:
        """Check if indexer is running."""
        return self.running
