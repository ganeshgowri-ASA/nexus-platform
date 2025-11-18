# NEXUS Platform

**NEXUS**: Unified AI-powered productivity platform with integrated **Lead Generation** and **Advertising Management** modules.

## Features

### Lead Generation Module

- **Multi-Channel Lead Capture**
  - Customizable forms (inline, popup, slide-in, embedded)
  - Landing page builder with A/B testing
  - AI-powered chatbot lead capture
  - Progressive profiling

- **Lead Management**
  - Email and phone validation
  - Lead enrichment (Clearbit, Hunter)
  - AI-powered lead scoring
  - Duplicate detection
  - Auto-routing and assignment

- **Lead Nurturing**
  - Activity tracking
  - Automated workflows
  - CRM synchronization
  - Lead magnets delivery

### Advertising Module

- **Multi-Platform Campaign Management**
  - Google Ads integration
  - Facebook Ads integration
  - LinkedIn Ads integration
  - Unified dashboard

- **Campaign Optimization**
  - Budget allocation and optimization
  - Bid management (manual, automated, target CPA/ROAS)
  - A/B testing
  - Automated rules

- **Performance Tracking**
  - Real-time metrics sync
  - Conversion tracking
  - Attribution modeling
  - ROI analysis
  - Custom reporting

- **Creative Management**
  - Creative library
  - Multi-format support (image, video, carousel)
  - Creative testing

## Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis
- **Task Queue**: Celery with Redis broker
- **AI/LLM**: Anthropic Claude, OpenAI GPT
- **UI**: Streamlit
- **Testing**: Pytest, pytest-asyncio
- **Migrations**: Alembic

## Project Structure

```
nexus-platform/
├── modules/
│   ├── lead_generation/
│   │   ├── models.py           # Database models
│   │   ├── schemas.py          # Pydantic schemas
│   │   ├── routers/            # API endpoints
│   │   └── services/           # Business logic
│   │       ├── lead_service.py
│   │       ├── form_service.py
│   │       ├── enrichment_service.py
│   │       ├── scoring_service.py
│   │       └── chatbot_service.py
│   └── advertising/
│       ├── models.py
│       ├── schemas.py
│       ├── routers/
│       └── services/
│           ├── campaign_service.py
│           └── google_ads_service.py
├── tasks/                      # Celery tasks
│   ├── lead_generation_tasks.py
│   └── advertising_tasks.py
├── ui/                         # Streamlit UI
│   ├── lead_generation_ui.py
│   └── advertising_ui.py
├── tests/                      # Test suite
├── alembic/                    # Database migrations
├── main.py                     # FastAPI app
├── streamlit_app.py           # Streamlit app
├── celery_app.py              # Celery app
├── config.py                  # Configuration
├── database.py                # Database setup
├── cache.py                   # Redis cache
└── requirements.txt           # Dependencies
```

## Quick Start

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed installation instructions.

```bash
# Clone repository
git clone https://github.com/ganeshgowri-ASA/nexus-platform.git
cd nexus-platform

# Setup environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Setup database
alembic upgrade head

# Run services
uvicorn main:app --reload                    # API
celery -A celery_app worker --loglevel=info  # Celery
streamlit run streamlit_app.py               # UI
```

## Documentation

- **Setup Guide**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **API Documentation**: http://localhost:8000/docs (when running)
- **Architecture**: See `/docs` directory

## API Endpoints

### Lead Generation
- `POST /api/lead-generation/leads/` - Create lead
- `GET /api/lead-generation/leads/` - List leads
- `POST /api/lead-generation/leads/{id}/enrich` - Enrich lead
- `POST /api/lead-generation/leads/{id}/score` - Score lead
- `POST /api/lead-generation/forms/` - Create form
- `POST /api/lead-generation/chatbot/conversations` - Start chat

### Advertising
- `POST /api/advertising/campaigns/` - Create campaign
- `GET /api/advertising/campaigns/` - List campaigns
- `POST /api/advertising/campaigns/{id}/pause` - Pause campaign
- `POST /api/advertising/campaigns/{id}/sync` - Sync metrics

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=modules --cov-report=html

# Run specific module
pytest tests/test_lead_generation.py
```

## Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## License

MIT License

## Support

- **Issues**: https://github.com/ganeshgowri-ASA/nexus-platform/issues
- **Email**: support@nexus-platform.com
