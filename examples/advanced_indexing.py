"""Advanced indexing examples for Nexus Platform."""

import asyncio
import logging
from datetime import datetime

from search.content_indexers import (
    DocumentContentIndexer,
    EmailContentIndexer,
    FileContentIndexer,
    ChatContentIndexer,
)
from search.indexer import AsyncIndexer
from search.client import es_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def bulk_email_indexing():
    """Demonstrate bulk email indexing."""
    logger.info("\n=== Bulk Email Indexing ===\n")

    indexer = EmailContentIndexer()

    # Prepare bulk emails
    emails = [
        {
            "id": f"bulk-email-{i}",
            "subject": f"Email Subject {i}",
            "content": f"This is the content of email number {i}",
            "sender": f"sender{i}@company.com",
            "recipients": ["team@company.com"],
            "owner_id": "user-1",
            "owner_name": "John Doe",
            "tags": ["bulk", "test"],
        }
        for i in range(100)
    ]

    result = await indexer.index_emails_bulk(emails)
    logger.info(f"Indexed {result['success']} emails, {result['failed']} failed")


async def async_indexing_demo():
    """Demonstrate async indexing with queue."""
    logger.info("\n=== Async Indexing Demo ===\n")

    # Create async indexer
    async_indexer = AsyncIndexer(queue_size=1000)

    # Start indexer
    await async_indexer.start()
    logger.info("Async indexer started")

    # Queue documents
    from search.models import EmailDocument

    for i in range(50):
        doc = EmailDocument(
            id=f"async-email-{i}",
            title=f"Async Email {i}",
            subject=f"Async Email {i}",
            content=f"Content for async email {i}",
            sender="async@company.com",
            recipients=["team@company.com"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            owner_id="user-1",
            owner_name="John Doe",
        )
        await async_indexer.queue_document(doc)

    queue_size = async_indexer.get_queue_size()
    logger.info(f"Queued documents: {queue_size}")

    # Wait for indexing to complete
    await async_indexer.stop(wait=True)
    logger.info("Async indexing completed")


async def file_indexing_demo():
    """Demonstrate file indexing."""
    logger.info("\n=== File Indexing Demo ===\n")

    indexer = FileContentIndexer()

    # Index sample files
    files = [
        {
            "file_id": f"file-{i}",
            "file_name": f"document_{i}.txt",
            "file_path": f"/files/document_{i}.txt",
            "content": f"This is the content of file {i}",
            "owner_id": "user-1",
            "owner_name": "John Doe",
            "file_type": "text",
            "file_size": 1024,
            "mime_type": "text/plain",
            "extension": "txt",
            "tags": ["file", "sample"],
        }
        for i in range(20)
    ]

    indexed = 0
    for file_data in files:
        success = await indexer.index_file(**file_data)
        if success:
            indexed += 1

    logger.info(f"Indexed {indexed} files")


async def chat_indexing_demo():
    """Demonstrate chat message indexing."""
    logger.info("\n=== Chat Indexing Demo ===\n")

    indexer = ChatContentIndexer()

    # Index chat messages
    messages = [
        {
            "message_id": f"msg-{i}",
            "channel_id": "channel-1",
            "channel_name": "general",
            "sender": f"User {i % 5}",
            "message": f"Chat message content {i}",
            "owner_id": "user-1",
            "owner_name": "John Doe",
            "participants": [f"user-{j}" for j in range(5)],
        }
        for i in range(30)
    ]

    # Bulk index
    result = await indexer.index_messages_bulk(messages)
    logger.info(f"Indexed {result['success']} chat messages")


async def document_update_demo():
    """Demonstrate document updates."""
    logger.info("\n=== Document Update Demo ===\n")

    from search.indexer import DocumentIndexer
    from search.models import DocumentType, EmailDocument

    indexer = DocumentIndexer()

    # Index original document
    email = EmailDocument(
        id="update-demo",
        title="Original Title",
        subject="Original Title",
        content="Original content",
        sender="test@company.com",
        recipients=["team@company.com"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        owner_id="user-1",
        owner_name="John Doe",
    )

    await indexer.index_document(email, refresh=True)
    logger.info("Indexed original document")

    # Update document
    success = await indexer.update_document(
        doc_id="update-demo",
        doc_type=DocumentType.EMAIL,
        partial_doc={
            "title": "Updated Title",
            "subject": "Updated Title",
            "tags": ["updated"],
        },
        refresh=True,
    )

    if success:
        logger.info("Document updated successfully")


async def main():
    """Run all indexing demos."""
    try:
        await bulk_email_indexing()
        await async_indexing_demo()
        await file_indexing_demo()
        await chat_indexing_demo()
        await document_update_demo()

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await es_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
