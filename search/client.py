"""Elasticsearch client with connection management and health checks."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from elasticsearch import AsyncElasticsearch, ConnectionError, NotFoundError
from elasticsearch.helpers import async_bulk

from .config import settings
from .models import HealthStatus, IndexStats

logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Production-ready Elasticsearch client with connection pooling and error handling."""

    def __init__(self):
        """Initialize Elasticsearch client."""
        self._client: Optional[AsyncElasticsearch] = None
        self._connected = False

    async def connect(self) -> None:
        """Establish connection to Elasticsearch cluster."""
        if self._connected and self._client:
            return

        try:
            # Build connection parameters
            connect_params: Dict[str, Any] = {
                "hosts": settings.hosts,
                "request_timeout": settings.elasticsearch_request_timeout,
                "max_retries": settings.elasticsearch_max_retries,
                "retry_on_timeout": True,
            }

            # Add authentication
            if settings.elasticsearch_cloud_id:
                connect_params["cloud_id"] = settings.elasticsearch_cloud_id

            if settings.elasticsearch_api_key:
                connect_params["api_key"] = settings.elasticsearch_api_key
            elif settings.elasticsearch_username and settings.elasticsearch_password:
                connect_params["basic_auth"] = (
                    settings.elasticsearch_username,
                    settings.elasticsearch_password,
                )

            # SSL configuration
            if settings.elasticsearch_use_ssl:
                connect_params["verify_certs"] = settings.elasticsearch_verify_certs
                if settings.elasticsearch_ca_certs:
                    connect_params["ca_certs"] = settings.elasticsearch_ca_certs

            self._client = AsyncElasticsearch(**connect_params)

            # Verify connection
            info = await self._client.info()
            self._connected = True
            logger.info(
                f"Connected to Elasticsearch cluster: {info['cluster_name']} "
                f"(version {info['version']['number']})"
            )

        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            raise ConnectionError(f"Cannot connect to Elasticsearch: {e}")

    async def disconnect(self) -> None:
        """Close Elasticsearch connection."""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Disconnected from Elasticsearch")

    @asynccontextmanager
    async def get_client(self):
        """Context manager for Elasticsearch client."""
        await self.connect()
        try:
            yield self._client
        finally:
            pass  # Keep connection open for reuse

    async def ping(self) -> bool:
        """Check if Elasticsearch is reachable."""
        try:
            await self.connect()
            return await self._client.ping()
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return False

    async def health_check(self) -> HealthStatus:
        """Get comprehensive health status."""
        await self.connect()

        try:
            # Get cluster health
            cluster_health = await self._client.cluster.health()
            cluster_name = cluster_health["cluster_name"]

            # Get index statistics
            indices_stats = {}
            stats = await self._client.indices.stats()

            for index_name, index_data in stats["indices"].items():
                if index_name.startswith(settings.elasticsearch_index_prefix):
                    indices_stats[index_name] = IndexStats(
                        index_name=index_name,
                        document_count=index_data["primaries"]["docs"]["count"],
                        size_in_bytes=index_data["primaries"]["store"]["size_in_bytes"],
                    )

            return HealthStatus(
                status=cluster_health["status"],
                cluster_name=cluster_name,
                indices=indices_stats,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise

    async def create_index(
        self,
        index_name: str,
        mappings: Dict[str, Any],
        settings_override: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Create an index with mappings and settings."""
        await self.connect()

        try:
            # Check if index already exists
            exists = await self._client.indices.exists(index=index_name)
            if exists:
                logger.info(f"Index {index_name} already exists")
                return False

            # Build index settings
            index_settings = {
                "number_of_shards": settings.elasticsearch_shards,
                "number_of_replicas": settings.elasticsearch_replicas,
                "analysis": {
                    "analyzer": {
                        "autocomplete": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "autocomplete_filter"],
                        },
                        "autocomplete_search": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase"],
                        },
                    },
                    "filter": {
                        "autocomplete_filter": {
                            "type": "edge_ngram",
                            "min_gram": 2,
                            "max_gram": 20,
                        }
                    },
                },
            }

            if settings_override:
                index_settings.update(settings_override)

            # Create index
            await self._client.indices.create(
                index=index_name,
                mappings=mappings,
                settings=index_settings,
            )

            logger.info(f"Created index: {index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            raise

    async def delete_index(self, index_name: str) -> bool:
        """Delete an index."""
        await self.connect()

        try:
            exists = await self._client.indices.exists(index=index_name)
            if not exists:
                logger.warning(f"Index {index_name} does not exist")
                return False

            await self._client.indices.delete(index=index_name)
            logger.info(f"Deleted index: {index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {e}")
            raise

    async def refresh_index(self, index_name: str) -> None:
        """Refresh an index to make recent changes searchable."""
        await self.connect()
        await self._client.indices.refresh(index=index_name)

    async def bulk_index(
        self,
        index_name: str,
        documents: List[Dict[str, Any]],
        refresh: bool = False,
    ) -> Dict[str, int]:
        """Bulk index documents."""
        await self.connect()

        actions = [
            {
                "_index": index_name,
                "_id": doc.get("id"),
                "_source": doc,
            }
            for doc in documents
        ]

        try:
            success, failed = await async_bulk(
                self._client,
                actions,
                chunk_size=settings.elasticsearch_bulk_size,
                raise_on_error=False,
            )

            if refresh:
                await self.refresh_index(index_name)

            logger.info(
                f"Bulk indexed {success} documents to {index_name}, {failed} failed"
            )

            return {"success": success, "failed": failed}

        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            raise

    async def index_document(
        self,
        index_name: str,
        doc_id: str,
        document: Dict[str, Any],
        refresh: bool = False,
    ) -> bool:
        """Index a single document."""
        await self.connect()

        try:
            await self._client.index(
                index=index_name,
                id=doc_id,
                document=document,
                refresh=refresh,
            )
            logger.debug(f"Indexed document {doc_id} to {index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            raise

    async def update_document(
        self,
        index_name: str,
        doc_id: str,
        partial_doc: Dict[str, Any],
        refresh: bool = False,
    ) -> bool:
        """Update a document partially."""
        await self.connect()

        try:
            await self._client.update(
                index=index_name,
                id=doc_id,
                doc=partial_doc,
                refresh=refresh,
            )
            logger.debug(f"Updated document {doc_id} in {index_name}")
            return True

        except NotFoundError:
            logger.warning(f"Document {doc_id} not found in {index_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            raise

    async def delete_document(
        self,
        index_name: str,
        doc_id: str,
        refresh: bool = False,
    ) -> bool:
        """Delete a document."""
        await self.connect()

        try:
            await self._client.delete(
                index=index_name,
                id=doc_id,
                refresh=refresh,
            )
            logger.debug(f"Deleted document {doc_id} from {index_name}")
            return True

        except NotFoundError:
            logger.warning(f"Document {doc_id} not found in {index_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise

    async def get_document(
        self,
        index_name: str,
        doc_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID."""
        await self.connect()

        try:
            result = await self._client.get(index=index_name, id=doc_id)
            return result["_source"]

        except NotFoundError:
            logger.debug(f"Document {doc_id} not found in {index_name}")
            return None
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            raise


# Global client instance
es_client = ElasticsearchClient()
