# Nexus Platform

NEXUS: Unified AI-powered productivity platform with 24 integrated modules - Word, Excel, PPT, Projects, Email, Chat, Flowcharts, Analytics, Meetings & more. Built with Streamlit & Claude AI.

## 🔍 Elasticsearch Search Module

A production-ready, full-text search engine for the Nexus platform with advanced features.

### Features

✅ **Full-text search** with relevance scoring
✅ **Async document indexing** with queue support
✅ **Advanced filtering** (document types, dates, owners, tags)
✅ **Faceted search** with aggregations
✅ **Autocomplete** suggestions
✅ **Syntax highlighting** in search results
✅ **Multi-field search** with boosting
✅ **Bulk indexing** for high throughput
✅ **Production-ready** with health checks and monitoring

### Quick Start

```bash
# Start Elasticsearch and Redis
make docker-up

# Initialize search indices
make init-search

# Run examples
python examples/basic_search.py
```

### Documentation

- **[Search Module README](search/README.md)** - Comprehensive API documentation
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions
- **[Examples](examples/)** - Usage examples and demos

### Project Structure

```
nexus-platform/
├── search/                 # Elasticsearch search module
│   ├── __init__.py
│   ├── client.py          # Elasticsearch client
│   ├── config.py          # Configuration management
│   ├── models.py          # Data models
│   ├── schemas.py         # Index schemas
│   ├── indexer.py         # Document indexing
│   ├── searcher.py        # Search engine
│   ├── content_indexers.py # Content-specific indexers
│   ├── monitoring.py      # Monitoring & analytics
│   ├── utils.py           # Utility functions
│   └── README.md          # Search documentation
├── tests/                 # Test suite
├── examples/              # Usage examples
├── scripts/               # Utility scripts
├── docker-compose.yml     # Docker configuration
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Supported Document Types

- 📄 Documents (Word, PDF, etc.)
- 📧 Emails
- 📁 Files
- 💬 Chat messages
- 📊 Spreadsheets
- 📽️ Presentations
- 📋 Projects
- 📝 Notes

### Usage Example

```python
import asyncio
from search import SearchEngine, SearchRequest

async def main():
    search_engine = SearchEngine()

    # Basic search
    request = SearchRequest(query="important meeting")
    response = await search_engine.search(request)

    print(f"Found {response.total} results")
    for hit in response.hits:
        print(f"- {hit.title} (score: {hit.score})")

asyncio.run(main())
```

### Requirements

- Python 3.8+
- Elasticsearch 8.x
- Redis 5.x+ (for async indexing)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd nexus-platform

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start services
docker-compose up -d

# Initialize indices
python scripts/init_search.py
```

### Development

```bash
# Run tests
make test

# Lint code
make lint

# Format code
make format

# Clean cache
make clean
```

### License

Proprietary - Nexus Platform

---

## Session Information

**Session 10: Elasticsearch Search Implementation**
Full-text search engine with document indexing, search API, filters, facets, autocomplete, relevance scoring, highlighting, and aggregations. Production-ready with comprehensive testing and documentation.
