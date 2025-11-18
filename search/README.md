# Nexus Platform - Elasticsearch Search Module

Production-ready full-text search engine for the Nexus platform with advanced features including document indexing, search with filters, facets, autocomplete, relevance scoring, highlighting, and aggregations.

## Features

- **Full-text search** with relevance scoring
- **Async document indexing** with queue support
- **Advanced filtering** (document types, dates, owners, tags, custom fields)
- **Faceted search** with aggregations
- **Autocomplete** suggestions
- **Syntax highlighting** in search results
- **Multi-field search** with boosting
- **Bulk indexing** for high throughput
- **Production-ready** with health checks, monitoring, and error handling

## Supported Document Types

- Documents (Word, PDF, etc.)
- Emails
- Files
- Chat messages
- Spreadsheets
- Presentations
- Projects
- Notes

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Edit .env with your Elasticsearch settings
```

### Basic Usage

```python
import asyncio
from search import (
    ElasticsearchClient,
    DocumentIndexer,
    SearchEngine,
    SearchRequest,
)

async def main():
    # Initialize indices
    indexer = DocumentIndexer()
    await indexer.initialize_indices()

    # Search for documents
    search_engine = SearchEngine()
    request = SearchRequest(query="important meeting")
    response = await search_engine.search(request)

    print(f"Found {response.total} results")
    for hit in response.hits:
        print(f"- {hit.title} (score: {hit.score})")

asyncio.run(main())
```

## Configuration

### Environment Variables

```bash
# Elasticsearch Connection
ELASTICSEARCH_HOSTS=http://localhost:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=changeme

# Index Settings
ELASTICSEARCH_INDEX_PREFIX=nexus
ELASTICSEARCH_SHARDS=2
ELASTICSEARCH_REPLICAS=1

# Performance
ELASTICSEARCH_BULK_SIZE=500
ELASTICSEARCH_QUEUE_SIZE=1000
```

## Usage Examples

### 1. Indexing Documents

```python
from search.content_indexers import DocumentContentIndexer

indexer = DocumentContentIndexer()

# Index a single document
await indexer.index_document(
    doc_id="doc-123",
    title="Project Proposal",
    content="This is the project proposal content...",
    owner_id="user-1",
    owner_name="John Doe",
    tags=["project", "important"],
)

# Index directory of documents
result = await indexer.index_documents_from_directory(
    directory="/path/to/documents",
    owner_id="user-1",
    owner_name="John Doe",
    recursive=True,
)
print(f"Indexed {result['success']} documents")
```

### 2. Indexing Emails

```python
from search.content_indexers import EmailContentIndexer

indexer = EmailContentIndexer()

await indexer.index_email(
    email_id="email-456",
    subject="Q4 Planning Meeting",
    sender="manager@company.com",
    recipients=["team@company.com"],
    content="Let's discuss Q4 plans...",
    owner_id="user-1",
    owner_name="John Doe",
    has_attachments=True,
    attachment_names=["budget.xlsx"],
    importance="high",
    folder="inbox",
)
```

### 3. Indexing Files

```python
from search.content_indexers import FileContentIndexer

indexer = FileContentIndexer()

await indexer.index_file(
    file_id="file-789",
    file_name="report.pdf",
    file_path="/documents/reports/report.pdf",
    content="Extracted PDF content...",
    owner_id="user-1",
    owner_name="John Doe",
    file_type="pdf",
    file_size=1024000,
    mime_type="application/pdf",
    extension="pdf",
)
```

### 4. Indexing Chat Messages

```python
from search.content_indexers import ChatContentIndexer

indexer = ChatContentIndexer()

await indexer.index_message(
    message_id="msg-999",
    channel_id="channel-1",
    channel_name="general",
    sender="John Doe",
    message="Has anyone seen the latest report?",
    owner_id="user-1",
    owner_name="John Doe",
    participants=["user-1", "user-2", "user-3"],
)
```

### 5. Advanced Search with Filters

```python
from search import SearchRequest, SearchFilters
from search.models import DocumentType
from datetime import datetime, timedelta

# Search with filters
filters = SearchFilters(
    document_types=[DocumentType.EMAIL, DocumentType.DOCUMENT],
    owner_ids=["user-1"],
    tags=["important"],
    date_from=datetime.utcnow() - timedelta(days=30),
    has_attachments=True,
)

