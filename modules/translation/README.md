# NEXUS Translation Module

Comprehensive translation service with support for 100+ languages, multiple translation providers, quality scoring, glossary management, and batch processing.

## Features

- **Text Translation**: Translate text between 100+ languages
- **Document Translation**: Support for multiple document formats (PDF, DOCX, TXT, CSV, etc.)
- **Real-time Translation**: Fast, synchronous translation API
- **Language Detection**: Automatic language detection with confidence scores
- **Glossary Support**: Create and manage custom glossaries for consistent terminology
- **Batch Translation**: Process multiple translations asynchronously with Celery
- **Quality Scoring**: Automated quality assessment for translations
- **Multiple Providers**: Support for Google Cloud Translation and DeepL
- **Streamlit UI**: User-friendly web interface
- **RESTful API**: Comprehensive FastAPI-based REST API

## Architecture

```
modules/translation/
├── api/                    # FastAPI routes and dependencies
├── models/                 # Database models and schemas
├── services/               # Core business logic
│   ├── providers/         # Translation provider implementations
│   ├── translation_service.py
│   ├── language_detection.py
│   ├── glossary_service.py
│   └── quality_scoring.py
├── tasks/                  # Celery tasks for batch processing
├── ui/                     # Streamlit user interface
├── tests/                  # Unit and integration tests
├── config.py              # Configuration management
├── constants.py           # Constants and supported languages
├── utils.py               # Utility functions
└── main.py                # FastAPI application entry point
```

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis (for Celery)
- Google Cloud Translation API key or DeepL API key

### Setup

1. **Install dependencies**:
   ```bash
   cd modules/translation
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Initialize database**:
   ```bash
   python -c "from modules.translation.models.database import init_db; init_db()"
   ```

## Usage

### Starting the API Server

```bash
# Start FastAPI server
python -m modules.translation.main

# Or with uvicorn
uvicorn modules.translation.main:app --host 0.0.0.0 --port 8000 --reload
```

### Starting the Streamlit UI

```bash
streamlit run modules/translation/ui/streamlit_app.py
```

### Starting Celery Worker

```bash
celery -A modules.translation.tasks.celery_tasks worker --loglevel=info
```

## API Endpoints

### Translation

- `POST /api/translation/translate` - Translate text
- `POST /api/translation/translate/batch` - Submit batch translation job
- `GET /api/translation/jobs/{job_id}` - Get job status
- `POST /api/translation/translate/document` - Translate document

### Language Detection

- `POST /api/translation/detect-language` - Detect language
- `GET /api/translation/languages` - List supported languages

### Glossary Management

- `POST /api/translation/glossaries` - Create glossary
- `GET /api/translation/glossaries` - List glossaries
- `GET /api/translation/glossaries/{id}` - Get glossary
- `PUT /api/translation/glossaries/{id}` - Update glossary
- `DELETE /api/translation/glossaries/{id}` - Delete glossary
- `POST /api/translation/glossaries/{id}/terms` - Add term
- `DELETE /api/translation/glossaries/terms/{id}` - Delete term

### Quality & Statistics

- `POST /api/translation/quality-score` - Calculate quality score
- `GET /api/translation/stats` - Get translation statistics
- `GET /api/translation/history` - Get translation history

## API Examples

### Text Translation

```bash
curl -X POST "http://localhost:8000/api/translation/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, world!",
    "source_language": "en",
    "target_language": "es",
    "provider": "google",
    "enable_quality_scoring": true
  }'
