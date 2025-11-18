# 🔷 NEXUS Platform - Campaign Manager

**Production-Ready AI-Powered Campaign Management System**

NEXUS Platform is a comprehensive campaign management solution featuring campaign planning, budget management, multi-channel orchestration, team collaboration, timeline management, performance tracking, ROI measurement, and AI-powered insights powered by Claude AI.

## ✨ Features

### Campaign Management
- **Campaign Planning** - Create and manage marketing campaigns with detailed configuration
- **Budget Management** - Allocate and track budgets across campaigns and channels
- **Multi-Channel Orchestration** - Coordinate campaigns across email, social media, paid ads, and more
- **Asset Library** - Store and manage creative assets with approval workflows
- **Team Collaboration** - Assign roles, tasks, and permissions to team members

### Analytics & Insights
- **Performance Tracking** - Real-time campaign performance metrics
- **ROI Measurement** - Comprehensive ROI calculations and financial tracking
- **Interactive Dashboards** - Visualize campaign data with charts and graphs
- **Gantt Charts** - Timeline visualization for milestones and deliverables
- **Channel Analytics** - Compare performance across marketing channels

### AI-Powered Features (Claude AI)
- **Campaign Insights** - AI-generated analysis of campaign performance
- **Budget Optimization** - AI-driven budget allocation recommendations
- **Content Suggestions** - AI-powered campaign content ideas
- **Automated Reporting** - Scheduled reports with AI insights

### Production Features
- **FastAPI Backend** - High-performance async REST API
- **PostgreSQL Database** - Robust relational data storage
- **Redis Caching** - High-speed data caching and message broker
- **Celery Tasks** - Async background job processing
- **Streamlit UI** - Interactive web interface
- **Docker Support** - Full containerization with Docker Compose
- **Full Type Safety** - Complete type hints with Pydantic

## 🏗️ Architecture

```
nexus-platform/
├── backend/                # FastAPI backend
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Security, config, Celery
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── modules/       # Feature modules
│   │   │   └── campaign_manager/
│   │   │       ├── router.py      # API endpoints
│   │   │       ├── service.py     # Business logic
│   │   │       ├── tasks.py       # Celery tasks
│   │   │       └── ai_service.py  # Claude AI integration
│   │   └── main.py        # Application entry point
│   └── alembic/           # Database migrations
├── frontend/              # Streamlit frontend
│   ├── pages/            # Multi-page app
│   ├── utils/            # API client & utilities
│   └── app.py            # Main app
├── docker/               # Docker configuration
└── docker-compose.yml    # Docker orchestration
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional but recommended)
- Anthropic API key for AI features

### Option 1: Docker (Recommended)

1. **Clone and setup**
```bash
git clone <repository-url>
cd nexus-platform
make setup
```

2. **Configure environment**
```bash
# Edit .env with your settings
# Required: ANTHROPIC_API_KEY for AI features
```

3. **Start all services**
```bash
make docker-build
make docker-up
```

4. **Access the platform**
- Frontend UI: http://localhost:8501
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Postgres: localhost:5432
- Redis: localhost:6379

### Option 2: Local Development

See detailed setup instructions in the documentation.

## 📦 Technology Stack

### Backend
- **FastAPI** 0.109.0 - Modern async web framework
- **SQLAlchemy** 2.0.25 - SQL ORM
- **PostgreSQL** - Primary database
- **Redis** - Cache & message broker
- **Celery** 5.3.6 - Distributed task queue
- **Pydantic** - Data validation
- **Anthropic Claude** - AI integration
- **Alembic** - Database migrations
- **JWT** - Authentication

### Frontend
- **Streamlit** 1.30.0 - Interactive UI
- **Plotly** - Interactive visualizations
- **Pandas** - Data processing

## 📚 API Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Key Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user

#### Campaigns
- `GET /api/v1/campaigns/` - List campaigns
- `POST /api/v1/campaigns/` - Create campaign
- `GET /api/v1/campaigns/{id}` - Get campaign details
- `PUT /api/v1/campaigns/{id}` - Update campaign
- `DELETE /api/v1/campaigns/{id}` - Delete campaign
- `POST /api/v1/campaigns/{id}/status/{status}` - Update status

#### Channels
- `POST /api/v1/campaigns/{id}/channels` - Add channel
- `GET /api/v1/campaigns/{id}/channels` - List channels

#### Milestones
- `POST /api/v1/campaigns/{id}/milestones` - Create milestone
- `GET /api/v1/campaigns/{id}/milestones` - List milestones
- `PUT /api/v1/milestones/{id}` - Update milestone

#### Analytics
- `GET /api/v1/campaigns/{id}/analytics` - Campaign analytics
- `GET /api/v1/campaigns/dashboard/stats` - Dashboard stats

#### AI Features
- `POST /api/v1/campaigns/{id}/optimize` - AI optimization
- `POST /api/v1/campaigns/{id}/reports/generate` - Generate report

## 🗄️ Database Models

### Core Models
- **User** - Authentication and authorization
- **Campaign** - Campaign details and configuration
- **CampaignChannel** - Marketing channels
- **CampaignAsset** - Creative assets
- **TeamMember** - Team collaboration
- **Milestone** - Timeline and tasks
- **PerformanceMetric** - Time-series metrics
- **CampaignReport** - Generated reports

All models include:
- Soft delete support
- Automatic timestamps (created_at, updated_at)
- Full relationship mapping
- Validation constraints

## 🔧 Configuration

Key environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql://nexus:password@localhost:5432/nexus

# Security
SECRET_KEY=your-secret-key-here

# AI (Required for AI features)
ANTHROPIC_API_KEY=your-anthropic-api-key-here
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
```

## 📈 Usage Guide

### 1. Creating a Campaign
1. Login to the platform
2. Navigate to Campaign Manager
3. Click "Create Campaign" tab
4. Configure campaign (name, type, budget, dates, goals)
5. Submit to create

### 2. Managing Channels
1. Open campaign
2. Add marketing channels
3. Allocate budget per channel
4. Track channel performance

### 3. Timeline Management
1. Create milestones with due dates
2. Assign to team members
3. Track progress
4. View Gantt chart visualization

### 4. AI Insights
1. Open campaign analytics
2. Click "Generate Insights"
3. Review AI recommendations
4. Apply budget optimizations

## 🧪 Testing

```bash
# Run tests
make test

# With coverage
make test-coverage

# Lint code
make lint

# Format code
make format
```

## 🚀 Production Deployment

1. **Update environment**
   - Set `DEBUG=False`
   - Use strong `SECRET_KEY`
   - Configure production database
   - Set proper CORS origins

2. **Database migrations**
```bash
make db-upgrade
```

3. **Build and deploy**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

4. **Monitor services**
   - Backend health: `/health`
   - API docs: `/api/docs`
   - Celery flower (optional): Setup monitoring

## 🎯 Roadmap

- [x] Campaign CRUD operations
- [x] Budget management
- [x] Multi-channel orchestration
- [x] Team collaboration
- [x] Gantt chart timelines
- [x] Performance analytics
- [x] ROI tracking
- [x] AI insights & optimization
- [x] Automated reporting
- [ ] Email notifications
- [ ] Social media integrations
- [ ] A/B testing framework
- [ ] Mobile app

## 📝 License

MIT License

## 🆘 Support

For issues and questions:
- GitHub Issues
- API Documentation: `/api/docs`

---

**Version:** 1.0.0
**Status:** Production Ready
**Built with:** FastAPI, PostgreSQL, Redis, Celery, Streamlit, Claude AI
