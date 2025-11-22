# NEXUS Translation Module - Quick Start Guide

Get up and running with the NEXUS Translation Module in 5 minutes!

## Prerequisites

- Python 3.8+
- PostgreSQL (or use Docker)
- Redis (or use Docker)
- API keys for Google Cloud Translation or DeepL

## Option 1: Docker (Recommended)

The easiest way to get started is using Docker:

```bash
# 1. Navigate to the translation module
cd modules/translation

# 2. Copy environment file
cp .env.example .env

# 3. Edit .env and add your API keys
nano .env  # or your preferred editor

# 4. Start all services
docker-compose up -d

# 5. Initialize database
docker-compose exec api python -c "from modules.translation.models.database import init_db; init_db()"
```

That's it! The services are now running:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Streamlit UI: http://localhost:8501

## Option 2: Local Development

If you prefer to run locally:

### Step 1: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Setup Database

```bash
# Make sure PostgreSQL is running, then create database
createdb nexus_translation

# Or using psql
psql -U postgres -c "CREATE DATABASE nexus_translation;"
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your configuration
# Required: Add your Google or DeepL API key
nano .env
```

### Step 4: Initialize Database

```bash
python -c "from modules.translation.models.database import init_db; init_db()"
```

### Step 5: Start Services

```bash
# Terminal 1: Start API server
make run-api
# Or: uvicorn modules.translation.main:app --reload

# Terminal 2: Start Celery worker (for batch translation)
make run-celery
# Or: celery -A modules.translation.tasks.celery_tasks worker --loglevel=info

# Terminal 3: Start Streamlit UI
make run-ui
# Or: streamlit run modules/translation/ui/streamlit_app.py
```

## Quick Test

### Using the API

```bash
# Test translation
curl -X POST "http://localhost:8000/api/translation/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, world!",
    "source_language": "en",
    "target_language": "es",
    "provider": "google"
  }'

# Test language detection
curl -X POST "http://localhost:8000/api/translation/detect-language" \
  -H "Content-Type: application/json" \
  -d '{"text": "Bonjour le monde"}'

# Get supported languages
curl http://localhost:8000/api/translation/languages
```

### Using the Streamlit UI

1. Open http://localhost:8501 in your browser
2. Select source and target languages
3. Enter text to translate
4. Click "Translate"

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Common Tasks

### Create a Glossary

```bash
curl -X POST "http://localhost:8000/api/translation/glossaries" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Terms",
    "description": "Technical terminology",
    "source_language": "en",
    "target_language": "es",
    "terms": [
      {
        "source_term": "API",
        "target_term": "API",
        "description": "Application Programming Interface"
      }
    ]
  }'
```

### Submit Batch Translation

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

### Check Translation Statistics

```bash
curl http://localhost:8000/api/translation/stats
```

## Configuration

Key environment variables in `.env`:

```bash
# Database
TRANSLATION_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nexus_translation

# Translation APIs (add at least one)
GOOGLE_TRANSLATE_API_KEY=your_key_here
DEEPL_API_KEY=your_key_here

# Default provider
DEFAULT_TRANSLATION_PROVIDER=google

# Celery (for batch processing)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
pg_isready

# Check database exists
psql -U postgres -c "\l" | grep nexus_translation
```

### Redis Connection Error
```bash
# Check Redis is running
redis-cli ping
# Should return: PONG
```

### API Key Issues
- Verify API keys are correct in `.env`
- Check API quotas in your Google Cloud or DeepL account
- Ensure billing is enabled for Google Cloud

### Import Errors
```bash
# Ensure you're in the correct directory
cd /path/to/nexus-platform

# Reinstall dependencies
pip install -r modules/translation/requirements.txt
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the [API documentation](http://localhost:8000/docs)
- Try the Streamlit UI at http://localhost:8501
- Check out the example scripts in `examples/`
- Review the architecture in the main README

## Getting Help

- Check the [README.md](README.md) for detailed documentation
- Review [API docs](http://localhost:8000/docs)
- Open an issue on GitHub
- Contact the NEXUS team

## What's Next?

Now that you have the translation module running, you can:

1. **Integrate with your application**: Use the REST API to add translation to your apps
2. **Create custom glossaries**: Build domain-specific terminology databases
3. **Process large batches**: Use batch translation for bulk processing
4. **Monitor quality**: Track translation quality scores
5. **Scale up**: Deploy to production with Docker or Kubernetes

Happy translating! 🌐
