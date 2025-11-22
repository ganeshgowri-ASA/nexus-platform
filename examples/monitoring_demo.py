"""Monitoring and analytics demo for Nexus Platform."""

import asyncio
import logging

from search.monitoring import analytics, health_monitor
from search.client import es_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def health_check_demo():
    """Demonstrate health checking."""
    logger.info("\n=== Health Check Demo ===\n")

    health = await health_monitor.check_health()

    logger.info(f"Overall Status: {health['status']}")
    logger.info(f"Timestamp: {health['timestamp']}")

    logger.info("\nHealth Checks:")
    for check_name, check_data in health['checks'].items():
        status = check_data.get('status', 'unknown')
        logger.info(f"  {check_name}: {status}")


async def index_stats_demo():
    """Demonstrate index statistics."""
    logger.info("\n=== Index Statistics Demo ===\n")

    stats = await analytics.get_index_stats()

    logger.info(f"Cluster: {stats['cluster_name']} ({stats['cluster_health']})")
    logger.info("\nIndex Statistics:")

    for index_name, index_stats in stats['indices'].items():
        logger.info(f"\n{index_name}:")
        logger.info(f"  Documents: {index_stats['document_count']:,}")
        logger.info(f"  Size: {index_stats['size_mb']} MB")
        logger.info(f"  Total Searches: {index_stats['search_total']:,}")
        logger.info(f"  Search Time: {index_stats['search_time_ms']:,} ms")


async def search_performance_demo():
    """Demonstrate search performance metrics."""
    logger.info("\n=== Search Performance Demo ===\n")

    perf = await analytics.get_search_performance()

    logger.info(f"Total Queries: {perf['total_queries']:,}")
    logger.info(f"Total Time: {perf['total_time_ms']:,} ms")
    logger.info(f"Average Query Time: {perf['average_query_time_ms']:.2f} ms")
    logger.info(f"Queries per Second: {perf['queries_per_second']:.2f}")


async def document_distribution_demo():
    """Demonstrate document distribution analysis."""
    logger.info("\n=== Document Distribution Demo ===\n")

    distribution = await analytics.get_document_distribution()

    logger.info("Document Distribution by Type:")
    total = sum(distribution.values())

    for doc_type, count in sorted(
        distribution.items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        percentage = (count / total * 100) if total > 0 else 0
        logger.info(f"  {doc_type:15s}: {count:6,} ({percentage:5.1f}%)")

    logger.info(f"\n  {'Total':15s}: {total:6,}")


async def index_health_demo():
    """Demonstrate index health checking."""
    logger.info("\n=== Index Health Demo ===\n")

    from search.config import settings
    from search.models import DocumentType

    for doc_type in DocumentType:
        index_name = settings.get_index_name(doc_type.value)
        health = await health_monitor.check_index_health(index_name)

        logger.info(f"\n{index_name}:")
        logger.info(f"  Status: {health.get('status', 'unknown')}")

        if health.get('status') not in ['not_found', 'error']:
            logger.info(f"  Documents: {health.get('documents', 0):,}")
            logger.info(f"  Size: {health.get('size_bytes', 0):,} bytes")
            logger.info(f"  Shards: {health.get('shards', 0)}")


async def main():
    """Run all monitoring demos."""
    try:
        await health_check_demo()
        await index_stats_demo()
        await search_performance_demo()
        await document_distribution_demo()
        await index_health_demo()

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        await es_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
