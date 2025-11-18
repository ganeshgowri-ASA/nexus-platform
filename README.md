# Nexus Platform

> NEXUS: Unified AI-powered productivity platform with 24 integrated modules - Word, Excel, PPT, Projects, Email, Chat, Flowcharts, Analytics, Meetings & more. Built with Streamlit & Claude AI.

## Overview

Nexus Platform is a comprehensive productivity suite that combines the power of AI with modern productivity tools. The platform is designed to rival industry leaders like Notion, Evernote, and Microsoft Office, providing a unified experience for all your productivity needs.

## Features

### 📝 Notes Module (COMPLETE)

A comprehensive note-taking system that rivals Notion and Evernote with the following features:

#### Rich Text Editing
- **WYSIWYG Editor**: Visual editing with real-time preview
- **Markdown Support**: Full markdown syntax support with live rendering
- **Code Blocks**: Syntax highlighting for multiple programming languages
- **Tables**: Create and edit tables seamlessly
- **Checklists**: Interactive task lists with checkboxes
- **Media Embed**: Support for images, videos, and other media

#### Organization
- **Notebooks**: Organize notes into customizable notebooks
- **Sections**: Further categorize notes within notebooks
- **Tags**: Flexible tagging system with color-coded tags
- **Favorites**: Quick access to important notes
- **Archive**: Keep your workspace clean without deleting notes

#### Search & Discovery
- **Full-Text Search**: Search across all note content
- **Tag Filtering**: Filter notes by one or more tags
- **Date Range Filters**: Find notes by creation or update date
- **Saved Searches**: Save frequently used search queries
- **Smart Suggestions**: AI-powered search suggestions

#### Collaboration
- **Share Notes**: Share notes with other users
- **Real-Time Editing**: Collaborative editing (planned)
- **Comments**: Add comments and discussions to notes
- **Permissions**: Fine-grained access control (view, comment, edit, admin)

#### Templates
- **Meeting Notes**: Pre-formatted meeting notes template
- **Project Plans**: Structured project planning template
- **To-Do Lists**: Task management template
- **Journal**: Daily journal template
- **Custom Templates**: Create and share your own templates

#### Attachments
- **Files**: Attach any file type to notes
- **Images**: Embed and display images
- **Audio**: Attach audio recordings
- **Links**: Embed external links with previews

#### Sync & Version Control
- **Cross-Device Sync**: Access notes from anywhere (planned)
- **Cloud Backup**: Automatic cloud backup (planned)
- **Version History**: Track changes with full version history
- **Restore**: Revert to previous versions easily

#### Export Options
- **PDF Export**: Professional PDF documents
- **Word Export**: Microsoft Word format (.docx)
- **Markdown Export**: Plain markdown files
- **HTML Export**: Rich HTML with styling

#### AI Assistant
Powered by Claude AI, the notes module includes:
- **Auto-Summarize**: Generate concise summaries of notes
- **Extract Tasks**: Automatically identify action items
- **Smart Tags**: AI-suggested tags based on content
- **Grammar Check**: Real-time grammar and style suggestions
- **Title Generation**: Auto-generate titles from content
- **Expand Outlines**: Turn bullet points into detailed content
- **Format Meeting Notes**: Structure raw meeting notes
- **Related Topics**: Discover related topics to explore

#### Integration
- **Calendar Integration**: Link notes to calendar events
- **Project Integration**: Associate notes with projects
- **Chat Integration**: Create notes from conversations

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/nexus-platform.git
cd nexus-platform
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

4. Initialize the database:
```bash
python -c "from nexus.core.database import init_db; init_db()"
```

5. Run the application:
```bash
streamlit run app.py
```

### Configuration

Edit the `.env` file to configure:

- **Database**: Set `DATABASE_URL` (default: SQLite)
- **API Keys**: Add your `CLAUDE_API_KEY` for AI features
- **Upload Settings**: Configure `UPLOAD_DIR` and `MAX_UPLOAD_SIZE_MB`
- **Features**: Enable/disable features with boolean flags

