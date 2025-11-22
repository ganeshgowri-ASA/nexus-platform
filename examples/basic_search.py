"""Basic search example for Nexus Platform."""

import asyncio
import logging
from datetime import datetime

from search import SearchEngine, SearchRequest
from search.indexer import DocumentIndexer
from search.models import EmailDocument, DocumentType
from search.client import es_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_sample_data():
    """Index sample documents for demonstration."""
    indexer = DocumentIndexer()

    # Initialize indices
    await indexer.initialize_indices()

    # Sample emails
    sample_emails = [
        EmailDocument(
            id="email-1",
            title="Q4 Planning Meeting",
            subject="Q4 Planning Meeting",
            content="Let's discuss our Q4 goals and strategies for the upcoming quarter.",
            sender="manager@company.com",
            recipients=["team@company.com"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            owner_id="user-1",
            owner_name="John Doe",
            tags=["meeting", "planning"],
        ),
        EmailDocument(
            id="email-2",
            title="Project Update",
            subject="Project Update",
            content="The new feature development is on track. Expected completion next week.",
            sender="developer@company.com",
            recipients=["manager@company.com"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            owner_id="user-1",
            owner_name="John Doe",
            tags=["project", "update"],
            importance="high",
        ),
        EmailDocument(
            id="email-3",
            title="Team Lunch",
            subject="Team Lunch",
            content="Don't forget about team lunch this Friday at 12 PM!",
            sender="hr@company.com",
            recipients=["all@company.com"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            owner_id="user-1",
            owner_name="John Doe",
            tags=["social"],
        ),
    ]

    # Index emails
    result = await indexer.index_documents_bulk(sample_emails, refresh=True)
    logger.info(f"Indexed {result['success']} sample emails")


async def basic_search_demo():
    """Demonstrate basic search functionality."""
    search_engine = SearchEngine()

    logger.info("\n=== Basic Search Demo ===\n")

    # Search for "project"
    logger.info("Searching for: 'project'")
    request = SearchRequest(query="project")
    response = await search_engine.search(request)

    logger.info(f"Found {response.total} results in {response.took_ms}ms")
    for i, hit in enumerate(response.hits, 1):
        logger.info(f"{i}. {hit.title} (score: {hit.score:.2f})")


async def filtered_search_demo():
    """Demonstrate search with filters."""
    search_engine = SearchEngine()

    logger.info("\n=== Filtered Search Demo ===\n")

    from search.models import SearchFilters

    filters = SearchFilters(
        tags=["meeting"],
        document_types=[DocumentType.EMAIL],
    )

    request = SearchRequest(
        query="planning",
        filters=filters,
    )

    response = await search_engine.search(request)

    logger.info(f"Found {response.total} results with filters")
    for hit in response.hits:
        logger.info(f"- {hit.title}")


async def autocomplete_demo():
    """Demonstrate autocomplete functionality."""
    search_engine = SearchEngine()

    logger.info("\n=== Autocomplete Demo ===\n")

    request = SearchRequest(
        query="proj",
        autocomplete=True,
    )

    response = await search_engine.search(request)

    logger.info("Autocomplete suggestions:")
    for suggestion in response.suggestions:
        logger.info(f"  - {suggestion}")


async def highlighted_search_demo():
    """Demonstrate search with highlighting."""
    search_engine = SearchEngine()

    logger.info("\n=== Highlighted Search Demo ===\n")

    request = SearchRequest(
        query="meeting planning",
        highlight=True,
        highlight_fields=["title", "content"],
    )

    response = await search_engine.search(request)

    logger.info(f"Search results with highlights:")
    for hit in response.hits:
        logger.info(f"\n{hit.title}")
        if hit.highlights:
            for highlight in hit.highlights:
                logger.info(f"  {highlight.field}:")
                for fragment in highlight.fragments:
                    logger.info(f"    {fragment}")


async def main():
    """Run all demos."""
    try:
        # Setup sample data
        await setup_sample_data()

        # Run demos
        await basic_search_demo()
        await filtered_search_demo()
        await autocomplete_demo()
        await highlighted_search_demo()

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Cleanup
        await es_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
