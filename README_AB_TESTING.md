# NEXUS A/B Testing Module

Production-ready A/B testing module for the NEXUS platform with comprehensive experiment management, statistical analysis, and real-time analytics.

## Features

### Core Capabilities
- ✅ **Experiment Management**: Create, start, pause, and complete A/B tests
- ✅ **Variant Management**: Configure multiple variants with traffic allocation
- ✅ **Traffic Allocation**: Deterministic hash-based assignment with consistent user experience
- ✅ **Statistical Analysis**: Z-tests, T-tests, Bayesian analysis, sequential testing
- ✅ **Winner Detection**: Automatic winner selection based on statistical significance
- ✅ **Multivariate Testing**: Test multiple variables simultaneously
- ✅ **Segment Targeting**: Target specific user segments with custom conditions
- ✅ **Metrics Tracking**: Track conversions, revenue, engagement, and custom metrics
- ✅ **Real-time Analytics**: Live dashboards with up-to-date results
- ✅ **Redis Caching**: High-performance caching for real-time operations

### Statistical Features
- **Sample Size Calculator**: Determine required sample size before starting
- **Confidence Intervals**: Calculate confidence intervals for effect sizes
- **P-value Calculation**: Statistical significance testing
- **Effect Size Measurement**: Cohen's d and h for practical significance
- **Power Analysis**: Ensure experiments have sufficient statistical power
- **Bayesian Probability**: Calculate probability each variant will win

### User Interface
- **Streamlit Dashboard**: Beautiful, interactive web interface
- **Visual Experiment Builder**: Create experiments without code
- **Real-time Results**: Live updating charts and statistics
- **Sample Size Calculator**: Built-in tools for experiment planning

## Architecture

```
modules/ab_testing/
├── api/                    # FastAPI endpoints
│   ├── experiments.py      # Experiment CRUD operations
│   ├── variants.py         # Variant management
│   ├── metrics.py          # Metrics tracking
│   └── main.py            # FastAPI application
├── core/                   # Core business logic
│   ├── statistics.py       # Statistical analysis engine
│   ├── cache.py           # Redis caching
│   ├── logging.py         # Logging configuration
│   └── monitoring.py      # Prometheus metrics
├── models/                 # SQLAlchemy database models
│   ├── base.py            # Base model and session
│   ├── experiment.py      # Experiment model
│   ├── variant.py         # Variant model
│   ├── metric.py          # Metric models
│   ├── participant.py     # Participant models
│   └── segment.py         # Segment models
├── schemas/                # Pydantic schemas for validation
│   ├── experiment.py      # Experiment schemas
│   ├── variant.py         # Variant schemas
│   ├── metric.py          # Metric schemas
│   └── segment.py         # Segment schemas
├── services/               # Business logic services
│   ├── experiment.py      # Experiment service
│   ├── allocation.py      # Traffic allocation
│   └── metrics.py         # Metrics service
├── ui/                     # Streamlit interface
│   └── app.py             # Dashboard application
├── config.py              # Configuration management
└── __init__.py
```

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Redis 6+

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/nexus-platform/nexus-platform.git
cd nexus-platform
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database and Redis credentials
```

4. **Run database migrations**
```bash
alembic upgrade head
```

5. **Start the API server**
```bash
python -m modules.ab_testing.api.main
```

6. **Launch the UI (in a separate terminal)**
```bash
streamlit run modules/ab_testing/ui/app.py
```

## Quick Start

### 1. Create an Experiment

```python
import httpx

# Create experiment
response = httpx.post("http://localhost:8000/api/v1/experiments/", json={
    "name": "Homepage CTA Button Test",
    "description": "Testing different CTA button colors",
    "hypothesis": "Red button will increase conversions by 10%",
    "type": "ab",
    "target_sample_size": 1000,
    "confidence_level": 0.95,
    "traffic_allocation": 1.0,
    "auto_winner_enabled": True
})

experiment = response.json()
experiment_id = experiment["id"]
```

### 2. Add Variants

```python
# Create control variant
httpx.post("http://localhost:8000/api/v1/variants/", json={
    "experiment_id": experiment_id,
    "name": "Control",
    "description": "Original blue button",
    "is_control": True,
    "traffic_weight": 1.0,
    "config": {"button_color": "blue"}
})

# Create treatment variant
httpx.post("http://localhost:8000/api/v1/variants/", json={
    "experiment_id": experiment_id,
    "name": "Treatment",
    "description": "New red button",
    "is_control": False,
    "traffic_weight": 1.0,
    "config": {"button_color": "red"}
})
```

### 3. Add Metrics

```python
# Create primary metric
response = httpx.post("http://localhost:8000/api/v1/metrics/", json={
    "experiment_id": experiment_id,
    "name": "Conversion Rate",
    "type": "conversion",
    "is_primary": True
})

metric_id = response.json()["id"]
```

### 4. Start Experiment

```python
httpx.post(f"http://localhost:8000/api/v1/experiments/{experiment_id}/start")
```

### 5. Assign Participants

```python
# Assign a user to a variant
response = httpx.post(
    f"http://localhost:8000/api/v1/experiments/{experiment_id}/assign",
    params={"participant_id": "user_123"},
    json={"properties": {"country": "US", "age": 25}}
)

