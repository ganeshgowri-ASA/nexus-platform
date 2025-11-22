# NEXUS Speech-to-Text Module

Comprehensive speech-to-text solution with support for multiple providers, speaker diarization, multilingual transcription, and real-time processing.

## 🌟 Features

- **Multiple Providers**: Whisper (local), Google Cloud Speech-to-Text, AWS Transcribe
- **Speaker Diarization**: Identify and separate different speakers in audio
- **Multilingual Support**: 100+ languages supported
- **Real-time Processing**: Async processing with Celery
- **Timestamps**: Word-level and segment-level timestamps
- **RESTful API**: FastAPI-based REST API
- **Modern UI**: Streamlit-based web interface
- **Scalable**: PostgreSQL database with async task processing

## 📋 Requirements

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- FFmpeg (for audio processing)

### Optional
- CUDA-capable GPU (for faster local Whisper processing)
- Google Cloud Platform account (for Google Speech-to-Text)
- AWS account (for AWS Transcribe)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
cd modules/speech_to_text

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install FFmpeg (required for audio processing)
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### 2. Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Required configurations:**
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- Choose at least one provider:
  - Whisper (no additional config needed)
  - Google: Set `GOOGLE_CREDENTIALS_PATH` and `GOOGLE_PROJECT_ID`
  - AWS: Set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_BUCKET`

### 3. Database Setup

```bash
# Initialize database tables
python -c "from config.database import init_db; init_db()"
```

### 4. Start Services

**Terminal 1: API Server**
```bash
python -m api.app
# Or with uvicorn directly:
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2: Celery Worker (optional, for async processing)**
```bash
celery -A tasks.celery_app worker --loglevel=info
```

**Terminal 3: Streamlit UI**
```bash
streamlit run ui/app.py
```

### 5. Access the Application

- **Streamlit UI**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc

## 📖 Usage

### Web Interface (Streamlit)

1. Open http://localhost:8501
2. Configure settings in the sidebar:
   - Select provider (Whisper/Google/AWS)
   - Set language or enable auto-detection
   - Enable speaker diarization if needed
3. Upload audio file
4. Click "Transcribe"
5. View results with segments and speakers

### API Usage

#### Upload and Transcribe

```bash
curl -X POST "http://localhost:8000/api/v1/speech/transcribe" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.mp3" \
  -F "provider=whisper" \
  -F "language=en" \
  -F "enable_diarization=true"
```

#### Get Transcription

```bash
curl -X GET "http://localhost:8000/api/v1/speech/transcriptions/1?include_segments=true"
```

#### List Transcriptions

```bash
curl -X GET "http://localhost:8000/api/v1/speech/transcriptions?user_id=demo&limit=10"
```

### Python Client Example

```python
import requests

# Upload file
with open("audio.mp3", "rb") as f:
    files = {"file": f}
    params = {
        "provider": "whisper",
        "language": "en",
        "enable_diarization": True,
        "user_id": "demo"
    }
    response = requests.post(
        "http://localhost:8000/api/v1/speech/transcribe",
        files=files,
        params=params
    )
    result = response.json()
    print(f"Transcription ID: {result['id']}")

# Get results
response = requests.get(
    f"http://localhost:8000/api/v1/speech/transcriptions/{result['id']}",
    params={"include_segments": True}
)
transcription = response.json()
print(f"Text: {transcription['full_text']}")
```

## 🎯 Providers

### Whisper (OpenAI)

**Pros:**
- Free and open-source
- Works offline
- Good accuracy
- 99 languages

**Setup:**
```bash
# No additional setup needed
# Model will be downloaded on first use
```

**Configuration:**
```env
WHISPER_MODEL=base  # tiny, base, small, medium, large
WHISPER_DEVICE=cpu  # or cuda for GPU
```

### Google Cloud Speech-to-Text

**Pros:**
- Excellent accuracy
- Native speaker diarization
- 125+ languages
- Streaming support

**Setup:**
1. Create a Google Cloud project
2. Enable Speech-to-Text API
3. Create service account and download credentials
4. Set environment variables

**Configuration:**
```env
GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
GOOGLE_PROJECT_ID=your-project-id
```

### AWS Transcribe

**Pros:**
- Good accuracy
- AWS ecosystem integration
- Custom vocabularies
- Medical/legal specialization

**Setup:**
1. Create AWS account
2. Create S3 bucket for audio files
3. Create IAM user with Transcribe and S3 permissions
4. Set environment variables

**Configuration:**
```env
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket
```

## 🎭 Speaker Diarization

Speaker diarization identifies "who spoke when" in audio files.

### Enabling Diarization

