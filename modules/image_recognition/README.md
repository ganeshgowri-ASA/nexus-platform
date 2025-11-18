# NEXUS Image Recognition Module

Comprehensive image recognition module featuring object detection, image classification, face detection, and scene recognition powered by Google Vision API and AWS Rekognition.

## Features

### Core Capabilities
- **Object Detection**: Detect and classify objects in images with bounding boxes
- **Image Classification**: Classify images into categories with confidence scores
- **Face Detection**: Detect faces with age, gender, and emotion analysis
- **Scene Recognition**: Identify scenes and environments in images
- **Custom Model Training**: Train and deploy custom computer vision models

### Technical Features
- FastAPI REST API with async support
- PostgreSQL database for analysis records
- Redis caching for performance
- Celery task queue for async processing
- Dual provider support (Google Vision & AWS Rekognition)
- Streamlit interactive UI
- Comprehensive analytics and reporting

## Architecture

```
modules/image_recognition/
├── api/                    # FastAPI application
│   └── main.py            # API endpoints
├── models/                # Data models
│   ├── database.py        # SQLAlchemy models
│   └── schemas.py         # Pydantic schemas
├── services/              # Business logic
│   ├── vision_service.py  # Vision API integration
│   └── celery_tasks.py    # Async task processing
├── ui/                    # User interface
│   └── streamlit_app.py   # Streamlit dashboard
├── config/                # Configuration
│   └── settings.py        # Settings management
└── tests/                 # Test suite
```

## Installation

### Prerequisites
- Python 3.9+
- PostgreSQL 14+
- Redis 7+

### Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

3. **Set up Google Cloud Vision** (optional):
```bash
# Download service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

4. **Set up AWS Rekognition** (optional):
```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_REGION="us-east-1"
```

5. **Initialize database**:
```bash
# Database tables are created automatically on first run
python -c "from modules.image_recognition.api.main import app"
```

## Usage

### Starting the API Server

```bash
# Development
uvicorn modules.image_recognition.api.main:app --reload --port 8001

# Production
uvicorn modules.image_recognition.api.main:app --host 0.0.0.0 --port 8001 --workers 4
```

### Starting Celery Workers

```bash
celery -A modules.image_recognition.services.celery_tasks worker --loglevel=info
```

### Starting the Streamlit UI

```bash
streamlit run modules/image_recognition/ui/streamlit_app.py --server.port 8501
```

### Using Docker

```bash
# Build and start all services
docker-compose up -d

# Access services:
# - API: http://localhost:8001
# - UI: http://localhost:8501
# - API Docs: http://localhost:8001/docs
```

## API Endpoints

### Image Analysis

```bash
# Analyze image
POST /analyze
Content-Type: multipart/form-data

curl -X POST "http://localhost:8001/analyze" \
  -F "file=@image.jpg" \
  -F "analysis_type=object_detection" \
  -F "user_id=1" \
  -F "provider=aws"
```

### Get Analyses

```bash
# Get all analyses
GET /analyses?user_id=1&limit=50

# Get specific analysis
GET /analyses/{analysis_id}
```

### Analytics

```bash
# Get analytics
GET /analytics?user_id=1&days=30
```

### Custom Models

```bash
# Train custom model
POST /models/train
Content-Type: application/json

{
  "name": "Product Classifier",
  "description": "Custom model for product classification",
  "model_type": "classification",
  "dataset_id": 1,
  "user_id": 1
}

# Get models
GET /models?user_id=1
```

## Configuration

### Vision Provider Selection

You can choose between Google Vision and AWS Rekognition:

```python
# Use AWS Rekognition (default)
provider = "aws"

# Use Google Cloud Vision
provider = "google"
```

### Analysis Types

- `object_detection`: Detect and classify objects with bounding boxes
- `image_classification`: Classify images into categories
- `face_detection`: Detect faces with attributes
- `scene_recognition`: Identify scenes and environments
- `custom_model`: Use custom trained models

## Examples

### Python Client

```python
import requests

# Analyze image
with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8001/analyze',
        files={'file': f},
        params={
            'analysis_type': 'object_detection',
            'user_id': 1,
            'provider': 'aws'
        }
    )

analysis = response.json()
print(f"Analysis ID: {analysis['id']}")
print(f"Status: {analysis['status']}")

# Get results
results = requests.get(f'http://localhost:8001/analyses/{analysis["id"]}')
print(results.json())
```

### Streamlit UI

The Streamlit UI provides an interactive dashboard for:
- Uploading and analyzing images
- Viewing analysis results with visualizations
- Managing custom models
- Viewing analytics and statistics
- Browsing analysis history

Access at: http://localhost:8501

## Performance

### Optimization Tips

1. **Use Redis caching** for frequently accessed data
2. **Enable Celery workers** for async processing
3. **Batch processing** for multiple images
4. **Image compression** before uploading
5. **Provider selection** based on use case:
   - AWS Rekognition: Better for faces and celebrities
   - Google Vision: Better for general objects and scenes

### Scaling

- Horizontal scaling with multiple API instances
- Multiple Celery workers for parallel processing
- Database read replicas for analytics
- CDN for image storage and delivery

## Testing

```bash
# Run tests
pytest modules/image_recognition/tests -v

# With coverage
pytest modules/image_recognition/tests --cov=modules.image_recognition --cov-report=html
```

## Monitoring

### Celery Monitoring with Flower

```bash
# Start Flower
celery -A modules.image_recognition.services.celery_tasks flower --port=5555

# Access: http://localhost:5555
```

### API Metrics

- Health check: `GET /health`
- Prometheus metrics: Available via prometheus-client

## Troubleshooting

### Common Issues

1. **Google Vision API errors**:
   - Verify service account key is valid
   - Check API is enabled in Google Cloud Console
   - Ensure billing is enabled

2. **AWS Rekognition errors**:
   - Verify AWS credentials
   - Check IAM permissions for Rekognition
   - Ensure region is correct

3. **Celery task failures**:
   - Check Redis connection
   - Verify image data is valid
   - Check worker logs: `celery -A ... worker --loglevel=debug`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

Part of the NEXUS platform - See main README for license information.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation
- Contact the development team
