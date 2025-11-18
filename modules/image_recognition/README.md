# NEXUS Image Recognition Module

## Overview

The Image Recognition module provides comprehensive computer vision capabilities including object detection, image classification, face detection, and scene recognition. It integrates with multiple AI providers (Google Vision, AWS Rekognition) and supports custom model training.

## Features

- **Object Detection**: Identify and locate objects within images
- **Image Classification**: Categorize images with labels and categories
- **Face Detection**: Detect faces and analyze facial attributes (age, gender, emotions)
- **Scene Recognition**: Identify scenes, landmarks, and contexts
- **Custom Model Training**: Train and deploy custom computer vision models
- **Async Processing**: Handle large batches with Celery task queue
- **RESTful API**: FastAPI-based API for easy integration
- **Web UI**: User-friendly Streamlit interface

## Architecture

```
modules/image_recognition/
├── api/                    # FastAPI application
│   └── main.py            # API endpoints
├── models/                 # Database models and schemas
│   ├── database.py        # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   └── db_connection.py   # Database connection
├── services/              # Business logic
│   ├── google_vision_service.py
│   ├── aws_rekognition_service.py
│   └── analysis_service.py
├── tasks/                 # Async task processing
│   └── celery_tasks.py
├── ui/                    # Streamlit UI
│   └── streamlit_app.py
└── config/                # Configuration files
```

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Google Cloud Vision API key or AWS credentials

### Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Initialize database**:
   ```bash
   python -c "from modules.image_recognition.models.db_connection import init_db; init_db()"
   ```

4. **Start Redis**:
   ```bash
   redis-server
   ```

5. **Start Celery worker**:
   ```bash
   celery -A modules.image_recognition.tasks.celery_tasks worker --loglevel=info
   ```

6. **Start API server**:
   ```bash
   uvicorn modules.image_recognition.api.main:app --reload --port 8000
   ```

7. **Start Streamlit UI** (optional):
   ```bash
   streamlit run modules/image_recognition/ui/streamlit_app.py
   ```

## Docker Deployment

```bash
docker-compose up -d
```

This will start all services:
- API server (port 8000)
- Celery worker
- Celery beat
- Flower monitoring (port 5555)
- Streamlit UI (port 8501)
- PostgreSQL
- Redis

## API Usage

### Analyze Image

```python
import requests

# Upload and analyze image
files = {'file': open('image.jpg', 'rb')}
params = {
    'analysis_type': 'object_detection',
    'provider': 'google_vision'
}

response = requests.post(
    'http://localhost:8000/analyze/upload',
    files=files,
    params=params
)

print(response.json())
```

### Using Image URL

```python
data = {
    'image_url': 'https://example.com/image.jpg',
    'analysis_type': 'face_detection',
    'provider': 'aws_rekognition'
}

response = requests.post(
    'http://localhost:8000/analyze',
    json=data
)

analysis_id = response.json()['id']
```

### Get Results

```python
response = requests.get(f'http://localhost:8000/analyze/{analysis_id}')
results = response.json()

# Access detected objects
for obj in results['objects']:
    print(f"Object: {obj['name']}, Confidence: {obj['confidence']}")

# Access detected faces
for face in results['faces']:
    print(f"Face detected with {face['confidence']} confidence")
    print(f"Age range: {face['age_range']}")
    print(f"Emotions: {face['emotions']}")
```

### Batch Processing

```python
data = {
    'images': [
        'https://example.com/image1.jpg',
        'https://example.com/image2.jpg',
        'https://example.com/image3.jpg'
    ],
    'analysis_type': 'image_classification',
    'provider': 'google_vision'
}

response = requests.post('http://localhost:8000/analyze/batch', json=data)
task_id = response.json()['task_id']
```

## Analysis Types

1. **object_detection**: Detect and locate objects in images
2. **image_classification**: Classify images with labels
3. **face_detection**: Detect faces and analyze attributes
4. **scene_recognition**: Recognize scenes and landmarks

## Providers

- **google_vision**: Google Cloud Vision API
  - Pros: High accuracy, comprehensive features
  - Best for: General-purpose image analysis

- **aws_rekognition**: AWS Rekognition
  - Pros: Fast processing, scalable
  - Best for: Face analysis, content moderation

## Database Schema

### ImageAnalysis
- Stores analysis metadata and results
- Links to detected objects, faces, labels, scenes

### DetectedObject
- Object name, confidence, bounding box
- Attributes (color, size, etc.)

### DetectedFace
- Face location, confidence
- Attributes (age, gender, emotions)
- Quality metrics

### ImageLabel
- Classification labels
- Confidence scores, categories

### DetectedScene
- Scene types and attributes
- Context information

## API Endpoints

### Core Endpoints

- `POST /analyze` - Create new analysis
- `POST /analyze/upload` - Upload and analyze image
- `POST /analyze/batch` - Batch processing
- `GET /analyze/{id}` - Get analysis results
- `GET /analyze/{id}/status` - Get analysis status
- `GET /analyses` - List all analyses
- `DELETE /analyze/{id}` - Delete analysis

### Analytics

- `GET /analytics` - Get analytics and statistics

### Custom Models

- `POST /models` - Register custom model
- `GET /models` - List custom models

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/nexus_image

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Google Vision
GOOGLE_VISION_API_KEY=your_api_key

# AWS Rekognition
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# Upload Directory
UPLOAD_DIR=/tmp/nexus_uploads
```

## Performance Optimization

1. **Caching**: Results cached for duplicate images
2. **Async Processing**: Celery for non-blocking operations
3. **Batch Processing**: Process multiple images efficiently
4. **Connection Pooling**: Database connection optimization

## Monitoring

### Celery Flower

Access Flower dashboard at `http://localhost:5555` to monitor:
- Active tasks
- Task history
- Worker status
- Performance metrics

### API Metrics

- Total analyses
- Analyses by type
- Average confidence scores
- Most detected objects/labels

## Security Considerations

1. **API Keys**: Store securely in environment variables
2. **Input Validation**: All inputs validated via Pydantic
3. **File Upload**: Restricted file types and sizes
4. **Rate Limiting**: Implement rate limiting for production

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check PostgreSQL is running
   systemctl status postgresql
   ```

2. **Redis Connection Error**
   ```bash
   # Check Redis is running
   redis-cli ping
   ```

3. **API Key Error**
   ```bash
   # Verify API keys in .env
   echo $GOOGLE_VISION_API_KEY
   ```

4. **Celery Worker Not Processing**
   ```bash
   # Restart worker
   celery -A modules.image_recognition.tasks.celery_tasks worker --loglevel=info
   ```

## Testing

```bash
# Run tests
pytest modules/image_recognition/tests/

# With coverage
pytest modules/image_recognition/tests/ --cov=modules/image_recognition
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Submit a pull request

## License

MIT License

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)
- Documentation: [Full docs](https://docs.nexus-platform.com)
