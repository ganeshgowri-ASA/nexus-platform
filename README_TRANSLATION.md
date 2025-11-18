# NEXUS Translation Module

## 🌐 Production-Ready Translation System

A comprehensive, production-ready translation module for the NEXUS platform with multi-engine support, AI enhancement, and advanced features.

## ✨ Features

### Core Translation
- **Multi-Engine Support**: Google Translate, DeepL, Azure Translator, AWS Translate, OpenAI GPT-4, Claude
- **Automatic Language Detection**: Confidence scoring with multiple detection methods
- **100+ Languages**: Support for all major world languages
- **Batch Translation**: Process multiple texts simultaneously
- **Streaming Translation**: Real-time translation with progress updates

### Advanced Features
- **Translation Memory (TM)**: Reuse previous translations, TMX import/export
- **Custom Glossaries**: Industry-specific terminology, domain glossaries
- **Quality Assessment**: Automatic scoring, back-translation validation
- **Context Analysis**: Tone preservation, domain detection
- **Document Translation**: PDF, DOCX, XLSX, PPTX, HTML with formatting preservation
- **Localization**: Cultural adaptation, date/time formats, currency conversion

### Performance & Optimization
- **Redis Caching**: Fast lookups for frequently translated content
- **Cost Optimization**: Smart engine selection, cache strategies
- **Async Processing**: Celery-based background tasks
- **WebSocket Support**: Real-time progress updates

### Enterprise Features
- **RESTful API**: Complete FastAPI endpoints
- **Authentication**: JWT-based user authentication
- **Role-Based Access**: User permissions and access control
- **Audit Logging**: Track all translation operations
- **Analytics**: Volume tracking, cost analysis, quality metrics
- **Export Formats**: JSON, XLIFF, TMX, CSV

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.10+
python --version

# PostgreSQL
psql --version

# Redis
redis-cli --version
```

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/nexus-platform.git
cd nexus-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or use pyproject.toml
pip install -e .
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

Required API keys:
- `ANTHROPIC_API_KEY` - For Claude translations
- `OPENAI_API_KEY` - For GPT-4 translations
- `DEEPL_API_KEY` - For DeepL translations
- `GOOGLE_TRANSLATE_API_KEY` - For Google Translate
- `AZURE_TRANSLATOR_KEY` - For Azure Translator
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` - For AWS Translate

### Database Setup

```bash
# Initialize database
python -m alembic upgrade head

# Or create tables directly (development only)
python -c "from config.database import init_db; init_db()"
```

### Running the Application

```bash
# Start Streamlit UI
streamlit run nexus/app.py

# Start FastAPI server
uvicorn nexus.api.main:app --reload

# Start Celery worker
celery -A nexus.core.celery_app worker --loglevel=info

# Start Celery beat (scheduled tasks)
celery -A nexus.core.celery_app beat --loglevel=info
```

## 📖 Usage Examples

### Python API

```python
from nexus.core.database import get_db_session
from nexus.modules.translation.translator import Translator

# Create translator
db = get_db_session()
translator = Translator(
    db=db,
    user_id=1,
    engine="deepl",  # or google, azure, aws, openai, claude
    use_cache=True,
    use_glossary=True,
)

# Translate text
translation = translator.translate(
    text="Hello, how are you?",
    target_lang="es",
    source_lang="en",
)

print(translation.target_text)  # "Hola, ¿cómo estás?"
print(f"Quality: {translation.quality_score}")
print(f"Processing time: {translation.processing_time_ms}ms")

db.close()
```

### Batch Translation

```python
from nexus.modules.translation.translator import BatchTranslator

batch_translator = BatchTranslator(db, user_id=1, engine="deepl")

texts = [
    "Good morning",
    "Thank you",
    "See you later",
]

translations = batch_translator.translate_batch(
    texts=texts,
    target_lang="fr",
    source_lang="en",
)

for t in translations:
    print(f"{t.source_text} → {t.target_text}")
```

### Language Detection

```python
from nexus.modules.translation.language_detection import LanguageDetector

detector = LanguageDetector()
result = detector.detect("Bonjour, comment allez-vous?")

print(f"Language: {result['language']}")  # fr
print(f"Confidence: {result['confidence']}")  # 0.99
```

### Glossary Management

```python
from nexus.modules.translation.glossary import GlossaryManager

manager = GlossaryManager(db)

# Create glossary
glossary = manager.create_glossary(
    name="Medical Terms",
    user_id=1,
    source_lang="en",
    target_lang="es",
    domain="medical",
)

# Add terms
manager.add_term(
    glossary_id=glossary.id,
    source_term="diabetes",
    target_term="diabetes",
)

# Apply glossary
terms = manager.apply_glossary(
    text="Patient has diabetes",
    source_lang="en",
    target_lang="es",
    user_id=1,
)
```

### REST API