**API:**
```bash
curl -X POST "http://localhost:8000/api/v1/speech/transcribe" \
  -F "file=@audio.mp3" \
  -F "enable_diarization=true" \
  -F "max_speakers=5"
```

**Python:**
```python
from services.factory import SpeechServiceFactory
from utils.diarization import DiarizationService

# Use Google or AWS (native diarization)
service = SpeechServiceFactory.create("google", config)
result = await service.transcribe_file(
    audio_path,
    enable_diarization=True,
    max_speakers=5
)

# Or use pyannote with Whisper
diarization_service = DiarizationService()
segments = diarization_service.diarize(audio_path, max_speakers=5)
```

### Provider Support

- ✅ **Google**: Native support
- ✅ **AWS**: Native support
- ⚠️ **Whisper**: Use pyannote.audio separately

## 🌍 Supported Languages

### Whisper (99 languages)
English, Chinese, Spanish, French, German, Japanese, Korean, Portuguese, Russian, Italian, and 89 more...

### Google Cloud (125+ languages)
All major languages with regional variants (e.g., en-US, en-GB, es-ES, es-MX)

### AWS Transcribe (30+ languages)
Major languages including English, Spanish, French, German, Portuguese, Chinese, Japanese, Korean, Arabic, Hindi, and more...

## 📁 Project Structure

```
modules/speech_to_text/
├── api/                    # FastAPI application
│   ├── app.py             # Main FastAPI app
│   ├── routes.py          # API endpoints
│   └── schemas.py         # Pydantic models
├── config/                # Configuration
│   ├── settings.py        # App settings
│   └── database.py        # Database connection
├── models/                # Database models
│   └── transcription.py   # SQLAlchemy models
├── services/              # Speech service implementations
│   ├── base.py           # Base service class
│   ├── whisper_service.py
│   ├── google_service.py
│   ├── aws_service.py
│   └── factory.py        # Service factory
├── tasks/                # Celery tasks
│   ├── celery_app.py
│   └── transcription_tasks.py
├── ui/                   # Streamlit UI
│   ├── app.py
│   └── .streamlit/
├── utils/                # Utilities
│   ├── diarization.py   # Speaker diarization
│   └── audio_utils.py   # Audio processing
├── tests/               # Tests
├── .env.example         # Example environment file
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=modules.speech_to_text

# Run specific test
pytest tests/test_services.py
```

## 🐳 Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📊 Performance Tips

### Whisper
- Use GPU for 5-10x faster processing
- Smaller models (tiny, base) are faster but less accurate
- Use `compute_type="int8"` for faster inference

### Google Cloud
- Use streaming API for real-time transcription
- Enable phrase hints for better accuracy
- Use regional endpoints for lower latency

### AWS Transcribe
- Store files in same region as service
- Use job queuing for batch processing
- Enable custom vocabularies for domain-specific terms

## 🔒 Security

- Store API credentials in environment variables, never in code
- Use HTTPS in production
- Implement authentication/authorization for API endpoints
- Regularly rotate API keys
- Sanitize uploaded filenames
- Limit file upload sizes

## 🛠️ Troubleshooting

### Whisper model download fails
```bash
# Manual download
python -c "import whisper; whisper.load_model('base')"
```

### Audio format not supported
```bash
# Convert to WAV using FFmpeg
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```

### Celery workers not processing tasks
```bash
# Check Redis connection
redis-cli ping

# Check Celery worker status
celery -A tasks.celery_app inspect active
```

### Database connection error
```bash
# Test PostgreSQL connection
psql $DATABASE_URL
```

## 📝 API Documentation

Full API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

- `POST /api/v1/speech/transcribe` - Upload and transcribe audio
- `GET /api/v1/speech/transcriptions` - List transcriptions
- `GET /api/v1/speech/transcriptions/{id}` - Get transcription details
- `DELETE /api/v1/speech/transcriptions/{id}` - Delete transcription
- `GET /api/v1/speech/providers` - List available providers
- `GET /api/v1/speech/health` - Health check

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is part of the NEXUS platform.

## 🙏 Acknowledgments

- OpenAI Whisper
- Google Cloud Speech-to-Text
- AWS Transcribe
- pyannote.audio
- FastAPI
- Streamlit

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review API docs at /docs endpoint

## 🗺️ Roadmap

- [ ] WebSocket support for real-time streaming
- [ ] Custom vocabulary/phrase boosting
- [ ] Audio preprocessing (noise reduction, normalization)
- [ ] Batch processing interface
- [ ] Export to SRT/VTT subtitle formats
- [ ] Translation support
- [ ] Speaker identification training
- [ ] Model fine-tuning interface
- [ ] Mobile app support

---

**Built with ❤️ for the NEXUS Platform**
