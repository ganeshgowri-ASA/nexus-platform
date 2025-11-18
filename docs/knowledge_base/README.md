# NEXUS Knowledge Base System

## Overview

The NEXUS Knowledge Base System is a comprehensive, production-ready platform for creating, managing, and delivering knowledge content. It features AI-powered search, multi-language support, collaborative authoring, and extensive integrations.

## Features

### Core Features

- **📝 Rich Content Management**: Create and manage articles, FAQs, tutorials, videos, and glossary terms
- **🔍 Advanced Search**: Semantic search with NLP, question answering, and autocomplete
- **🌍 Multi-Language Support**: Auto-translation and language detection
- **💬 AI Chatbot**: Instant answers from KB content powered by Claude/GPT-4
- **📊 Analytics**: Comprehensive usage tracking and content effectiveness metrics
- **⭐ Ratings & Feedback**: User ratings, helpful votes, and comments
- **🎓 Interactive Tutorials**: Step-by-step guides with progress tracking
- **🎥 Video Knowledge**: Video hosting with transcription and chapter navigation
- **📝 Glossary**: Terminology database with cross-references
- **👥 Collaborative Authoring**: Team collaboration and review workflows
- **📄 Templates**: Pre-built templates for common content types
- **📤 Export/Import**: PDF, DOCX, HTML export and import from other KB platforms
- **🔗 Integrations**: Connect with support tickets, CRM, and chat systems
- **🌐 Embedding**: Embed KB widget on external sites

### Technical Features

- **Production-Ready**: Full type hints, error handling, and logging
- **Scalable Architecture**: PostgreSQL, Redis caching, Celery for async tasks
- **Search Technologies**: Elasticsearch for full-text, Pinecone/Weaviate for semantic search
- **AI Integration**: Claude AI, GPT-4 for chatbot and recommendations
- **RESTful API**: FastAPI with OpenAPI documentation
- **Modern UI**: Streamlit-based interface
- **Security**: Access controls, public/private content
- **Performance**: Pagination, caching, CDN support

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 6+
- Elasticsearch 8+ (optional but recommended)
- Pinecone or Weaviate account (for semantic search)

### Setup

1. **Clone the repository**:
```bash
git clone https://github.com/your-org/nexus-platform.git
cd nexus-platform
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**:
```bash
alembic upgrade head
```

6. **Start services**:
```bash
# Start Redis
redis-server

# Start Celery worker
celery -A modules.knowledge_base.tasks worker -l info

# Start FastAPI server
uvicorn modules.knowledge_base.routes:router --reload

# Start Streamlit UI
streamlit run modules/knowledge_base/streamlit_ui.py
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/nexus_kb

# Redis
REDIS_URL=redis://localhost:6379/0

# Elasticsearch
ELASTICSEARCH_HOST=localhost:9200
ELASTICSEARCH_ENABLED=true

# Vector Database (Pinecone)
PINECONE_API_KEY=your-api-key
PINECONE_ENVIRONMENT=us-east1-gcp
PINECONE_INDEX=kb-embeddings

# AI / LLM
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key

# Translation
GOOGLE_TRANSLATE_API_KEY=your-google-key

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key
```

## Usage

### Creating Articles

```python
from modules.knowledge_base.articles import ArticleManager
from uuid import uuid4

# Initialize manager
article_mgr = ArticleManager(db_session)

# Create article
article = await article_mgr.create_article(
    title="Getting Started with NEXUS",
    content="<h1>Introduction</h1><p>Welcome to NEXUS...</p>",
    author_id=uuid4(),
    category_id=category_id,
    tags=["getting-started", "tutorial"],
)

# Publish article
published = await article_mgr.publish_article(article.id)
```

### Searching Content

```python
from modules.knowledge_base.search import SearchEngine

# Initialize search engine
search = SearchEngine(db_session, es_client, vector_db_client)

# Search
results = await search.search(
    query="How do I get started?",
    use_semantic=True,
    limit=10,
)

# Question answering
answer = await search.question_answering(
    question="What is NEXUS?",
)
```

### Using the Chatbot

```python
from modules.knowledge_base.chatbot import ChatbotManager

# Initialize chatbot
chatbot = ChatbotManager(db_session, llm_client, search_engine)

# Create session
session = await chatbot.create_session(user_id=user_id)

