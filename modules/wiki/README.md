# NEXUS Wiki System

A comprehensive, production-ready wiki system for the NEXUS platform with advanced features including real-time collaboration, AI-powered assistance, version control, and extensive integrations.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🚀 Features

### Core Functionality
- **Rich Text Editing**: WYSIWYG editor with markdown support, syntax highlighting, tables, and media embedding
- **Version Control**: Complete history tracking with visual diff, one-click rollback, and version comparison
- **Smart Linking**: Auto-suggest internal links, backlink tracking, broken link detection, and redirect management
- **Hierarchical Organization**: Nested pages, categories, namespaces, and breadcrumb navigation
- **Advanced Search**: Full-text search, semantic search, filters by category/tag/date/author

### Collaboration
- **Real-Time Editing**: Multiple users can edit simultaneously with conflict resolution
- **Comments & Discussions**: Threaded comments, mentions, reactions, and notifications
- **Presence Indicators**: See who's currently viewing or editing pages
- **Activity Feeds**: Recent changes, watchlists, and personalized content feeds

### Content Management
- **Page Templates**: Pre-built templates for meeting notes, project docs, how-tos, API documentation, etc.
- **Dynamic Macros**: Embed tables of contents, page lists, code snippets, charts, and queries
- **Attachments**: Images, videos, files with preview and version control
- **Categories & Tags**: Flexible categorization with hierarchical categories and tag clouds

### Advanced Features
- **AI Assistant**: Content suggestions, auto-linking, summarization, Q&A, and grammar checking
- **Analytics**: Page views, popular pages, contributor stats, and activity heatmaps
- **Permissions**: Granular page, namespace, and category-level access controls
- **Export/Import**: Multi-format export (PDF, HTML, Markdown, DOCX) and import from Confluence, MediaWiki, Notion

