#!/usr/bin/env python3
"""Initialize Elasticsearch indices for Nexus Platform."""

import asyncio
import logging
import sys

from search.indexer import DocumentIndexer
from search.client import es_client
from search.monitoring import health_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Initialize search system."""
    try:
        logger.info("Starting Nexus Search initialization...")

        # Check Elasticsearch connection
        logger.info("Checking Elasticsearch connection...")
        is_connected = await es_client.ping()

        if not is_connected:
            logger.error("Cannot connect to Elasticsearch. Please check your configuration.")
            return 1

        logger.info("✓ Connected to Elasticsearch")

        # Check cluster health
        health = await health_monitor.check_health()
        logger.info(f"✓ Cluster health: {health['status']}")

        # Initialize indices
        logger.info("Creating indices...")
        indexer = DocumentIndexer()
        await indexer.initialize_indices()

        logger.info("✓ All indices created successfully")

        # Verify indices
        from search.monitoring import analytics
        stats = await analytics.get_index_stats()

        logger.info(f"\nCreated {len(stats['indices'])} indices:")
        for index_name in stats['indices'].keys():
            logger.info(f"  - {index_name}")

        logger.info("\n✓ Nexus Search initialization complete!")
        logger.info("\nYou can now start indexing documents and searching.")

        return 0

    except Exception as e:
        logger.error(f"Initialization failed: {e}", exc_info=True)
        return 1

    finally:
        await es_client.disconnect()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