# Send message
response = await chatbot.send_message(
    session_id=session.id,
    message="How do I integrate the API?",
)
```

### API Endpoints

The Knowledge Base provides a comprehensive REST API:

#### Articles
- `POST /api/kb/articles` - Create article
- `GET /api/kb/articles/{id}` - Get article
- `PUT /api/kb/articles/{id}` - Update article
- `DELETE /api/kb/articles/{id}` - Delete article
- `POST /api/kb/articles/{id}/publish` - Publish article
- `GET /api/kb/articles` - List articles

#### Search
- `POST /api/kb/search` - Search KB
- `GET /api/kb/search/autocomplete` - Autocomplete
- `POST /api/kb/search/question` - Question answering

#### Categories
- `POST /api/kb/categories` - Create category
- `GET /api/kb/categories` - List categories
- `GET /api/kb/categories/tree` - Get category tree

#### FAQs
- `POST /api/kb/faqs` - Create FAQ
- `GET /api/kb/faqs` - List FAQs

#### Analytics
- `GET /api/kb/analytics/content/{id}` - Get content stats
- `GET /api/kb/analytics/popular` - Get popular content

See full API documentation at `/docs` when running the FastAPI server.

## Architecture

### Components

```
modules/knowledge_base/
├── __init__.py              # Module initialization
├── kb_types.py              # Type definitions
├── models.py                # Database models
├── articles.py              # Article management
├── categories.py            # Categories and tags
├── search.py                # Search engine
├── faqs.py                  # FAQ management
├── tutorials.py             # Tutorial system
├── videos.py                # Video management
├── glossary.py              # Glossary terms
├── ratings.py               # Ratings and feedback
├── recommendations.py       # AI recommendations
├── multilingual.py          # Multi-language support
├── versioning.py            # Version control
├── analytics.py             # Analytics tracking
├── chatbot.py               # AI chatbot
├── embedding.py             # Widget embedding
├── authoring.py             # Collaborative authoring
├── templates.py             # Content templates
├── export.py                # Export functionality
├── import_kb.py             # Import functionality
├── integration.py           # Third-party integrations
├── routes.py                # FastAPI routes
├── tasks.py                 # Celery tasks
├── config.py                # Configuration
└── streamlit_ui.py          # Streamlit UI
```

### Database Schema

The system uses PostgreSQL with the following main tables:

- `kb_articles` - Article content
- `kb_categories` - Hierarchical categories
- `kb_tags` - Content tags
- `kb_faqs` - FAQ entries
- `kb_tutorials` - Interactive tutorials
- `kb_videos` - Video content
- `kb_glossary_terms` - Glossary definitions
- `kb_ratings` - User ratings and feedback
- `kb_analytics_events` - Analytics tracking
- `kb_chat_sessions` - Chatbot sessions
- `kb_article_versions` - Version history

### Search Architecture

1. **Full-Text Search** (Elasticsearch):
   - Fast text matching
   - Filtering and faceting
   - Highlighting

2. **Semantic Search** (Pinecone/Weaviate):
   - Vector embeddings
   - Similarity search
   - Intent understanding

3. **Hybrid Search**:
   - Combines results from both engines
   - Re-ranking based on relevance

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=modules.knowledge_base

# Run specific test file
pytest tests/knowledge_base/test_articles.py -v
```

## Performance

### Optimization Tips

1. **Enable caching**:
   - Redis caching for frequently accessed content
   - CDN for static assets

2. **Use pagination**:
   - Limit results to 20-50 per page
   - Implement infinite scroll for better UX

3. **Optimize search**:
   - Use filters to narrow results
   - Enable semantic search only when needed

4. **Async operations**:
   - Index content asynchronously with Celery
   - Generate embeddings in background

## Security

### Best Practices

1. **Access Control**:
   - Use `access_level` field to control visibility
   - Implement role-based permissions

2. **Content Sanitization**:
   - Sanitize HTML content before saving
   - Validate user inputs

3. **API Security**:
   - Use API keys for authentication
   - Implement rate limiting
   - Enable CORS only for trusted origins

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure production database
- [ ] Set up Redis sentinel
- [ ] Configure Elasticsearch cluster
- [ ] Set up Celery with supervisor
- [ ] Enable SSL/TLS
- [ ] Configure CDN
- [ ] Set up monitoring (Sentry, Prometheus)
- [ ] Configure backups
- [ ] Set up log aggregation

### Docker Deployment

```bash
# Build image
docker build -t nexus-kb:latest .

# Run with docker-compose
docker-compose up -d
```

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/api/kb/health

# Celery status
celery -A modules.knowledge_base.tasks inspect active
```

### Metrics

- Article views
- Search queries
- Chatbot conversations
- API response times
- Error rates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

Copyright © 2024 NEXUS Platform Team. All rights reserved.

## Support

For support, please contact:
- Email: support@nexus.com
- Documentation: https://docs.nexus.com
- GitHub Issues: https://github.com/your-org/nexus-platform/issues
