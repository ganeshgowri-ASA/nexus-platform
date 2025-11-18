# NEXUS Platform

**NEXUS: Unified AI-powered productivity platform with integrated modules for Image Recognition and Testing & QA**

## Overview

NEXUS is a comprehensive, modular platform designed to provide enterprise-grade AI and automation capabilities. This repository contains two powerful modules:

1. **Image Recognition Module**: Advanced computer vision with object detection, classification, face detection, and scene recognition
2. **Testing & QA Module**: Comprehensive automated testing framework with CI/CD integration

## 🚀 Features

### Image Recognition Module
- ✅ **Object Detection**: Identify and locate objects in images
- ✅ **Image Classification**: Categorize images with AI-powered labels
- ✅ **Face Detection**: Detect faces and analyze facial attributes
- ✅ **Scene Recognition**: Recognize scenes, landmarks, and contexts
- ✅ **Multi-Provider Support**: Google Vision API & AWS Rekognition
- ✅ **Custom Models**: Train and deploy custom computer vision models
- ✅ **Async Processing**: Celery-based task queue for batch processing
- ✅ **RESTful API**: FastAPI backend with comprehensive endpoints
- ✅ **Web UI**: User-friendly Streamlit interface

### Testing & QA Module
- ✅ **Unit/Integration/E2E Testing**: Comprehensive test execution with pytest & Selenium
- ✅ **Test Management**: Create and manage test cases and suites
- ✅ **Test Reporting**: Detailed reports with coverage analysis
- ✅ **Defect Tracking**: Built-in bug tracking system
- ✅ **CI/CD Integration**: GitHub Actions workflows included
- ✅ **Performance Testing**: Load testing and performance metrics
- ✅ **Security Testing**: Automated security scanning
- ✅ **RESTful API**: FastAPI backend
- ✅ **Web UI**: Streamlit dashboard for test management

## 📦 Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/your-org/nexus-platform.git
cd nexus-platform

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys and configuration

# Start all services
docker-compose up -d

# Access the services:
# - Image Recognition API: http://localhost:8000
# - Testing API: http://localhost:8001
# - Image Recognition UI: http://localhost:8501
# - Testing UI: http://localhost:8502
# - Celery Flower: http://localhost:5555
```

### Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Initialize databases
python -c "from modules.image_recognition.models.db_connection import init_db; init_db()"
python -c "from modules.testing.models.db_connection import init_db; init_db()"

# Start Redis
redis-server

# Start Celery worker (for image recognition)
celery -A modules.image_recognition.tasks.celery_tasks worker --loglevel=info

# Start API servers
uvicorn modules.image_recognition.api.main:app --reload --port 8000 &
uvicorn modules.testing.api.main:app --reload --port 8001 &

# Start Streamlit UIs
streamlit run modules/image_recognition/ui/streamlit_app.py --server.port 8501 &
streamlit run modules/testing/ui/streamlit_app.py --server.port 8502 &
```

## 🏗️ Architecture

```
nexus-platform/
├── modules/
│   ├── image_recognition/       # Image Recognition Module
│   │   ├── api/                 # FastAPI application
│   │   ├── models/              # Database models & schemas
│   │   ├── services/            # Business logic & AI integrations
│   │   ├── tasks/               # Celery async tasks
│   │   ├── ui/                  # Streamlit UI
│   │   └── README.md            # Module documentation
│   │
│   └── testing/                 # Testing & QA Module
│       ├── api/                 # FastAPI application
│       ├── models/              # Database models & schemas
│       ├── services/            # Test execution & caching
│       ├── runners/             # Pytest & Selenium runners
│       ├── ui/                  # Streamlit UI
│       ├── pipelines/           # CI/CD configurations
│       └── README.md            # Module documentation
│
├── .github/
│   └── workflows/               # GitHub Actions CI/CD
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Docker services
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## 📚 Documentation

### Module Documentation
- [Image Recognition Module](modules/image_recognition/README.md)
- [Testing & QA Module](modules/testing/README.md)

### API Documentation
- Image Recognition API: http://localhost:8000/docs
- Testing API: http://localhost:8001/docs

## 🎯 Usage Examples

### Image Recognition

```python
import requests

