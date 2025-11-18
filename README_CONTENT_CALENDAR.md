# NEXUS Content Calendar Module

A comprehensive, production-ready content calendar system for the NEXUS platform with AI-powered features, multi-channel publishing, and advanced collaboration tools.

## Features

### 📅 Visual Calendar
- Month, week, and day views
- Drag-and-drop event scheduling
- Multi-channel content planning
- Color-coded status indicators
- Bulk operations support

### ✍️ Content Creation
- Rich text editor
- AI-powered content suggestions
- Content templates library
- Media management (images, videos)
- Multi-format support (posts, articles, videos, etc.)

### 🤖 AI Assistant
- Content idea generation
- Draft creation
- Content improvement suggestions
- Hashtag generation
- SEO optimization

### ⏰ Smart Scheduling
- Auto-scheduling at optimal times
- Recurring content patterns
- Timezone support
- Schedule conflict detection
- Campaign scheduling

### 👥 Team Collaboration
- Task assignments
- Approval workflows
- Comments and discussions
- Version control
- Real-time updates (WebSocket)

### 📊 Analytics & Reporting
- Performance tracking
- Engagement metrics
- Content ROI calculation
- Channel performance comparison
- Top content identification
- Audience insights

### 🔗 Multi-Platform Integration
- Twitter/X
- Facebook
- Instagram
- LinkedIn
- Blog platforms
- Email campaigns

## Architecture

```
nexus-platform/
├── modules/
│   └── content_calendar/
│       ├── __init__.py
│       ├── calendar_types.py      # Type definitions
│       ├── planner.py             # Calendar planning
│       ├── content.py             # Content management
│       ├── scheduling.py          # Auto-scheduling
│       ├── workflows.py           # Approval workflows
│       ├── collaboration.py       # Team features
│       ├── analytics.py           # Performance tracking
│       ├── integration.py         # External platforms
│       └── streamlit_ui.py        # Web interface
├── api.py                         # FastAPI routes
├── celery_app.py                  # Async tasks
├── database.py                    # Database models
├── config.py                      # Configuration
└── tests/                         # Test suite
```

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 6+

### Setup

1. **Clone the repository:**

```bash
git clone https://github.com/your-org/nexus-platform.git
cd nexus-platform
```

2. **Create virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ANTHROPIC_API_KEY`: Claude AI API key
- Social media API credentials (optional)

5. **Initialize database:**

```bash
python -c "from database import init_db; init_db()"
```

## Running the Application

### Start FastAPI Server

```bash
# Development
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

API will be available at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### Start Streamlit UI

```bash
streamlit run modules/content_calendar/streamlit_ui.py
```

UI will be available at `http://localhost:8501`

### Start Celery Worker

```bash
celery -A celery_app worker --loglevel=info
```

### Start Celery Beat (Scheduler)

```bash
celery -A celery_app beat --loglevel=info
```

## API Endpoints

### Calendar

- `GET /api/calendar/events` - Get calendar events
- `POST /api/calendar/events` - Create event
- `PUT /api/calendar/events/{id}` - Update event
- `DELETE /api/calendar/events/{id}` - Delete event
- `POST /api/calendar/events/{id}/move` - Move event (drag-drop)

### Content

- `POST /api/content` - Create content
- `GET /api/content/{id}` - Get content
- `GET /api/content/search` - Search content
- `POST /api/content/generate-ideas` - Generate AI ideas

### Scheduling

- `POST /api/scheduling/schedule` - Schedule content
- `POST /api/scheduling/auto-schedule` - Auto-schedule
- `GET /api/scheduling/optimal-times` - Get optimal times

### Workflows

- `POST /api/workflows` - Create workflow
- `GET /api/workflows/{content_id}` - Get workflow

### Analytics

- `GET /api/analytics/content/{id}` - Get content performance
- `GET /api/analytics/top-content` - Get top content

### Integrations

- `POST /api/integrations/publish` - Publish content
- `POST /api/integrations/sync-analytics/{id}` - Sync analytics

