# 🚀 NEXUS Platform

**Unified AI-Powered Productivity Platform with 24 Integrated Modules**

NEXUS is a comprehensive productivity suite featuring Word, Excel, PPT, Projects, Email, Chat, Flowcharts, Analytics, Meetings, **OCR**, **Translation**, and more. Built with FastAPI, Streamlit, and powered by Claude AI.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Modules](#modules)
  - [OCR Module](#ocr-module)
  - [Translation Module](#translation-module)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## 🌟 Overview

NEXUS Platform is a modular, scalable productivity suite designed to streamline workflows and enhance productivity through AI-powered features. This release focuses on two core modules:

### ✅ Currently Available Modules

1. **📄 OCR Module** - Optical Character Recognition
   - Extract text from images and PDFs
   - Multi-language support (100+ languages)
   - Table detection and extraction
   - Handwriting recognition
   - Layout analysis

2. **🌐 Translation Module** - Text Translation
   - Translate text to 100+ languages
   - Custom glossaries for consistent terminology
   - Batch translation
   - Quality scoring
   - Context-aware translation

---

## 🎯 Features

### OCR Module Features
- ✅ **Image & PDF OCR** - Extract text from images (PNG, JPEG, TIFF) and PDFs
- ✅ **Multiple OCR Engines** - Support for Tesseract, Google Vision, AWS Textract
- ✅ **Handwriting Recognition** - Detect and extract handwritten text
- ✅ **Table Detection** - Automatically detect and extract tables
- ✅ **Layout Analysis** - Understand document structure and layout
- ✅ **100+ Languages** - Multilingual OCR support
- ✅ **Confidence Scoring** - Quality metrics for extracted text
- ✅ **Async Processing** - Celery-based task queue for large documents

### Translation Module Features
- ✅ **Text Translation** - Translate text between 100+ languages
- ✅ **Multiple Services** - Google Translate, Anthropic Claude, DeepL
- ✅ **Language Detection** - Automatic source language detection
- ✅ **Custom Glossaries** - Maintain consistent terminology
- ✅ **Batch Translation** - Process multiple texts at once
- ✅ **Quality Scoring** - Translation quality metrics
- ✅ **Context-Aware** - Provide context for better translations
- ✅ **Real-time Translation** - Streaming translation support

---

## 🏗️ Architecture

```
nexus-platform/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── core/           # Core configuration
│   │   ├── db/             # Database setup
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── modules/        # Feature modules
│   │   │   ├── ocr/       # OCR module
│   │   │   └── translation/ # Translation module
│   │   ├── celery_tasks/  # Async tasks
│   │   └── main.py        # FastAPI app
│   ├── tests/             # Test suite
│   └── requirements.txt
├── frontend/              # Streamlit frontend
│   ├── pages/            # UI pages
│   │   ├── ocr_page.py
│   │   └── translation_page.py
│   └── app.py           # Main Streamlit app
├── docker/              # Docker configurations
├── docker-compose.yml   # Container orchestration
└── README.md

Technology Stack:
- Backend: FastAPI, SQLAlchemy, PostgreSQL, Redis
- Frontend: Streamlit
- OCR: Tesseract, Google Vision, AWS Textract
- Translation: Google Translate, Anthropic Claude, DeepL
- Task Queue: Celery, Redis
- Database: PostgreSQL
- Containerization: Docker, Docker Compose
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (recommended)
- PostgreSQL 15+ (if not using Docker)
- Redis (if not using Docker)

### Quick Start with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/nexus-platform.git
   cd nexus-platform
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend (Streamlit): http://localhost:8501
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/v1/docs

### Manual Installation

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt

   # Set up database
   export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/nexus_db"

   # Run migrations (if using Alembic)
   alembic upgrade head

   # Start backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   pip install -r requirements.txt

   # Start frontend
   streamlit run app.py
   ```

3. **Celery Worker (Optional for async processing)**
   ```bash
   cd backend
   celery -A app.celery_tasks.celery_app worker --loglevel=info
   ```

---

## 📦 Modules

### 📄 OCR Module

Extract text from images and PDFs with high accuracy.

#### Quick Example

**Using API:**
```python
import requests

# Upload and process image
files = {"file": open("document.png", "rb")}
data = {
    "engine": "tesseract",
    "detect_language": True,
    "extract_tables": True
}

response = requests.post(
    "http://localhost:8000/api/v1/ocr/extract",
    files=files,
    data=data
)

result = response.json()
print(f"Extracted text: {result['extracted_text']}")
print(f"Confidence: {result['confidence_score']}")
print(f"Tables found: {result['tables_detected']}")
```

**Using UI:**
1. Navigate to OCR page in Streamlit
2. Upload an image or PDF
3. Select OCR options
4. Click "Extract Text"
5. View and download results

#### Supported File Types
- Images: PNG, JPEG, TIFF
- Documents: PDF (single and multi-page)

#### OCR Engines
- **Tesseract** (Free, Open-source) - Good for general text
- **Google Vision** (API key required) - Better accuracy, handwriting support
- **AWS Textract** (AWS credentials required) - Best for forms and tables

---

### 🌐 Translation Module

Translate text between 100+ languages with quality scoring.

#### Quick Example

**Using API:**
```python
import requests

# Translate text
payload = {
    "text": "Hello, how are you?",
    "source_language": "en",
    "target_language": "es",
    "service": "google"
}

response = requests.post(
    "http://localhost:8000/api/v1/translation/translate",
    json=payload
)

result = response.json()
print(f"Translation: {result['translated_text']}")
print(f"Quality score: {result['quality_score']}")
```

**Using UI:**
1. Navigate to Translation page
2. Enter text to translate
3. Select source and target languages
4. Click "Translate"
5. View results and quality metrics

#### Supported Languages

100+ languages including:
- Major: English, Spanish, French, German, Italian, Portuguese, Russian
- Asian: Chinese, Japanese, Korean, Hindi, Arabic, Thai, Vietnamese
- And many more...

#### Translation Services
- **Google Translate** (Free tier available) - Fast, reliable
- **Anthropic Claude** (API key required) - Context-aware, high quality
- **DeepL** (API key required) - Professional-grade translations

#### Custom Glossaries

Create custom glossaries for consistent terminology:

```python
# Create glossary
glossary = {
    "name": "Product Terms",
    "source_language": "en",
    "target_language": "es",
    "entries": {
        "dashboard": "panel de control",
        "user profile": "perfil de usuario"
    }
}

response = requests.post(
    "http://localhost:8000/api/v1/translation/glossaries",
    json=glossary
)
```

---

## 📚 API Documentation

### Interactive Documentation

Once the backend is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

### Key Endpoints

#### OCR Endpoints
- `POST /api/v1/ocr/extract` - Extract text from image/PDF
- `GET /api/v1/ocr/documents` - List OCR documents
- `GET /api/v1/ocr/documents/{id}` - Get document details
- `DELETE /api/v1/ocr/documents/{id}` - Delete document
- `GET /api/v1/ocr/documents/{id}/tables` - Get extracted tables

#### Translation Endpoints
- `POST /api/v1/translation/translate` - Translate text
- `POST /api/v1/translation/batch` - Batch translation
- `GET /api/v1/translation/translations` - List translations
- `GET /api/v1/translation/translations/{id}` - Get translation details
- `GET /api/v1/translation/languages` - Get supported languages
- `POST /api/v1/translation/glossaries` - Create glossary
- `GET /api/v1/translation/glossaries` - List glossaries
- `PUT /api/v1/translation/glossaries/{id}` - Update glossary

---

## 🛠️ Development

### Project Structure

```
backend/app/
├── core/              # Configuration, logging, settings
├── db/                # Database session, base models
├── models/            # SQLAlchemy ORM models
├── schemas/           # Pydantic request/response schemas
├── modules/
│   ├── ocr/
│   │   ├── models.py      # OCR database models
│   │   ├── schemas.py     # OCR schemas
│   │   ├── processor.py   # OCR processing logic
│   │   ├── service.py     # OCR business logic
│   │   ├── router.py      # OCR API endpoints
│   │   └── utils.py       # OCR utilities
│   └── translation/
│       ├── models.py      # Translation models
│       ├── schemas.py     # Translation schemas
│       ├── processor.py   # Translation logic
│       ├── service.py     # Translation business logic
│       ├── router.py      # Translation API endpoints
│       └── utils.py       # Translation utilities
└── celery_tasks/      # Async task definitions
```

### Adding a New Module

1. Create module directory: `backend/app/modules/your_module/`
2. Implement models, schemas, processor, service, and router
3. Register router in `backend/app/api/v1/api.py`
4. Add Celery tasks if needed
5. Create frontend page in `frontend/pages/`
6. Add tests in `backend/tests/`

---

## 🧪 Testing

### Run All Tests

```bash
cd backend
pytest
```

### Run Specific Test Module

```bash
pytest tests/test_ocr.py
pytest tests/test_translation.py
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Test Structure

- `tests/conftest.py` - Pytest fixtures and configuration
- `tests/test_ocr.py` - OCR module tests
- `tests/test_translation.py` - Translation module tests

---

## 🚢 Deployment

### Docker Deployment (Production)

1. **Update docker-compose.yml for production**
   ```yaml
   # Use production-ready settings
   - Set DEBUG=False
   - Use strong passwords
   - Configure SSL/TLS
   - Set up volume backups
   ```

2. **Deploy**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Environment Variables

Required environment variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Redis
REDIS_URL=redis://redis:6379/0

# API Keys (optional but recommended for full features)
GOOGLE_CLOUD_API_KEY=your_key
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
ANTHROPIC_API_KEY=your_key

# Application
APP_ENV=production
DEBUG=False
SECRET_KEY=your-secret-key
```

---

## 📊 Performance

### OCR Performance
- **Tesseract**: ~2-5 seconds per page
- **Google Vision**: ~1-2 seconds per page
- **AWS Textract**: ~1-3 seconds per page

### Translation Performance
- **Google Translate**: ~0.5-1 second per request
- **Anthropic Claude**: ~1-2 seconds per request
- **Batch processing**: Parallel processing for faster results

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Write unit tests for new features
- Update documentation
- Ensure all tests pass before submitting PR

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- FastAPI for the amazing web framework
- Streamlit for rapid UI development
- Tesseract OCR for open-source OCR
- Google Cloud, AWS, and Anthropic for AI services

---

## 📞 Support

- **Documentation**: See `/docs` folder
- **Issues**: [GitHub Issues](https://github.com/yourusername/nexus-platform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/nexus-platform/discussions)

---

**Built with ❤️ using FastAPI, Streamlit, and Claude AI**