# Analyze an image
files = {'file': open('image.jpg', 'rb')}
response = requests.post(
    'http://localhost:8000/analyze/upload',
    files=files,
    params={'analysis_type': 'object_detection', 'provider': 'google_vision'}
)

results = response.json()
print(f"Detected {len(results['objects'])} objects")
```

### Testing & QA

```python
import requests

# Create a test case
test_case = {
    "name": "User Login Test",
    "test_type": "e2e",
    "priority": "high",
    "is_automated": True
}
response = requests.post('http://localhost:8001/test-cases', json=test_case)

# Run test suite
test_run = {
    "test_suite_id": 1,
    "environment": "staging",
    "triggered_by": "manual"
}
response = requests.post('http://localhost:8001/test-runs', json=test_run)
```

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nexus_platform

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Image Recognition APIs
GOOGLE_VISION_API_KEY=your_google_api_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 🚦 CI/CD

The platform includes comprehensive GitHub Actions workflows:

- **Automated Testing**: Run on every push/PR
- **Code Quality**: Black, isort, Flake8, mypy
- **Security Scanning**: Bandit, Safety
- **Coverage Reports**: Codecov integration
- **Documentation**: Auto-build and deploy
- **Scheduled Runs**: Daily regression tests

See `.github/workflows/testing-ci.yml` for details.

## 📊 Monitoring

### Celery Flower
Monitor async tasks at http://localhost:5555

### API Metrics
- Image Recognition Analytics: `GET /analytics`
- Testing Analytics: `GET /analytics`

### Logs
```bash
# API logs
docker logs nexus_image_api
docker logs nexus_testing_api

# Worker logs
docker logs nexus_celery_worker
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=modules --cov-report=html

# Run specific module tests
pytest modules/image_recognition/tests/
pytest modules/testing/tests/

# Run with markers
pytest -m unit
pytest -m integration
pytest -m e2e
```

## 🔒 Security

- API keys stored in environment variables
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy
- CORS configuration for production
- Security scanning with Bandit
- Dependency vulnerability checks with Safety

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new features
4. Ensure all tests pass (`pytest`)
5. Format code (`black modules/ && isort modules/`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📈 Performance

- **Async Processing**: Non-blocking operations with Celery
- **Caching**: Redis for frequently accessed data
- **Connection Pooling**: Optimized database connections
- **Batch Processing**: Handle multiple images/tests efficiently
- **Parallel Execution**: Pytest-xdist for parallel test runs

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check PostgreSQL
   docker ps | grep postgres
   psql -U postgres -d nexus_platform
   ```

2. **Redis Connection Error**
   ```bash
   # Check Redis
   docker ps | grep redis
   redis-cli ping
   ```

3. **API Not Starting**
   ```bash
   # Check logs
   docker logs nexus_image_api
   # Restart
   docker-compose restart nexus_image_api
   ```

4. **Celery Worker Issues**
   ```bash
   # Check worker
   celery -A modules.image_recognition.tasks.celery_tasks inspect active
   # Restart
   docker-compose restart celery_worker
   ```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- FastAPI for the excellent API framework
- Streamlit for the intuitive UI framework
- Google Cloud Vision & AWS Rekognition for AI services
- pytest & Selenium for testing frameworks
- The open-source community

## 📞 Support

- **GitHub Issues**: [Report bugs](https://github.com/your-org/nexus-platform/issues)
- **Documentation**: [Full docs](https://docs.nexus-platform.com)
- **Email**: support@nexus-platform.com

## 🗺️ Roadmap

### Upcoming Features
- [ ] Additional AI providers (Azure Vision, OpenAI Vision)
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Mobile testing support (Appium)
- [ ] Kubernetes deployment
- [ ] GraphQL API
- [ ] Real-time test execution streaming
- [ ] AI-powered test generation

## 📊 Project Stats

- **Languages**: Python
- **Frameworks**: FastAPI, Streamlit, SQLAlchemy
- **AI Services**: Google Vision, AWS Rekognition
- **Testing**: pytest, Selenium, Celery
- **Database**: PostgreSQL
- **Cache**: Redis
- **CI/CD**: GitHub Actions

---

**Built with ❤️ by the NEXUS Team**

For more information, visit [nexus-platform.com](https://nexus-platform.com)