```

Response:
```json
{
  "id": 1,
  "source_text": "Hello, world!",
  "translated_text": "¡Hola, mundo!",
  "source_language": "en",
  "target_language": "es",
  "provider": "google",
  "quality_score": 0.95,
  "character_count": 13,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Language Detection

```bash
curl -X POST "http://localhost:8000/api/translation/detect-language" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Bonjour le monde"
  }'
```

Response:
```json
{
  "detected_language": "fr",
  "language_name": "French",
  "confidence": 0.99,
  "alternative_languages": [
    {
      "language": "en",
      "language_name": "English",
      "confidence": 0.01
    }
  ]
}
```

### Batch Translation

```bash
curl -X POST "http://localhost:8000/api/translation/translate/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Hello", "Goodbye", "Thank you"],
    "source_language": "en",
    "target_language": "fr",
    "provider": "google"
  }'
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "total_items": 3,
  "message": "Batch translation job submitted successfully"
}
```

### Create Glossary

```bash
curl -X POST "http://localhost:8000/api/translation/glossaries" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Technical Terms",
    "description": "Technical terminology glossary",
    "source_language": "en",
    "target_language": "es",
    "terms": [
      {
        "source_term": "API",
        "target_term": "API",
        "description": "Application Programming Interface"
      },
      {
        "source_term": "database",
        "target_term": "base de datos",
        "description": "Data storage system"
      }
    ]
  }'
```

## Configuration

Key configuration options in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `TRANSLATION_DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/nexus_translation` |
| `GOOGLE_TRANSLATE_API_KEY` | Google Cloud Translation API key | - |
| `DEEPL_API_KEY` | DeepL API key | - |
| `DEFAULT_TRANSLATION_PROVIDER` | Default provider (google/deepl) | `google` |
| `CELERY_BROKER_URL` | Redis URL for Celery | `redis://localhost:6379/0` |
| `TRANSLATION_API_PORT` | API server port | `8000` |
| `TRANSLATION_UI_PORT` | Streamlit UI port | `8501` |
| `ENABLE_QUALITY_SCORING` | Enable quality scoring | `true` |

## Supported Languages

The module supports 100+ languages including:

- Arabic (ar)
- Chinese - Simplified (zh-CN)
- Chinese - Traditional (zh-TW)
- English (en)
- French (fr)
- German (de)
- Hindi (hi)
- Italian (it)
- Japanese (ja)
- Korean (ko)
- Portuguese (pt)
- Russian (ru)
- Spanish (es)
- And 90+ more...

See `constants.py` for the complete list.

## Quality Scoring

The quality scoring system evaluates translations based on multiple factors:

1. **Length Ratio**: Comparison of source and target text lengths
2. **Character Diversity**: Variety of characters used
3. **Punctuation Preservation**: Retention of punctuation marks
4. **Formatting Preservation**: Preservation of newlines and formatting
5. **Number Preservation**: Retention of numeric values
6. **Repetition Score**: Detection of excessive word repetition
7. **Special Characters**: Preservation of special characters

Scores range from 0.0 to 1.0:
- **0.9+**: Excellent
- **0.75-0.9**: Good
- **0.6-0.75**: Acceptable
- **<0.6**: Poor

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest modules/translation/tests/

# Run with coverage
pytest --cov=modules.translation modules/translation/tests/

# Run specific test file
pytest modules/translation/tests/test_translation_service.py
```

## Development

### Code Style

The project uses:
- Black for code formatting
- Flake8 for linting
- MyPy for type checking

```bash
# Format code
black modules/translation/

# Lint code
flake8 modules/translation/

# Type check
mypy modules/translation/
```

### Database Migrations

Using Alembic for database migrations:

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Troubleshooting

### Common Issues

1. **Database connection errors**:
   - Ensure PostgreSQL is running
   - Check database credentials in `.env`
   - Verify database exists

2. **Translation API errors**:
   - Verify API keys are correct
   - Check API quotas and limits
   - Ensure internet connectivity

3. **Celery tasks not processing**:
   - Ensure Redis is running
   - Check Celery worker is started
   - Verify broker URL in `.env`

## License

Part of the NEXUS Platform - All rights reserved

## Support

For issues and questions:
- Create an issue in the repository
- Contact the NEXUS team
- Check the documentation

## Roadmap

Future enhancements:
- [ ] Neural machine translation support
- [ ] Custom model training
- [ ] Real-time streaming translation
- [ ] Audio/video translation
- [ ] Translation memory
- [ ] CAT tool integration
- [ ] Multi-provider comparison
- [ ] Advanced caching strategies
- [ ] Webhook notifications
- [ ] GraphQL API