```bash
# Translate text
curl -X POST "http://localhost:8000/api/v1/translation/translate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world",
    "target_language": "es",
    "source_language": "en",
    "engine": "deepl"
  }'

# Detect language
curl -X POST "http://localhost:8000/api/v1/translation/detect-language" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Bonjour le monde"
  }'

# List available engines
curl "http://localhost:8000/api/v1/translation/engines"
```

## 🏗️ Architecture

### Directory Structure

```
modules/translation/
├── __init__.py
├── engines.py              # Translation engine integrations
├── translator.py           # Main translator classes
├── language_detection.py   # Language detection
├── glossary.py             # Glossary management
├── quality.py              # Quality assessment
├── context.py              # Context analysis
├── cache.py                # Redis caching
├── memory.py               # Translation memory
├── api.py                  # FastAPI endpoints
├── schemas.py              # Pydantic schemas
├── tasks.py                # Celery tasks
├── ui.py                   # Streamlit UI
└── tests/                  # Unit tests
```

### Database Models

- **Translation**: Main translation records
- **TranslationHistory**: Version control for translations
- **Language**: Supported language definitions
- **Glossary**: Custom glossary containers
- **GlossaryTerm**: Individual glossary entries
- **TranslationMemory**: Translation memory entries
- **TranslationQuality**: Quality assessment results

### Supported Translation Engines

| Engine | Speed | Quality | Cost | Features |
|--------|-------|---------|------|----------|
| Google Translate | ⚡⚡⚡ | ⭐⭐⭐ | 💰 | Free tier, 100+ languages |
| DeepL | ⚡⚡ | ⭐⭐⭐⭐⭐ | 💰💰 | Best quality, neural MT |
| Azure Translator | ⚡⚡⭐ | ⭐⭐⭐⭐ | 💰💰 | Enterprise features |
| AWS Translate | ⚡⚡⭐ | ⭐⭐⭐⭐ | 💰💰 | Scalable, pay-per-use |
| OpenAI GPT-4 | ⚡ | ⭐⭐⭐⭐⭐ | 💰💰💰 | Context-aware, custom tone |
| Claude | ⚡ | ⭐⭐⭐⭐⭐ | 💰💰💰 | Best for nuance, culture |

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=nexus --cov-report=html

# Run specific test file
pytest tests/test_translation.py -v

# Run integration tests
pytest tests/integration/ -v
```

## 📊 Monitoring & Analytics

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram

translation_requests = Counter('translation_requests_total', 'Total translation requests')
translation_duration = Histogram('translation_duration_seconds', 'Translation processing time')
```

### Logging

```python
from config.logging import get_logger

logger = get_logger(__name__)

logger.info("Translation started", user_id=123, language_pair="en-es")
logger.error("Translation failed", error=str(e), exc_info=True)
```

## 🔒 Security

- **Authentication**: JWT-based authentication
- **Authorization**: Role-based access control
- **Data Encryption**: Sensitive data encrypted at rest
- **Input Validation**: Pydantic schema validation
- **Rate Limiting**: API rate limits
- **Audit Logging**: All operations logged

## 📈 Performance

### Benchmarks

- Single translation: ~500ms (with DeepL)
- Batch translation (10 texts): ~2s
- Cache hit: ~10ms
- Translation memory lookup: ~50ms

### Optimization Tips

1. **Enable caching**: Set `use_cache=True` for frequently translated content
2. **Use translation memory**: Reduces costs and improves consistency
3. **Batch processing**: Process multiple texts together
4. **Choose appropriate engine**: Balance quality vs. cost
5. **Configure Redis**: Optimize cache TTL for your use case

## 🛠️ Configuration

### Environment Variables

See `.env.example` for all configuration options:

- **Database**: `DATABASE_URL`
- **Redis**: `REDIS_URL`
- **Translation**: `DEFAULT_TRANSLATION_ENGINE`, `TRANSLATION_CACHE_TTL`
- **AI**: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`
- **Storage**: `STORAGE_PROVIDER`, `UPLOAD_DIR`

## 🚢 Deployment

### Docker

```bash
# Build image
docker build -t nexus-platform .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f app
```

### Production Checklist

- [ ] Set `DEBUG=false`
- [ ] Configure production database
- [ ] Set up Redis cluster
- [ ] Configure load balancer
- [ ] Enable SSL/TLS
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Configure backup strategy
- [ ] Set up log aggregation (ELK, Datadog)
- [ ] Review security settings
- [ ] Configure CDN for static files

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 📞 Support

- Documentation: https://docs.nexus-platform.com
- Issues: https://github.com/your-org/nexus-platform/issues
- Email: support@nexus-platform.com

## 🙏 Acknowledgments

- DeepL for exceptional translation quality
- Anthropic for Claude AI
- OpenAI for GPT-4
- All contributors and users

---

Built with ❤️ by the NEXUS Team
