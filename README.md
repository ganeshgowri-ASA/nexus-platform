# NEXUS Platform

**Unified AI-powered productivity platform with 24 integrated modules**

NEXUS is a comprehensive enterprise platform featuring Word processing, Excel, PowerPoint, Projects, Email, Chat, Flowcharts, Analytics, Meetings, **Image Recognition**, and **Testing & QA** modules. Built with cutting-edge technologies including Streamlit, FastAPI, and Claude AI.

## 🚀 New Modules

### 🔍 Image Recognition Module
Advanced computer vision capabilities powered by Google Vision API and AWS Rekognition:
- **Object Detection**: Detect and classify objects with bounding boxes
- **Image Classification**: Categorize images with confidence scores
- **Face Detection**: Analyze faces with age, gender, emotion detection
- **Scene Recognition**: Identify environments and scenes
- **Custom Model Training**: Train and deploy custom vision models
- **Async Processing**: Celery-based task queue for scalability
- **Dual Provider Support**: Choose between Google Vision and AWS Rekognition

**Tech Stack**: FastAPI, PostgreSQL, Redis, Celery, Google Vision API, AWS Rekognition, Streamlit

📖 [Full Documentation](./modules/image_recognition/README.md)

### 🧪 Testing & QA Module
Production-ready automated testing and quality assurance platform:
- **Multiple Test Types**: Unit, Integration, E2E, Performance, Security tests
- **Test Management**: Suites, cases, runs, and execution tracking
- **E2E Testing**: Selenium WebDriver integration for browser testing
- **Performance Testing**: Load testing with detailed metrics
- **Security Scanning**: OWASP Top 10 vulnerability checks
- **CI/CD Integration**: GitHub Actions workflows included
- **Coverage Reporting**: Comprehensive code coverage analysis
- **Defect Tracking**: Built-in bug tracking and management

**Tech Stack**: FastAPI, PostgreSQL, Redis, pytest, Selenium, GitHub Actions, Streamlit

📖 [Full Documentation](./modules/testing/README.md)

## 📋 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 14+
- Redis 7+
- Docker & Docker Compose (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/nexus-platform.git
cd nexus-platform

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# Start with Docker (recommended)
docker-compose up -d
```

### Access the Services

| Service | URL | Description |
|---------|-----|-------------|
| Image Recognition API | http://localhost:8001 | REST API for image analysis |
| Image Recognition UI | http://localhost:8501 | Interactive dashboard |
| Testing & QA API | http://localhost:8002 | REST API for test management |
| Testing & QA UI | http://localhost:8502 | Test management dashboard |
| Celery Flower | http://localhost:5555 | Task queue monitoring |
| API Documentation | http://localhost:8001/docs | Swagger/OpenAPI docs |

## 🏗️ Architecture

```
nexus-platform/
├── modules/
│   ├── image_recognition/       # Computer vision module
│   │   ├── api/                 # FastAPI endpoints
│   │   ├── models/              # Database models
│   │   ├── services/            # Vision services & Celery tasks
│   │   ├── ui/                  # Streamlit interface
│   │   └── tests/               # Test suite
│   │
│   └── testing/                 # Testing & QA module
│       ├── api/                 # FastAPI endpoints
│       ├── models/              # Database models
│       ├── services/            # Test execution services
│       ├── ui/                  # Streamlit interface
│       └── tests/               # Test suite
│
├── docker/                      # Docker configurations
├── .github/workflows/           # CI/CD pipelines
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Docker orchestration
└── README.md                    # This file
```

## 🛠️ Development

### Running Individual Services

**Image Recognition API**:
```bash
uvicorn modules.image_recognition.api.main:app --reload --port 8001
```

**Testing API**:
```bash
uvicorn modules.testing.api.main:app --reload --port 8002
```

**Celery Worker**:
```bash
celery -A modules.image_recognition.services.celery_tasks worker --loglevel=info
```

**Streamlit UIs**:
```bash
# Image Recognition UI
streamlit run modules/image_recognition/ui/streamlit_app.py --server.port 8501

# Testing UI
streamlit run modules/testing/ui/streamlit_app.py --server.port 8502
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific module tests
pytest modules/image_recognition/tests -v
pytest modules/testing/tests -v

# With coverage
pytest --cov=modules --cov-report=html
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=postgresql://nexus_user:nexus_pass@localhost:5432/nexus_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Google Cloud Vision
GOOGLE_VISION_API_KEY=your_key_here
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# AWS Rekognition
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_REGION=us-east-1

# AI/LLM APIs
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

## 📊 Features Overview

### Image Recognition
✅ Multi-provider support (Google Vision, AWS Rekognition)
✅ Async task processing with Celery
✅ Custom model training capabilities
✅ Real-time analytics dashboard
✅ Batch processing support
✅ Comprehensive API documentation

### Testing & QA
✅ 6 test types (Unit, Integration, E2E, Performance, Security, Regression)
✅ Selenium-based E2E testing
✅ Performance benchmarking
✅ OWASP security scanning
✅ CI/CD pipeline integration
✅ Coverage reporting
✅ Defect tracking system

## 🚀 Deployment

### Docker Production Deployment

```bash
# Build production images
docker-compose build

# Deploy
docker-compose up -d

# Scale services
docker-compose up -d --scale image-recognition-api=3
```

## 📈 Monitoring & Logging

- **API Monitoring**: Built-in health checks at `/health`
- **Task Queue**: Flower dashboard at http://localhost:5555
- **Logs**: Structured logging with Python's logging module

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- UI powered by [Streamlit](https://streamlit.io/)
- Computer vision by [Google Cloud Vision](https://cloud.google.com/vision) & [AWS Rekognition](https://aws.amazon.com/rekognition/)
- Testing framework: [pytest](https://pytest.org/)
- E2E testing: [Selenium](https://www.selenium.dev/)

---

**Built with ❤️ by the NEXUS Team**
