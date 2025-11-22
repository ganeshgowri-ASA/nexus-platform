"""Monitoring and analytics for search system."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .client import es_client
from .config import settings
from .models import DocumentType

logger = logging.getLogger(__name__)


class SearchAnalytics:
    """Analytics and monitoring for search operations."""

    async def get_index_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all indices."""
        stats = {}

        try:
            async with es_client.get_client() as client:
                # Get index stats
                indices_stats = await client.indices.stats(
                    index=f"{settings.elasticsearch_index_prefix}_*"
                )

                # Get cluster health
                cluster_health = await client.cluster.health()

                for index_name, index_data in indices_stats["indices"].items():
                    stats[index_name] = {
                        "document_count": index_data["primaries"]["docs"]["count"],
                        "deleted_count": index_data["primaries"]["docs"]["deleted"],
                        "size_bytes": index_data["primaries"]["store"]["size_in_bytes"],
                        "size_mb": round(
                            index_data["primaries"]["store"]["size_in_bytes"] / 1024 / 1024,
                            2,
                        ),
                        "indexing_total": index_data["primaries"]["indexing"]["index_total"],
                        "search_total": index_data["primaries"]["search"]["query_total"],
                        "search_time_ms": index_data["primaries"]["search"]["query_time_in_millis"],
                    }

                return {
                    "cluster_health": cluster_health["status"],
                    "cluster_name": cluster_health["cluster_name"],
                    "indices": stats,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            raise

    async def get_search_performance(
        self,
        index_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get search performance metrics."""
        try:
            async with es_client.get_client() as client:
                target_index = index_name or f"{settings.elasticsearch_index_prefix}_*"

                stats = await client.indices.stats(index=target_index)

                total_queries = 0
                total_time_ms = 0
                total_fetch_time_ms = 0

                for idx, data in stats["indices"].items():
                    search_stats = data["primaries"]["search"]
                    total_queries += search_stats["query_total"]
                    total_time_ms += search_stats["query_time_in_millis"]
                    total_fetch_time_ms += search_stats["fetch_time_in_millis"]

                avg_query_time = (
                    round(total_time_ms / total_queries, 2) if total_queries > 0 else 0
                )

                return {
                    "total_queries": total_queries,
                    "total_time_ms": total_time_ms,
                    "total_fetch_time_ms": total_fetch_time_ms,
                    "average_query_time_ms": avg_query_time,
                    "queries_per_second": round(
                        total_queries / (total_time_ms / 1000) if total_time_ms > 0 else 0,
                        2,
                    ),
                }

        except Exception as e:
            logger.error(f"Failed to get search performance: {e}")
            raise

    async def get_top_searches(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get most common search queries (requires query logging)."""
        # This would require implementing search query logging
        # For now, return placeholder
        logger.warning("Top searches tracking requires query logging implementation")
        return []

    async def get_document_distribution(self) -> Dict[str, int]:
        """Get distribution of documents by type."""
        distribution = {}

        for doc_type in DocumentType:
            index_name = settings.get_index_name(doc_type.value)

            try:
                async with es_client.get_client() as client:
                    count = await client.count(index=index_name)
                    distribution[doc_type.value] = count["count"]
            except Exception as e:
                logger.error(f"Failed to count {doc_type}: {e}")
                distribution[doc_type.value] = 0

        return distribution

    async def get_indexing_rate(
        self,
        time_window_minutes: int = 60,
    ) -> Dict[str, float]:
        """Calculate indexing rate over time window."""
        try:
            async with es_client.get_client() as client:
                stats = await client.indices.stats(
                    index=f"{settings.elasticsearch_index_prefix}_*"
                )

                rates = {}
                for index_name, data in stats["indices"].items():
                    indexing_total = data["primaries"]["indexing"]["index_total"]
                    # Simplified rate calculation
                    rate_per_minute = indexing_total / time_window_minutes
                    rates[index_name] = round(rate_per_minute, 2)

                return rates

        except Exception as e:
            logger.error(f"Failed to get indexing rate: {e}")
            raise

    async def optimize_indices(self) -> Dict[str, bool]:
        """Optimize indices for better performance."""
        results = {}

        try:
            async with es_client.get_client() as client:
                # Force merge to optimize segment count
                for doc_type in DocumentType:
                    index_name = settings.get_index_name(doc_type.value)

                    try:
                        await client.indices.forcemerge(
                            index=index_name,
                            max_num_segments=1,
                        )
                        results[index_name] = True
                        logger.info(f"Optimized index: {index_name}")
                    except Exception as e:
                        logger.error(f"Failed to optimize {index_name}: {e}")
                        results[index_name] = False

            return results

        except Exception as e:
            logger.error(f"Index optimization failed: {e}")
            raise

    async def clear_cache(self, index_name: Optional[str] = None) -> bool:
        """Clear search caches."""
        try:
            async with es_client.get_client() as client:
                target = index_name or f"{settings.elasticsearch_index_prefix}_*"
                await client.indices.clear_cache(index=target)
                logger.info(f"Cleared cache for {target}")
                return True

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False


class HealthMonitor:
    """Health monitoring for the search system."""

    async def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health_data = {
            "status": "unknown",
            "checks": {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Check Elasticsearch connection
        try:
            is_connected = await es_client.ping()
            health_data["checks"]["elasticsearch_connection"] = {
                "status": "healthy" if is_connected else "unhealthy",
                "message": "Connected" if is_connected else "Not connected",
            }
        except Exception as e:
            health_data["checks"]["elasticsearch_connection"] = {
                "status": "unhealthy",
                "message": str(e),
            }

        # Check cluster health
        try:
            cluster_health = await es_client.health_check()
            health_data["checks"]["cluster_health"] = {
                "status": cluster_health.status,
                "cluster_name": cluster_health.cluster_name,
            }
        except Exception as e:
            health_data["checks"]["cluster_health"] = {
                "status": "unhealthy",
                "message": str(e),
            }

        # Check indices
        try:
            analytics = SearchAnalytics()
            stats = await analytics.get_index_stats()
            health_data["checks"]["indices"] = {
                "status": "healthy",
                "count": len(stats.get("indices", {})),
            }
        except Exception as e:
            health_data["checks"]["indices"] = {
                "status": "unhealthy",
                "message": str(e),
            }

        # Determine overall status
        statuses = [
            check.get("status", "unknown")
            for check in health_data["checks"].values()
        ]

        if all(s == "healthy" or s == "green" for s in statuses):
            health_data["status"] = "healthy"
        elif any(s == "unhealthy" or s == "red" for s in statuses):
            health_data["status"] = "unhealthy"
        else:
            health_data["status"] = "degraded"

        return health_data

    async def check_index_health(
        self,
        index_name: str,
    ) -> Dict[str, Any]:
        """Check health of a specific index."""
        try:
            async with es_client.get_client() as client:
                # Check if index exists
                exists = await client.indices.exists(index=index_name)
                if not exists:
                    return {
                        "status": "not_found",
                        "message": f"Index {index_name} does not exist",
                    }

                # Get index health
                health = await client.cluster.health(index=index_name)

                # Get index stats
                stats = await client.indices.stats(index=index_name)
                index_stats = stats["indices"][index_name]["primaries"]

                return {
                    "status": health["status"],
                    "documents": index_stats["docs"]["count"],
                    "size_bytes": index_stats["store"]["size_in_bytes"],
                    "shards": health["active_shards"],
                    "replicas": health["number_of_replicas"],
                }

        except Exception as e:
            logger.error(f"Failed to check index health: {e}")
            return {
                "status": "error",
                "message": str(e),
            }


# Global instances
analytics = SearchAnalytics()
health_monitor = HealthMonitor()