## Architecture

### Project Structure

```
nexus-platform/
├── src/nexus/
│   ├── core/                    # Core infrastructure
│   │   ├── config.py           # Configuration management
│   │   ├── database.py         # Database setup
│   │   ├── logger.py           # Logging configuration
│   │   └── exceptions.py       # Custom exceptions
│   ├── modules/                # Feature modules
│   │   └── notes/              # Notes module
│   │       ├── models.py       # Database models
│   │       ├── schemas.py      # Pydantic schemas
│   │       ├── repository.py   # Data access layer
│   │       ├── service.py      # Business logic
│   │       ├── markdown_processor.py
│   │       ├── ai_assistant.py
│   │       ├── export.py
│   │       ├── ui/             # UI components
│   │       ├── integrations/   # Module integrations
│   │       └── tests/          # Unit tests
│   ├── shared/                 # Shared utilities
│   └── pages/                  # Streamlit pages
├── tests/                      # Integration tests
├── config/                     # Configuration files
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
├── app.py                      # Main application
├── requirements.txt            # Dependencies
└── pyproject.toml             # Project configuration
```

### Architecture Principles

1. **Layered Architecture**: Clear separation between UI, business logic, and data layers
2. **Dependency Injection**: Services receive dependencies explicitly
3. **Type Safety**: Full type hints throughout the codebase
4. **Testability**: Each layer can be tested independently
5. **Modularity**: Features organized as independent modules

## Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **Backend**: Python 3.10+
- **Database**: SQLAlchemy ORM (SQLite/PostgreSQL)
- **AI**: Anthropic Claude API
- **Document Processing**:
  - Markdown: python-markdown
  - PDF: WeasyPrint, ReportLab
  - Word: python-docx
- **Testing**: pytest
- **Code Quality**: black, ruff, mypy

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest src/nexus/modules/notes/tests/test_service.py
```

### Code Quality

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## API Documentation

### Notes Service API

#### Create Note
```python
from nexus.modules.notes.service import NoteService
from nexus.modules.notes.schemas import NoteCreate

service = NoteService(db_session)
note_data = NoteCreate(
    title="My Note",
    content="Note content",
    tags=["important", "work"]
)
note = service.create_note(user_id="user123", data=note_data)
```

#### Search Notes
```python
notes = service.search_notes(
    user_id="user123",
    query="meeting",
    tags=["work"],
    date_from=datetime(2024, 1, 1)
)
```

#### Export Notes
```python
from nexus.modules.notes.export import NoteExporter

exporter = NoteExporter()
pdf_bytes = exporter.export_notes(
    notes=[note1, note2],
    format="pdf"
)
```

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t nexus-platform .

# Run container
docker run -p 8501:8501 \
  -e DATABASE_URL=postgresql://... \
  -e CLAUDE_API_KEY=sk-ant-... \
  nexus-platform
```

### Cloud Deployment

The application can be deployed to:
- **Streamlit Cloud**: Native deployment platform
- **Heroku**: PaaS deployment
- **AWS/GCP/Azure**: Cloud infrastructure
- **Docker**: Containerized deployment

## Roadmap

### Phase 1: Foundation (COMPLETE)
- ✅ Notes module with full features
- ✅ AI-powered assistance
- ✅ Export functionality
- ✅ Integration framework

### Phase 2: Upcoming
- [ ] Calendar module
- [ ] Projects module
- [ ] Chat/Messaging module
- [ ] Real-time collaboration
- [ ] Mobile app

### Phase 3: Advanced Features
- [ ] Analytics dashboard
- [ ] Email client
- [ ] Presentation builder
- [ ] Spreadsheet editor
- [ ] Flowchart designer

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/nexus-platform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/nexus-platform/discussions)

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [Anthropic Claude](https://www.anthropic.com/)
- Inspired by Notion, Evernote, and Microsoft Office

---

**Built with ❤️ for productivity enthusiasts**