request = SearchRequest(
    query="quarterly report",
    filters=filters,
    page=1,
    page_size=20,
)

response = await search_engine.search(request)
```

### 6. Faceted Search

```python
from search.models import FacetRequest

request = SearchRequest(
    query="project",
    facets=[
        FacetRequest(field="type", size=10),
        FacetRequest(field="tags", size=20),
        FacetRequest(field="owner_id", size=10),
    ],
)

response = await search_engine.search(request)

# Display facets
for facet in response.facets:
    print(f"\n{facet.field}:")
    for bucket in facet.buckets:
        print(f"  {bucket.key}: {bucket.count}")
```

### 7. Autocomplete Search

```python
request = SearchRequest(
    query="proj",
    autocomplete=True,
)

response = await search_engine.search(request)

# Display suggestions
print("Suggestions:")
for suggestion in response.suggestions:
    print(f"  - {suggestion}")
```

### 8. Search with Highlighting

```python
request = SearchRequest(
    query="meeting agenda",
    highlight=True,
    highlight_fields=["title", "content", "subject"],
)

response = await search_engine.search(request)

for hit in response.hits:
    print(f"\n{hit.title}")
    for highlight in hit.highlights:
        print(f"  {highlight.field}:")
        for fragment in highlight.fragments:
            print(f"    {fragment}")
```

### 9. Bulk Indexing

```python
from search.indexer import AsyncIndexer

# Create async indexer with queue
async_indexer = AsyncIndexer(queue_size=1000)
await async_indexer.start()

# Queue documents for indexing
for doc in large_document_list:
    await async_indexer.queue_document(doc)

# Check queue status
queue_size = async_indexer.get_queue_size()
print(f"Documents in queue: {queue_size}")

# Stop indexer (wait for queue to drain)
await async_indexer.stop(wait=True)
```

### 10. Similar Documents

```python
from search.models import DocumentType

# Find similar documents
similar = await search_engine.get_similar_documents(
    doc_id="doc-123",
    doc_type=DocumentType.DOCUMENT,
    limit=10,
)

print("Similar documents:")
for doc in similar:
    print(f"  - {doc.title} (score: {doc.score})")
```

## Monitoring and Analytics

### Health Check

```python
from search.monitoring import health_monitor

health = await health_monitor.check_health()
print(f"Status: {health['status']}")
print(f"Cluster: {health['checks']['cluster_health']['cluster_name']}")
```

### Index Statistics

```python
from search.monitoring import analytics

stats = await analytics.get_index_stats()
for index_name, index_stats in stats['indices'].items():
    print(f"\n{index_name}:")
    print(f"  Documents: {index_stats['document_count']}")
    print(f"  Size: {index_stats['size_mb']} MB")
    print(f"  Searches: {index_stats['search_total']}")
```

### Search Performance

```python
perf = await analytics.get_search_performance()
print(f"Total queries: {perf['total_queries']}")
print(f"Average query time: {perf['average_query_time_ms']} ms")
print(f"Queries per second: {perf['queries_per_second']}")
```

### Document Distribution

```python
distribution = await analytics.get_document_distribution()
for doc_type, count in distribution.items():
    print(f"{doc_type}: {count} documents")
```

## Production Deployment

### Docker Compose Example

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  es_data:
```

### Performance Tuning

1. **Bulk Size**: Adjust `ELASTICSEARCH_BULK_SIZE` based on document size
2. **Queue Size**: Increase `ELASTICSEARCH_QUEUE_SIZE` for high-throughput indexing
3. **Shards**: Set appropriate shard count based on data volume
4. **Replicas**: Use replicas for high availability

### Index Optimization

```python
# Optimize indices periodically
results = await analytics.optimize_indices()
for index_name, success in results.items():
    print(f"{index_name}: {'optimized' if success else 'failed'}")
```

## API Reference

See individual module documentation:

- `search.client` - Elasticsearch client
- `search.indexer` - Document indexing
- `search.searcher` - Search engine
- `search.models` - Data models
- `search.content_indexers` - Content-specific indexers
- `search.monitoring` - Monitoring and analytics

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=search tests/

# Run specific test
pytest tests/test_search.py::test_search_basic
```

## License

Proprietary - Nexus Platform
