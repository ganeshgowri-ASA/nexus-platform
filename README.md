# NEXUS Platform - Lead Generation & Advertising Manager

NEXUS is a unified AI-powered productivity platform with comprehensive Lead Generation and Advertising Manager modules.

## 🎯 Features

### Lead Generation Module
- **Lead Capture**: Forms, landing pages, popups, chatbots, and lead magnets
- **Form Builder**: Drag-and-drop builder with conditional logic and multi-step forms
- **Landing Pages**: Template library, A/B testing, mobile responsive
- **Validation**: Email/phone validation, duplicate detection
- **Enrichment**: Third-party API integration (Clearbit, Hunter, ZoomInfo)
- **Scoring**: Behavioral, demographic, firmographic, and predictive scoring
- **Qualification**: BANT, CHAMP, MEDDIC frameworks
- **Routing**: Round-robin, territory-based, skill-based, load balancing
- **Nurturing**: Drip campaigns, progressive profiling
- **Analytics**: Conversion tracking, source attribution, ROI measurement
- **Integration**: CRM sync (Salesforce, HubSpot, Pipedrive)

### Advertising Manager Module
- **Multi-Platform**: Google Ads, Facebook, LinkedIn, Twitter, TikTok integration
- **Campaign Management**: Creation, scheduling, budgeting, optimization
- **Creative Management**: Image/video upload, dynamic ads, templates
- **Audience Targeting**: Demographics, interests, behaviors, lookalike audiences
- **Bid Management**: Manual bidding, auto-bidding, bid optimization
- **Budget Management**: Allocation, pacing, spend tracking, alerts
- **Optimization**: A/B testing, auto-pause, performance recommendations
- **Tracking**: Conversion tracking, pixel management, UTM parameters
- **Analytics**: Cross-platform reporting, ROI analysis, ROAS calculation
- **Automation**: Automated rules, smart bidding, budget optimization

## 🏗️ Architecture

```
nexus-platform/
├── api/                    # FastAPI application
├── config/                 # Configuration & settings
├── modules/
│   ├── lead_generation/   # Lead generation module
│   └── advertising/       # Advertising module
├── shared/                # Shared utilities & types
├── tests/                 # Test suite
└── celery_tasks.py        # Async task processing
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/nexus-platform.git
cd nexus-platform
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize database:
```bash
python -c "from config.database import init_db; init_db()"
```

5. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Using Docker

```bash
docker-compose up -d
```

## 📖 API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Testing

Run tests with coverage:
```bash
pytest --cov=modules --cov-report=html
```

## 📊 Streamlit UIs

### Lead Generation Dashboard
```bash
streamlit run modules/lead_generation/streamlit_ui.py
```

### Advertising Manager Dashboard
```bash
streamlit run modules/advertising/streamlit_ui.py
```

## 🔧 API Endpoints

### Lead Generation
- `POST /api/leads/` - Create lead
- `GET /api/leads/{id}` - Get lead
- `POST /api/leads/{id}/score` - Calculate score
- `POST /api/leads/{id}/qualify` - Qualify lead
- `POST /api/leads/forms/` - Create form
- `POST /api/leads/landing-pages/` - Create landing page

### Advertising
- `POST /api/advertising/campaigns/` - Create campaign
- `GET /api/advertising/campaigns/{id}` - Get campaign
- `PATCH /api/advertising/campaigns/{id}/status` - Update status
- `POST /api/advertising/creatives/` - Create creative
- `GET /api/advertising/analytics/campaign/{id}` - Get analytics

## ⚙️ Configuration

### Environment Variables

See `.env.example` for all configuration options.

Key settings:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `ANTHROPIC_API_KEY` - Claude AI API key
- `GOOGLE_ADS_*` - Google Ads API credentials
- `FACEBOOK_*` - Facebook Ads API credentials
- `CLEARBIT_API_KEY` - Lead enrichment API key

## 🤖 Background Tasks

Celery tasks for async operations:

### Lead Generation
- `enrich_pending_leads` - Daily lead enrichment
- `calculate_lead_scores` - Daily score calculation
- `send_nurture_emails` - Hourly email campaigns

### Advertising
- `sync_ad_performance` - Hourly performance sync
- `check_budget_alerts` - Hourly budget monitoring
- `optimize_campaigns` - Automated optimization

## 🔐 Security

- API key authentication
- OAuth integration for ad platforms
- Data encryption at rest
- GDPR compliance features
- Rate limiting
- Input sanitization

## 📈 Performance

- Redis caching for frequently accessed data
- Database connection pooling
- Async task processing with Celery
- Pagination for large datasets
- Query optimization with indexes

## 🛠️ Development

### Project Structure

- `modules/lead_generation/` - Lead generation module
  - `capture.py` - Lead capture logic
  - `forms.py` - Form builder
  - `scoring.py` - Lead scoring
  - `enrichment.py` - Data enrichment
  - `qualification.py` - Lead qualification
  - `analytics.py` - Analytics engine

- `modules/advertising/` - Advertising module
  - `campaigns.py` - Campaign management
  - `platforms.py` - Platform integrations
  - `targeting.py` - Audience targeting
  - `bidding.py` - Bid management
  - `optimization.py` - Campaign optimization
  - `analytics.py` - Performance analytics

### Code Style

- Full Python type hints
- Comprehensive docstrings
- PEP 8 compliant
- 80%+ test coverage

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 📧 Support

For support, email support@nexus.com or open an issue.

## 🎉 Acknowledgments

Built with:
- FastAPI
- SQLAlchemy
- Celery
- Redis
- PostgreSQL
- Streamlit
- Anthropic Claude AI