### WebSocket

- `WS /ws` - Real-time updates

## Usage Examples

### Creating Content with AI

```python
from modules.content_calendar import ContentManager
from database import SessionLocal

db = SessionLocal()
manager = ContentManager(db)

# Generate content ideas
ideas = manager.generate_content_ideas(
    topic="AI in Marketing",
    content_type="article",
    count=5
)

# Generate draft
draft = manager.generate_content_draft(
    title="AI-Powered Marketing Strategies",
    description="Article about using AI in marketing",
    content_type="article",
    length="long"
)

# Create content
content = manager.create_content(
    title="AI-Powered Marketing Strategies",
    content=draft,
    content_type=ContentFormat.ARTICLE,
    creator_id=1
)
```

### Auto-Scheduling

```python
from modules.content_calendar import ContentScheduler

scheduler = ContentScheduler(db)

# Auto-schedule at optimal time
scheduled = scheduler.auto_schedule(
    content_id=123,
    channel="twitter",
    timezone="America/New_York"
)

# Get optimal posting times
optimal_times = scheduler.get_optimal_posting_times(
    channel="twitter",
    top_n=5
)
```

### Publishing Content

```python
from modules.content_calendar import IntegrationManager

integration = IntegrationManager(db)

# Publish to multiple channels
results = integration.publish_content(
    content_id=123,
    channels=["twitter", "facebook", "linkedin"]
)

# Sync analytics
integration.sync_analytics(content_id=123)
```

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=modules --cov-report=html

# Run specific test file
pytest tests/test_planner.py

# Run with verbose output
pytest -v
```

## Configuration

### Database Models

The system uses SQLAlchemy with the following main models:

- `User` - User accounts
- `ContentItem` - Content items
- `Campaign` - Marketing campaigns
- `Assignment` - Task assignments
- `Comment` - Comments and feedback
- `Approval` - Workflow approvals
- `ContentVersion` - Version history
- `Template` - Content templates
- `Analytics` - Performance metrics

### Celery Tasks

Scheduled tasks run automatically:

- **Every minute**: Check for scheduled content
- **Hourly**: Sync analytics from platforms
- **Daily 9 AM**: Send deadline reminders
- **Daily midnight**: Generate recurring content
- **Weekly**: Clean up old data

## Security

- All passwords are hashed using bcrypt
- JWT-based authentication (implement as needed)
- CORS configuration
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy ORM

## Performance

- Database connection pooling
- Redis caching for frequently accessed data
- Async task processing with Celery
- WebSocket for real-time updates
- Efficient database queries with proper indexing

## Monitoring

- Logging with loguru
- Celery monitoring with Flower:
  ```bash
  celery -A celery_app flower
  ```
- API metrics with Prometheus (integration ready)

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t nexus-content-calendar .

# Run containers
docker-compose up -d
```

### Production Checklist

- [ ] Set secure `SECRET_KEY`
- [ ] Configure production database
- [ ] Set up Redis with persistence
- [ ] Configure social media API credentials
- [ ] Enable HTTPS
- [ ] Set up monitoring and alerting
- [ ] Configure backups
- [ ] Set appropriate CORS origins
- [ ] Review and set rate limits

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
systemctl status postgresql

# Test connection
psql -h localhost -U user -d nexus_db
```

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping

# Should return: PONG
```

### Celery Not Processing Tasks

```bash
# Check Celery worker logs
celery -A celery_app inspect active

# Restart worker
celery -A celery_app worker --loglevel=info
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

Copyright © 2024 NEXUS Platform. All rights reserved.

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/nexus-platform/issues
- Documentation: https://docs.nexus-platform.com
- Email: support@nexus-platform.com

## Changelog

### Version 1.0.0 (2024-01-15)
- Initial release
- Visual calendar with drag-drop
- AI-powered content generation
- Multi-channel publishing
- Team collaboration features
- Analytics and reporting
- Comprehensive API
