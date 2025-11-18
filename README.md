# NEXUS Platform

NEXUS: Unified AI-powered productivity platform with 24 integrated modules - Word, Excel, PPT, Projects, Email, Chat, Flowcharts, Analytics, Meetings & more. Built with Streamlit & Claude AI.

## 🧪 A/B Testing Module

This repository includes a **production-ready A/B testing module** with comprehensive features for running experiments, analyzing results, and making data-driven decisions.

### Quick Start

#### Using Docker (Recommended)
```bash
# Start all services (PostgreSQL, Redis, API, UI)
make docker-up

# Access the services
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/api/docs
# - Streamlit UI: http://localhost:8501
```

#### Manual Setup
```bash
# Install dependencies
make install

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run database migrations
make migrate

# Start API server
make run-api

# In another terminal, start UI
make run-ui
```

### Features

✅ **Experiment Management** - Create and manage A/B tests
✅ **Statistical Analysis** - Z-tests, T-tests, Bayesian analysis
✅ **Traffic Allocation** - Deterministic hash-based assignment
✅ **Winner Detection** - Automatic winner selection
✅ **Multivariate Testing** - Test multiple variables
✅ **Segment Targeting** - Target specific user groups
✅ **Real-time Analytics** - Live dashboards and metrics
✅ **Redis Caching** - High-performance caching
✅ **Streamlit UI** - Beautiful web interface
✅ **Full Type Safety** - Complete type annotations
✅ **Comprehensive Tests** - Unit and integration tests
✅ **Production Ready** - Logging, monitoring, error handling

### Documentation

- **Full Documentation**: [README_AB_TESTING.md](README_AB_TESTING.md)
- **API Documentation**: http://localhost:8000/api/docs (when running)
- **Architecture**: See `modules/ab_testing/` directory structure

### Technology Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Caching**: Redis
- **Statistics**: SciPy, NumPy, Pandas
- **Frontend**: Streamlit, Plotly
- **Testing**: Pytest
- **Deployment**: Docker, Docker Compose

### Example Usage

```python
import httpx

# Create an experiment
response = httpx.post("http://localhost:8000/api/v1/experiments/", json={
    "name": "Homepage CTA Test",
    "description": "Testing button colors",
    "hypothesis": "Red button increases conversions by 10%",
    "type": "ab",
    "confidence_level": 0.95
})

experiment_id = response.json()["id"]

# Add variants
httpx.post("http://localhost:8000/api/v1/variants/", json={
    "experiment_id": experiment_id,
    "name": "Control",
    "is_control": True,
    "config": {"button_color": "blue"}
})

# Start experiment and track results!
```

### Testing

```bash
# Run all tests with coverage
make test

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration
```

### Development

```bash
# Install development dependencies
make dev-install

# Format code
make format

# Run linters
make lint

# Clean up generated files
make clean
```

### Architecture Overview

```
nexus-platform/
├── modules/ab_testing/     # A/B testing module
│   ├── api/               # FastAPI endpoints
│   ├── core/              # Business logic
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Services layer
│   └── ui/                # Streamlit UI
├── tests/                 # Test suite
├── migrations/            # Alembic migrations
├── docker-compose.yml     # Docker configuration
└── requirements.txt       # Python dependencies
```

### Deployment

#### Docker Production Deployment
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Health Checks
- API Health: http://localhost:8000/health
- Prometheus Metrics: http://localhost:8000/metrics

### Contributing

Contributions are welcome! Please see the contributing guidelines in the full documentation.

### License

MIT License - see LICENSE file for details.

### Support

- **Issues**: https://github.com/nexus-platform/nexus-platform/issues
- **Documentation**: [README_AB_TESTING.md](README_AB_TESTING.md)
- **Email**: support@nexus.com

### Roadmap

- [x] Core A/B testing functionality
- [x] Statistical analysis engine
- [x] Real-time analytics
- [x] Streamlit UI
- [ ] Machine learning-based optimization
- [ ] Mobile SDK
- [ ] Advanced segmentation
- [ ] Data warehouse integrations

---

Built with ❤️ by the NEXUS team
