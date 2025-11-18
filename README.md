# NEXUS Platform - Marketing Automation Module

**NEXUS**: Unified AI-powered productivity platform with 24 integrated modules including Word, Excel, PPT, Projects, Email, Chat, Flowcharts, Analytics, Meetings & more. Built with Streamlit & Claude AI.

## 🚀 Marketing Automation Module

A production-ready, AI-powered marketing automation platform with comprehensive features for email campaigns, lead nurturing, behavioral triggers, and multi-channel automation.

### ✨ Key Features

#### Campaign Management
- **Visual Workflow Builder**: Drag-and-drop interface for creating automation workflows
- **Email Campaigns**: Create, schedule, and send targeted email campaigns
- **SMS Campaigns**: Multi-channel messaging support via Twilio integration
- **Drip Campaigns**: Automated nurture sequences with time-based triggers
- **A/B Testing**: Test subject lines, content, and send times

#### Lead Management
- **Contact Management**: Comprehensive contact database with custom attributes
- **Lead Scoring**: Intelligent scoring based on engagement and behavior
- **Dynamic Segmentation**: Create segments with complex conditions
- **Tag Management**: Organize contacts with flexible tagging system

#### Automation & Triggers
- **Behavioral Triggers**: Respond to user actions in real-time
- **Time-Based Triggers**: Schedule automations for specific times
- **Event-Based Triggers**: React to custom events and webhooks
- **Conditional Logic**: Branch workflows based on contact data

#### AI-Powered Features
- **Content Generation**: AI-powered email content creation with Claude
- **Personalization Engine**: Deep personalization using AI
- **Subject Line Optimization**: Generate high-converting subject lines
- **Send Time Optimization**: AI-suggested optimal send times
- **Campaign Analytics**: AI-powered insights and recommendations

#### Analytics & Reporting
- **Real-Time Metrics**: Track opens, clicks, conversions
- **Campaign Performance**: Comprehensive campaign analytics
- **Link Click Tracking**: Track individual link performance
- **Multi-Touch Attribution**: Understand customer journey
- **Revenue Tracking**: Track revenue from campaigns

### 🏗️ Architecture

```
nexus-platform/
├── config/                      # Configuration
│   ├── settings.py             # Pydantic settings
│   ├── logging_config.py       # Structured logging
│   └── constants.py            # Application constants
├── src/
│   ├── core/                   # Core utilities
│   │   ├── database.py         # Database setup
│   │   ├── llm_client.py       # Claude AI integration
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── utils.py            # Utility functions
│   ├── models/                 # Database models
│   │   ├── base.py            # User, Workspace
│   │   ├── campaign.py        # Campaign models
│   │   ├── contact.py         # Contact models
│   │   ├── automation.py      # Automation models
│   │   └── analytics.py       # Analytics models
│   ├── schemas/                # Pydantic schemas
│   │   ├── marketing/
│   │   │   ├── campaign_schema.py
│   │   │   ├── contact_schema.py
│   │   │   └── automation_schema.py
│   │   └── common.py          # Common schemas
│   ├── services/               # Business logic
│   │   └── marketing/
│   │       ├── campaign_service.py
│   │       ├── contact_service.py
│   │       ├── email_service.py
│   │       ├── automation_service.py
│   │       └── analytics_service.py
│   ├── api/                    # FastAPI routes
│   │   └── v1/marketing/
│   │       ├── campaigns.py
│   │       ├── contacts.py
│   │       └── automations.py
│   ├── tasks/                  # Celery tasks
│   │   └── marketing/
│   │       └── email_tasks.py
│   └── ui/                     # Streamlit UI
│       └── marketing/
├── tests/                      # Test suite
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── app.py                      # FastAPI application
├── main.py                     # Streamlit UI
├── celery_app.py              # Celery configuration
├── requirements.txt            # Dependencies
└── .env.example               # Environment template
```

### 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.10+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache/Queue**: Redis
- **Task Queue**: Celery + Flower
- **AI/LLM**: Anthropic Claude, OpenAI (optional)
- **Email**: SMTP, SendGrid (optional)
- **SMS**: Twilio (optional)
- **UI**: Streamlit
- **Testing**: Pytest, Pytest-asyncio
- **Code Quality**: Black, Flake8, MyPy, isort

### 📦 Installation

#### 1. Clone the repository

```bash
git clone https://github.com/ganeshgowri-ASA/nexus-platform.git
cd nexus-platform
```

#### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install dependencies

```bash
pip install -r requirements.txt
```