### Integrations
- **Slack**: Notifications, slash commands, link unfurling
- **Microsoft Teams**: Adaptive cards, webhooks, bot integration
- **GitHub**: Wiki sync, issue linking, PR references
- **JIRA**: Ticket linking, documentation sync

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Usage Guide](#usage-guide)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

## 💻 Installation

### Prerequisites

- Python 3.9+
- PostgreSQL 12+ (or SQLite for development)
- Redis (optional, for caching and WebSocket)
- Node.js 16+ (optional, for advanced features)

### Install Dependencies

```bash
# Install main NEXUS platform dependencies
pip install -r requirements.txt

# Install wiki-specific dependencies
pip install -r modules/wiki/requirements.txt
```

### Database Setup

```bash
# Create database tables
python -c "from modules.wiki.models import create_all_tables; create_all_tables()"

# Or use Alembic for migrations
alembic upgrade head
```

### Environment Variables

Create a `.env` file:

```env
# Database
DATABASE__URL=postgresql://user:pass@localhost/nexus

# AI Features
ANTHROPIC__API_KEY=your-api-key-here

# Wiki Configuration
WIKI__ENABLED=true
WIKI__STORAGE_PATH=data/wiki/attachments
WIKI__ENABLE_AI_ASSISTANT=true
WIKI__ENABLE_REAL_TIME_EDITING=true

# Integrations (optional)
WIKI__ENABLE_SLACK_INTEGRATION=true
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-secret

WIKI__ENABLE_GITHUB_INTEGRATION=true
GITHUB_TOKEN=ghp_your_token
```

## 🚀 Quick Start

### 1. Start the Wiki System

```python
from modules.wiki import get_page_manager, get_editor_service
from database import SessionLocal

# Initialize database session
db = SessionLocal()

# Create a page manager
page_manager = get_page_manager(db)

# Create your first page
from modules.wiki.wiki_types import PageCreateRequest, PageStatus

request = PageCreateRequest(
    title="Getting Started",
    content="# Welcome to NEXUS Wiki\n\nThis is your first page!",
    namespace="docs",
    tags=["tutorial", "getting-started"],
    status=PageStatus.PUBLISHED
)

page = page_manager.create_page(request, author_id=1, auto_publish=True)
print(f"Created page: {page.title} at {page.full_path}")
```

### 2. Launch the Streamlit UI

```bash
streamlit run modules/wiki/streamlit_ui.py
```

### 3. Access the REST API

```bash
# Start FastAPI server
uvicorn app.main:app --reload

# Access API documentation
open http://localhost:8000/docs

# Example API call
curl -X GET "http://localhost:8000/api/wiki/pages" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Enable Real-Time Collaboration

```bash
# WebSocket endpoint
ws://localhost:8000/ws/wiki
```

## 🏗️ Architecture

### Module Structure

```
modules/wiki/
├── __init__.py                 # Module interface
├── wiki_types.py              # Pydantic models and enums
├── models.py                  # SQLAlchemy database models
│
├── Core Services
├── pages.py                   # Page CRUD operations
├── editor.py                  # Rich text editing
├── versioning.py              # Version control
├── linking.py                 # Link management
├── categories.py              # Category hierarchy
├── search.py                  # Search functionality
├── navigation.py              # Navigation utilities
│
├── Content & Collaboration
├── templates.py               # Page templates
├── macros.py                  # Dynamic content
├── attachments.py             # File management
├── comments.py                # Discussion system
├── collaboration.py           # Real-time features
├── permissions.py             # Access control
│
├── Advanced Features
├── analytics.py               # Usage tracking
├── ai_assistant.py            # AI features
├── export.py                  # Export functionality
├── import.py                  # Import functionality
├── integration.py             # External integrations
│
└── Interface
    ├── streamlit_ui.py        # Streamlit interface
    └── websocket.py           # WebSocket handler

api/routers/
└── wiki.py                    # FastAPI REST endpoints
```

### Database Schema

The wiki system uses 12 main tables:

- `wiki_pages`: Core page data
- `wiki_categories`: Hierarchical categories
- `wiki_tags`: Tags for categorization
- `wiki_sections`: Page sections
- `wiki_links`: Internal/external links
- `wiki_attachments`: File attachments
- `wiki_comments`: Discussion threads
- `wiki_history`: Version history
- `wiki_permissions`: Access control
- `wiki_templates`: Page templates
- `wiki_analytics`: Usage metrics
- `wiki_macros`: Custom macros

### Service Layer

Each major feature has a dedicated service class:

- `PageManager`: Page CRUD and organization
- `EditorService`: Content processing and editing
- `VersioningService`: Version control operations
- `LinkingService`: Link management and validation
- `CategoryService`: Category and tag management
- `SearchService`: Search and discovery
- `NavigationService`: Navigation utilities
- `TemplateService`: Template management
- `CollaborationService`: Real-time collaboration
- `PermissionService`: Access control
- `MacroService`: Dynamic content generation
- `ExportService`: Export to various formats
- `ImportService`: Import from external sources
- `AttachmentService`: File management
- `CommentService`: Discussion management
- `AnalyticsService`: Analytics tracking
- `AIAssistantService`: AI-powered features
- `IntegrationService`: External integrations

## ⚙️ Configuration

### Wiki Settings

Configure the wiki system in `app/config.py` or via environment variables:

```python
# Example configuration
settings.wiki.enabled = True
settings.wiki.max_attachment_size = 104857600  # 100MB
settings.wiki.enable_ai_assistant = True
settings.wiki.enable_real_time_editing = True
settings.wiki.search_results_per_page = 20
```

### Feature Flags

Enable or disable features:

```env
# AI Features
WIKI__ENABLE_AI_ASSISTANT=true
WIKI__ENABLE_AUTO_LINKING=true
WIKI__ENABLE_AUTO_TAGGING=true

# Collaboration
WIKI__ENABLE_COMMENTS=true
WIKI__ENABLE_REAL_TIME_EDITING=true

# Integrations
WIKI__ENABLE_SLACK_INTEGRATION=false
WIKI__ENABLE_GITHUB_INTEGRATION=false
```

## 📖 API Documentation

### REST Endpoints

#### Pages

```bash
# List pages
GET /api/wiki/pages?limit=20&offset=0&status=published

# Create page
POST /api/wiki/pages
{
  "title": "My Page",
  "content": "Page content",
  "namespace": "docs",
  "tags": ["tutorial"]
}

# Get page
GET /api/wiki/pages/{page_id}

# Update page
PUT /api/wiki/pages/{page_id}
{
  "content": "Updated content",
  "change_summary": "Fixed typos"
}

# Delete page
DELETE /api/wiki/pages/{page_id}
```

#### Search

```bash
# Search pages
GET /api/wiki/search?query=tutorial&category_id=5&limit=20

# Advanced search
POST /api/wiki/search
{
  "query": "python tutorial",
  "tags": ["python", "beginner"],
  "date_from": "2024-01-01",
  "include_content": true
}
```

#### Version History

```bash
# Get page history
GET /api/wiki/pages/{page_id}/history

# Get specific version
GET /api/wiki/pages/{page_id}/history/{version}

# Restore version
POST /api/wiki/pages/{page_id}/history/{version}/restore
```

For complete API documentation, visit `/docs` when running the FastAPI server.

### WebSocket API

Connect to `ws://localhost:8000/ws/wiki`:

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/wiki');

// Send message
ws.send(JSON.stringify({
  type: 'PAGE_OPENED',
  page_id: 123,
  user_id: 1
}));

// Receive updates
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message.type);
};
```

## 📚 Usage Guide

### Creating Pages

```python
from modules.wiki.pages import PageManager
from modules.wiki.wiki_types import PageCreateRequest