assignment = response.json()
variant_id = assignment["variant_id"]
variant_name = assignment["variant_name"]
```

### 6. Track Events

```python
# Track a conversion
httpx.post("http://localhost:8000/api/v1/metrics/events", json={
    "metric_id": metric_id,
    "participant_id": "user_123",
    "variant_id": variant_id,
    "value": 1.0  # 1 for conversion
})
```

### 7. View Results

```python
# Get experiment statistics
response = httpx.get(f"http://localhost:8000/api/v1/experiments/{experiment_id}/stats")
stats = response.json()

print(f"Total Participants: {stats['total_participants']}")
print(f"Statistical Significance: {stats['statistical_significance']}")
print(f"Recommended Action: {stats['recommended_action']}")
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Statistical Methods

### Z-Test (Proportions)
Used for comparing conversion rates between two variants:
- **When to use**: Binary outcomes (converted/not converted)
- **Requirements**: Sample size > 30 per variant
- **Output**: P-value, confidence interval, effect size

### T-Test (Continuous Values)
Used for comparing continuous metrics like revenue:
- **When to use**: Continuous outcomes (revenue, time on site)
- **Requirements**: Approximately normal distribution
- **Output**: P-value, confidence interval, Cohen's d

### Bayesian Analysis
Provides probability-based conclusions:
- **Output**: Probability each variant will win
- **Advantage**: Easier to interpret than p-values
- **Use case**: Early decision making

### Sequential Testing (SPRT)
Allows for early stopping:
- **Advantage**: Reduce experiment duration
- **Trade-off**: Slightly higher false positive rate
- **Decision**: Continue, declare winner A, or declare winner B

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/nexus_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# A/B Testing
AB_TEST_DEFAULT_CONFIDENCE_LEVEL=0.95
AB_TEST_MIN_SAMPLE_SIZE=100
AB_TEST_AUTO_WINNER_ENABLED=true
AB_TEST_AUTO_WINNER_THRESHOLD=0.95

# Logging
LOG_LEVEL=INFO
ENVIRONMENT=production
```

## Testing

### Run Unit Tests
```bash
pytest tests/unit/ -v
```

### Run Integration Tests
```bash
pytest tests/integration/ -v
```

### Run All Tests with Coverage
```bash
pytest --cov=modules/ab_testing --cov-report=html
```

## Monitoring

### Prometheus Metrics
Access metrics at: http://localhost:8000/metrics

Available metrics:
- `ab_test_experiments_created_total`
- `ab_test_experiments_started_total`
- `ab_test_experiments_completed_total`
- `ab_test_variant_assignments_total`
- `ab_test_metric_events_total`
- `ab_test_api_request_duration_seconds`
- `ab_test_statistical_test_duration_seconds`

### Logs
- **Console**: Real-time logs in development
- **Files**: Rotated log files in production
  - `logs/ab_testing.log`: General logs
  - `logs/errors.log`: Error logs only

## Best Practices

### 1. Sample Size Planning
Always calculate required sample size before starting:
```python
from modules.ab_testing.core.statistics import StatisticalAnalyzer

analyzer = StatisticalAnalyzer()
result = analyzer.calculate_sample_size(
    baseline_conversion_rate=0.1,  # 10% current conversion
    minimum_detectable_effect=0.2,  # Want to detect 20% improvement
    power=0.8,
    significance_level=0.05
)

print(f"Required sample size: {result.required_sample_size} per variant")
```

### 2. Avoid Peeking
- Don't make decisions before reaching minimum sample size
- Use sequential testing if you need to check early
- Set a predetermined stopping rule

### 3. Single Primary Metric
- Define one primary metric before starting
- Secondary metrics are OK but don't use for decisions
- Avoid multiple comparison problems

### 4. Traffic Allocation
- Start with 50/50 split for maximum power
- Use traffic allocation < 1.0 for gradual rollout
- Consider multi-armed bandit for ongoing optimization

### 5. Segment Analysis
- Pre-define segments before experiment
- Avoid post-hoc segmentation (leads to false positives)
- Use segments for targeted rollouts, not decisions

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
pg_isready

# Test connection
psql -h localhost -U nexus -d nexus_db
```

### Redis Connection Issues
```bash
# Check Redis is running
redis-cli ping

# Should return: PONG
```

### Migration Issues
```bash
# Reset migrations (WARNING: destroys data)
alembic downgrade base
alembic upgrade head
```

## Performance

### Caching Strategy
- Variant assignments cached for 24 hours
- Experiment configurations cached for 1 hour
- Real-time stats cached for 5 minutes

### Database Optimization
- Indexed on frequently queried columns
- Batch inserts for metric events
- Connection pooling configured

### Expected Throughput
- **Variant assignments**: 10,000+ req/sec (with Redis)
- **Metric tracking**: 5,000+ req/sec
- **Statistics calculation**: < 100ms for most experiments

## License

MIT License - see LICENSE file for details

## Support

- **Documentation**: https://docs.nexus.com/ab-testing
- **Issues**: https://github.com/nexus-platform/nexus-platform/issues
- **Discord**: https://discord.gg/nexus
- **Email**: support@nexus.com

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.

## Roadmap

- [ ] Machine learning-based automatic traffic allocation
- [ ] Multi-armed bandit algorithms
- [ ] Advanced segmentation with ML predictions
- [ ] Integration with data warehouses (Snowflake, BigQuery)
- [ ] Mobile SDK for native apps
- [ ] Advanced visualization options
- [ ] Experiment scheduling and automation
- [ ] A/A test detection
- [ ] Sample ratio mismatch detection

## Credits

Built with ❤️ by the NEXUS team using:
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- Streamlit
- SciPy
- NumPy
- Plotly