#### 4. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ANTHROPIC_API_KEY`: Claude AI API key
- `SMTP_*`: Email server configuration

#### 5. Initialize database

```bash
# Create database
createdb nexus_db

# Run migrations (when implemented)
alembic upgrade head

# Or initialize directly
python scripts/init_db.py
```

#### 6. Start services

**Terminal 1 - API Server:**
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Celery Worker:**
```bash
celery -A celery_app worker --loglevel=info
```

**Terminal 3 - Celery Beat (Scheduler):**
```bash
celery -A celery_app beat --loglevel=info
```

**Terminal 4 - Streamlit UI:**
```bash
streamlit run main.py
```

### 🚦 Quick Start

#### Create a Campaign

```python
import requests

# Create campaign
response = requests.post(
    "http://localhost:8000/api/v1/marketing/campaigns/",
    json={
        "name": "Summer Sale 2024",
        "type": "email",
        "subject": "Get 50% off this summer!",
        "content": "<h1>Summer Sale</h1><p>Use code SUMMER50</p>",
        "from_name": "NEXUS Team",
        "from_email": "hello@nexus.io"
    }
)

campaign = response.json()["data"]
print(f"Campaign created: {campaign['id']}")
```

#### Send Campaign

```python
# Send campaign immediately
response = requests.post(
    f"http://localhost:8000/api/v1/marketing/campaigns/{campaign_id}/send",
    json={"send_immediately": True}
)
```

#### Create Automation

```python
# Create welcome automation
response = requests.post(
    "http://localhost:8000/api/v1/marketing/automations/",
    json={
        "name": "Welcome Series",
        "trigger_type": "event",
        "trigger_config": {
            "event_type": "contact_subscribed"
        },
        "actions": [
            {
                "action_type": "send_email",
                "config": {
                    "template_id": "welcome_email"
                },
                "delay_minutes": 0
            },
            {
                "action_type": "wait",
                "config": {
                    "delay_minutes": 1440  # 24 hours
                }
            },
            {
                "action_type": "send_email",
                "config": {
                    "template_id": "onboarding_tips"
                }
            }
        ]
    }
)
```

### 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_campaign_service.py

# Run with verbose output
pytest -v
```

### 📊 API Documentation

Once the API server is running, access the interactive documentation at:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### 🎨 Streamlit UI

Access the Streamlit interface at:
- http://localhost:8501

Features:
- Dashboard with key metrics
- Campaign creation and management
- Contact management and segmentation
- Automation workflow builder
- Analytics and reporting

### 🔐 Security

- **Authentication**: JWT-based authentication (implement as needed)
- **Authorization**: Role-based access control
- **Data Encryption**: Sensitive data encrypted at rest
- **Rate Limiting**: API rate limiting enabled
- **Input Validation**: Comprehensive validation with Pydantic
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **XSS Prevention**: HTML sanitization

### 🚀 Deployment

#### Docker Deployment

```bash
# Build image
docker build -t nexus-platform .

# Run with Docker Compose
docker-compose up -d
```

#### Production Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY`
- [ ] Configure proper CORS origins
- [ ] Set up database backups
- [ ] Configure monitoring (Sentry)
- [ ] Set up SSL/TLS certificates
- [ ] Configure reverse proxy (Nginx)
- [ ] Set up log aggregation
- [ ] Configure auto-scaling
- [ ] Set up CDN for static assets

### 📈 Performance

- **Database Connection Pooling**: Optimized pool size
- **Async Operations**: Full async/await support
- **Caching**: Redis caching for frequently accessed data
- **Background Tasks**: Celery for async processing
- **Batch Processing**: Efficient bulk operations
- **Query Optimization**: Indexed queries and eager loading

### 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run tests and linting
6. Submit a pull request

### 📝 License

MIT License - see LICENSE file for details

### 🆘 Support

- **Documentation**: https://docs.nexus-platform.io
- **Issues**: https://github.com/ganeshgowri-ASA/nexus-platform/issues
- **Email**: support@nexus-platform.io

### 🗺️ Roadmap

- [ ] WhatsApp integration
- [ ] Social media scheduling
- [ ] Advanced A/B testing
- [ ] Predictive analytics
- [ ] Mobile app
- [ ] Marketplace for templates
- [ ] Third-party integrations (Salesforce, HubSpot, etc.)
- [ ] Advanced workflow builder
- [ ] WebSocket support for real-time updates
- [ ] Multi-language support

### 👥 Team

Built with ❤️ by the NEXUS Team

---

**Version**: 0.1.0
**Last Updated**: January 2025