manager = PageManager(db)

# Create from scratch
request = PageCreateRequest(
    title="API Documentation",
    content="# API Guide\n\nComplete API reference...",
    category_id=5,
    tags=["api", "reference"]
)
page = manager.create_page(request, author_id=1)

# Create from template
from modules.wiki.templates import TemplateService

template_service = TemplateService(db)
page = template_service.create_page_from_template(
    template_id=1,
    title="Sprint Planning Meeting",
    variables={"date": "2024-01-15", "sprint": "Sprint 10"},
    author_id=1
)
```

### Version Control

```python
from modules.wiki.versioning import VersioningService

versioning = VersioningService(db)

# Get history
history, total = versioning.get_page_history(page_id=123, limit=50)

# Compare versions
diff = versioning.compare_versions(page_id=123, version1=1, version2=2)
print(diff['html_diff'])

# Rollback
page = versioning.rollback_to_version(
    page_id=123,
    version=5,
    user_id=1,
    change_summary="Reverting spam edits"
)
```

### Search

```python
from modules.wiki.search import SearchService

search = SearchService(db)

# Full-text search
results, total = search.search_pages(
    query="python tutorial",
    limit=20
)

# Advanced search
from modules.wiki.wiki_types import PageSearchRequest

request = PageSearchRequest(
    query="API",
    tags=["python", "rest"],
    category_id=5,
    status=PageStatus.PUBLISHED
)
results, total = search.advanced_search(request)
```

### AI Assistant

```python
from modules.wiki.ai_assistant import AIAssistantService

ai = AIAssistantService()

# Summarize content
summary = ai.summarize_content(
    content=page.content,
    max_length=200
)

# Suggest links
suggestions = ai.suggest_links(
    content=page.content,
    existing_pages=all_pages
)

# Suggest tags
tags = ai.suggest_tags(
    content=page.content,
    existing_tags=all_tags,
    max_tags=5
)
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest modules/wiki/tests/ -v

# Run with coverage
pytest modules/wiki/tests/ --cov=modules/wiki --cov-report=html

# Run specific test file
pytest modules/wiki/tests/test_pages.py -v

# Run specific test
pytest modules/wiki/tests/test_pages.py::test_create_page -v
```

### Test Structure

```
modules/wiki/tests/
├── conftest.py                # Test fixtures
├── test_pages.py              # Page tests
├── test_versioning.py         # Version control tests
├── test_search.py             # Search tests
├── test_permissions.py        # Permission tests
├── test_collaboration.py      # Collaboration tests
└── test_api.py                # API endpoint tests
```

## 🚢 Deployment

### Production Checklist

- [ ] Set strong `security.secret_key`
- [ ] Use PostgreSQL for database
- [ ] Enable Redis for caching
- [ ] Configure proper file storage (S3, Azure Blob)
- [ ] Set up SSL/TLS certificates
- [ ] Configure rate limiting
- [ ] Enable monitoring and logging
- [ ] Set up backups
- [ ] Configure CDN for attachments
- [ ] Enable API authentication

### Docker Deployment

```bash
# Build image
docker build -t nexus-wiki .

# Run container
docker run -d \
  -p 8000:8000 \
  -e DATABASE__URL=postgresql://... \
  -e ANTHROPIC__API_KEY=... \
  -v /data/wiki:/app/data/wiki \
  nexus-wiki
```

### Production Configuration

```env
# Production settings
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE__URL=postgresql://user:pass@db-host/nexus
DATABASE__POOL_SIZE=20
DATABASE__MAX_OVERFLOW=40

# Security
SECURITY__SECRET_KEY=your-strong-secret-key
SECURITY__ALLOWED_ORIGINS=["https://yourdomain.com"]

# Wiki
WIKI__STORAGE_PATH=/data/wiki/attachments
WIKI__MAX_ATTACHMENT_SIZE=104857600
WIKI__ENABLE_CACHING=true
WIKI__CACHE_TTL=3600

# Rate Limiting
WIKI__RATE_LIMIT_ENABLED=true
WIKI__RATE_LIMIT_PER_MINUTE=60
```

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest`)
5. Format code with `black` and `isort`
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style

- Follow PEP 8
- Use type hints for all functions
- Write Google-style docstrings
- Add tests for new features
- Update documentation

## 📄 License

This project is part of the NEXUS Platform and follows the same license terms.

## 🙏 Acknowledgments

- Built on the NEXUS Platform architecture
- Uses Anthropic Claude for AI features
- Inspired by Confluence, Notion, and MediaWiki

## 📞 Support

- Documentation: `/docs`
- Issues: Create an issue on GitHub
- Email: support@nexus-platform.example

---

Built with ❤️ by the NEXUS Platform Team
