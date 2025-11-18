#!/usr/bin/env python3
"""Reindex all documents in Nexus Platform."""

import asyncio
import logging
import sys

from search.indexer import DocumentIndexer
from search.client import es_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_sample_data(doc_type):
    """
    Get documents from your data source.

    Replace this with your actual data source logic.
    This is a placeholder that returns empty list.
    """
    # TODO: Implement data source integration
    # Examples:
    # - Query database
    # - Read from files
    # - Fetch from API
    # - etc.

    logger.warning(f"No data source configured for {doc_type}")
    return []


async def main():
    """Reindex all documents."""
    try:
        logger.info("Starting full reindex...")

        # Confirmation
        print("\n⚠️  WARNING: This will reindex ALL documents.")
        response = input("Are you sure you want to continue? (yes/no): ")

        if response.lower() != "yes":
            logger.info("Reindex cancelled")
            return 0

        # Initialize indexer
        indexer = DocumentIndexer()

        # Perform reindex
        result = await indexer.reindex_all(
            data_source_callback=get_sample_data,
            batch_size=500,
        )

        logger.info(f"\n✓ Reindex complete!")
        logger.info(f"  Indexed: {result['success']:,} documents")
        logger.info(f"  Failed: {result['failed']:,} documents")

        return 0

    except Exception as e:
        logger.error(f"Reindex failed: {e}", exc_info=True)
        return 1

    finally:
        await es_client.disconnect()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
