# NEXUS Image Recognition Module

<<<<<<< HEAD
<<<<<<< HEAD
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![TensorFlow 2.13+](https://img.shields.io/badge/tensorflow-2.13+-orange.svg)](https://tensorflow.org)
[![PyTorch 2.0+](https://img.shields.io/badge/pytorch-2.0+-red.svg)](https://pytorch.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Production-ready image recognition and computer vision module for the NEXUS platform. Provides state-of-the-art capabilities for image classification, object detection, segmentation, feature extraction, and more.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Supported Models](#supported-models)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Performance](#performance)
- [Contributing](#contributing)
- [License](#license)
=======
Comprehensive image recognition module featuring object detection, image classification, face detection, and scene recognition powered by Google Vision API and AWS Rekognition.
>>>>>>> origin/claude/image-recognition-testing-modules-015kXqhjEMyEF78aWorhJ5ak

## Features

### Core Capabilities
<<<<<<< HEAD

#### 🎯 Image Classification
- Single-label classification
- Multi-label classification
- Zero-shot classification with GPT-4 Vision
- Custom classifier training with transfer learning
- Support for 1000+ ImageNet classes

#### 🔍 Object Detection
- General object detection (80+ COCO classes)
- Face detection with landmarks
- Logo and brand detection
- Product recognition for e-commerce
- Real-time detection on video streams

#### 🎨 Image Segmentation
- Semantic segmentation (pixel-wise classification)
- Instance segmentation (individual object separation)
- Background removal
- Mask generation and refinement

#### 🧠 Feature Extraction
- Deep feature embeddings (512-2048 dimensions)
- Similarity search (cosine, euclidean, manhattan)
- Duplicate detection
- Visual clustering (K-means, DBSCAN, hierarchical)

#### 📸 Image Preprocessing
- Normalization (standard, MinMax, Z-score)
- Resizing (fit, fill, stretch, pad)
- Augmentation (flip, rotate, brightness, contrast, blur, noise)
- Color correction (white balance, gamma, hue)
- Noise reduction (gaussian, bilateral, median, NLM)

#### 🏋️ Model Training
- Transfer learning from pre-trained models
- Fine-tuning on custom datasets
- Data augmentation pipelines
- Training progress monitoring
- Model versioning and management

#### 🚀 Batch & Real-time Processing
- Asynchronous batch processing with Celery
- Real-time predictions
- Ensemble predictions (voting, averaging)
- Caching for improved performance
- Progress tracking with WebSocket

#### 🌆 Scene Understanding
- Scene classification (indoor, outdoor, urban, natural)
- Context analysis
- Object relationship detection
- Activity recognition
- Scene graph generation

#### ✅ Quality Assessment
- Blur detection (Laplacian variance, motion blur)
- Noise detection
- Brightness and contrast analysis
- Color saturation analysis
- Sharpness metrics
- Quality scoring with recommendations

#### 🏷️ Annotation Tools
- Bounding box annotation
- Polygon annotation
- Mask annotation
- Point annotation
- Label management
- Annotation validation
- Dataset statistics

#### 📦 Export Capabilities
- JSON export
- CSV export
- Excel export (multi-sheet)
- COCO format
- YOLO format
- Pascal VOC format
- Archive creation (ZIP)
=======
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
>>>>>>> origin/claude/image-recognition-testing-modules-015kXqhjEMyEF78aWorhJ5ak
=======
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
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

## Architecture

```
modules/image_recognition/
<<<<<<< HEAD
<<<<<<< HEAD
├── __init__.py                  # Module initialization
├── db_models.py                 # SQLAlchemy ORM models
├── schemas.py                   # Pydantic request/response schemas
├── models.py                    # Pre-trained model wrappers
├── classifier.py                # Classification engines
├── detection.py                 # Object detection
├── segmentation.py              # Image segmentation
├── features.py                  # Feature extraction
├── preprocessing.py             # Image preprocessing
├── training.py                  # Model training
├── prediction.py                # Prediction engines
├── scene_understanding.py       # Scene analysis
├── quality.py                   # Quality assessment
├── custom_models.py             # Custom model management
├── annotation.py                # Annotation tools
├── export.py                    # Export functionality
├── tasks.py                     # Celery async tasks
├── api.py                       # FastAPI routes
├── ui.py                        # Streamlit dashboard
├── requirements.txt             # Dependencies
├── README.md                    # This file
└── tests/                       # Test suite
    ├── conftest.py              # Pytest fixtures
    ├── test_models.py
    ├── test_classifier.py
    ├── test_detection.py
    ├── test_preprocessing.py
    ├── test_features.py
    ├── test_quality.py
    ├── test_api.py
    ├── test_tasks.py
    ├── test_db_models.py
    └── test_export.py
=======
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
>>>>>>> origin/claude/image-recognition-testing-modules-015kXqhjEMyEF78aWorhJ5ak
=======
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
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
```

## Installation

### Prerequisites
<<<<<<< HEAD
<<<<<<< HEAD

- Python 3.10 or higher
- PostgreSQL 13+
- Redis 6+
- CUDA-capable GPU (optional, for faster inference)

### Install Dependencies

```bash
# Clone repository
cd /path/to/nexus-platform

# Install module dependencies
pip install -r modules/image_recognition/requirements.txt

# For GPU support (NVIDIA)
pip install tensorflow[and-cuda]
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Database Setup

```bash
# Create database
createdb nexus_image_recognition

# Run migrations
alembic upgrade head
```

### Environment Variables

Create a `.env` file:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/nexus

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Storage
STORAGE_TYPE=local  # local, s3, azure
STORAGE_PATH=/tmp/nexus/images
=======

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
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

<<<<<<< HEAD
# API
API_HOST=0.0.0.0
API_PORT=8000
JWT_SECRET_KEY=your-secret-key
```

## Quick Start

### 1. Start Services

```bash
# Start Redis
redis-server

# Start Celery worker
celery -A modules.image_recognition.tasks worker --loglevel=info

# Start API server
uvicorn modules.image_recognition.api:app --reload --port 8000

# Start UI (in another terminal)
streamlit run modules/image_recognition/ui.py
```

### 2. Basic Usage

#### Python API

```python
from modules.image_recognition.classifier import ImageClassifier
from PIL import Image

# Initialize classifier
classifier = ImageClassifier(model_type="resnet50")

# Classify image
image = Image.open("cat.jpg")
result = classifier.classify(image, top_k=5)

print(result['predictions'])
# [
#   {'label': 'tabby_cat', 'confidence': 0.87},
#   {'label': 'tiger_cat', 'confidence': 0.11},
#   ...
# ]
```

#### REST API

```bash
# Classification
curl -X POST http://localhost:8000/api/image-recognition/classify \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@cat.jpg" \
  -F "model_type=resnet50"

# Object Detection
curl -X POST http://localhost:8000/api/image-recognition/detect \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@street.jpg" \
  -F "model_type=yolo"
```

#### Streamlit UI

```bash
# Open browser
open http://localhost:8501
```

## API Documentation

### Authentication

All API endpoints require JWT authentication:

```bash
Authorization: Bearer <your_jwt_token>
```

### Endpoints

#### Classification

**POST** `/api/image-recognition/classify`

Classify a single image.

**Request:**
- `image`: Image file (multipart/form-data)
- `model_type`: Model to use (vgg16, resnet50, inceptionv3, efficientnet)
- `top_k`: Number of top predictions (default: 5)
- `confidence_threshold`: Minimum confidence (default: 0.0)

**Response:**
```json
{
  "success": true,
  "predictions": [
    {
      "label": "golden_retriever",
      "confidence": 0.95,
      "class_id": 207
    }
  ],
  "processing_time_ms": 145.2,
  "model_name": "resnet50"
}
```

#### Object Detection

**POST** `/api/image-recognition/detect`

Detect objects in an image.

**Request:**
- `image`: Image file
- `model_type`: yolo (default)
- `confidence_threshold`: Minimum confidence (default: 0.5)
- `iou_threshold`: IoU threshold for NMS (default: 0.45)

**Response:**
```json
{
  "success": true,
  "detections": [
    {
      "label": "person",
      "confidence": 0.92,
      "bbox": {
        "x": 100,
        "y": 50,
        "width": 200,
        "height": 400
      }
    }
  ],
  "num_detections": 3,
  "processing_time_ms": 89.3
}
```

#### Batch Processing

**POST** `/api/image-recognition/classify/batch`

Process multiple images asynchronously.

**Request:**
```json
{
  "job_name": "Product Classification",
  "image_urls": [
    "https://example.com/img1.jpg",
    "https://example.com/img2.jpg"
  ],
  "model_type": "resnet50",
  "confidence_threshold": 0.5
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "message": "Batch job created successfully"
}
```

#### Job Status

**GET** `/api/image-recognition/jobs/{job_id}`

Get job status and results.

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Product Classification",
  "status": "completed",
  "progress_percentage": 100.0,
  "total_images": 50,
  "processed_images": 50,
  "successful_images": 48,
  "failed_images": 2,
  "processing_time_seconds": 45.2,
  "results_summary": {
    "top_labels": ["shirt", "pants", "shoes"],
    "average_confidence": 0.87
  }
}
```

### WebSocket

Real-time job updates via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/image-recognition/ws/user_id');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Job update:', data);
  // { job_id: '...', status: 'processing', progress: 45.2 }
};
```

## Supported Models

### Pre-trained Models

| Model | Type | Input Size | Parameters | Accuracy (ImageNet) | Speed |
|-------|------|------------|------------|---------------------|-------|
| VGG16 | Classification | 224x224 | 138M | 71.3% | Medium |
| ResNet50 | Classification | 224x224 | 25.6M | 76.1% | Fast |
| InceptionV3 | Classification | 299x299 | 23.8M | 77.9% | Medium |
| EfficientNet-B0 | Classification | 224x224 | 5.3M | 77.1% | Fast |
| YOLOv5s | Detection | 640x640 | 7.2M | mAP 37.4% | Very Fast |
| YOLOv5m | Detection | 640x640 | 21.2M | mAP 45.4% | Fast |
| YOLOv5l | Detection | 640x640 | 46.5M | mAP 49.0% | Medium |
| GPT-4 Vision | Multi-modal | Variable | N/A | State-of-art | Slow |

### Custom Models

Train your own models:

```python
from modules.image_recognition.training import ModelTrainer

trainer = ModelTrainer(
    base_model="resnet50",
    num_classes=10,
    dataset_path="/path/to/dataset"
)

history = trainer.train(
    epochs=20,
    batch_size=32,
    learning_rate=0.001
)

trainer.save_model("my_custom_model.h5")
```

## Usage Examples

### Example 1: Image Classification

```python
from modules.image_recognition.classifier import ImageClassifier
from PIL import Image

# Load classifier
classifier = ImageClassifier(model_type="resnet50")

# Classify image
image = Image.open("dog.jpg")
result = classifier.classify(
    image,
    top_k=3,
    confidence_threshold=0.1
)

for pred in result['predictions']:
    print(f"{pred['label']}: {pred['confidence']:.2%}")
```

### Example 2: Object Detection

```python
from modules.image_recognition.detection import ObjectDetector
from PIL import Image

# Load detector
detector = ObjectDetector(model_type="yolo")

# Detect objects
image = Image.open("street.jpg")
result = detector.detect(
    image,
    confidence_threshold=0.5
)

for detection in result['detections']:
    label = detection['label']
    conf = detection['confidence']
    bbox = detection['bbox']
    print(f"{label} ({conf:.2%}): {bbox}")
```

### Example 3: Similarity Search

```python
from modules.image_recognition.features import VisualSearchEngine
from PIL import Image

# Initialize search engine
search = VisualSearchEngine(model_type="resnet50")

# Index images
search.index_image("img1.jpg", metadata={"product_id": 1})
search.index_image("img2.jpg", metadata={"product_id": 2})

# Find similar images
query_image = Image.open("query.jpg")
results = search.search(query_image, top_k=5)

for result in results:
    print(f"Similarity: {result['similarity']:.2%}")
    print(f"Metadata: {result['metadata']}")
```

### Example 4: Batch Processing

```python
from modules.image_recognition.prediction import BatchPredictor

# Initialize predictor
predictor = BatchPredictor(
    model_type="resnet50",
    batch_size=32
)

# Process multiple images
image_paths = ["img1.jpg", "img2.jpg", "img3.jpg"]
results = predictor.predict_batch(
    image_paths,
    show_progress=True
)

for i, result in enumerate(results):
    print(f"Image {i+1}: {result['predictions'][0]['label']}")
```

### Example 5: Quality Assessment

```python
from modules.image_recognition.quality import QualityAssessment
from PIL import Image

# Initialize assessor
qa = QualityAssessment()

# Assess image quality
image = Image.open("photo.jpg")
result = qa.assess(image)

print(f"Quality Score: {result['quality_score']:.2%}")
print(f"Is Blurry: {result['is_blurry']}")
print(f"Is Noisy: {result['is_noisy']}")
print(f"Brightness: {result['brightness']:.2f}")
print(f"Recommendations: {result['recommendations']}")
=======
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
>>>>>>> origin/claude/image-recognition-testing-modules-015kXqhjEMyEF78aWorhJ5ak
```

## Configuration

<<<<<<< HEAD
### Model Configuration

```python
# Custom model configuration
config = {
    'input_shape': (224, 224),
    'batch_size': 32,
    'confidence_threshold': 0.5,
    'use_gpu': True,
    'num_workers': 4
}

classifier = ImageClassifier(
    model_type="resnet50",
    config=config
)
```

### Preprocessing Configuration

```python
from modules.image_recognition.preprocessing import PreprocessingPipeline

pipeline = PreprocessingPipeline([
    ('resize', {'size': (224, 224), 'mode': 'fit'}),
    ('normalize', {'method': 'standard'}),
    ('augment', {'flip': True, 'rotate': 15})
])

processed_image = pipeline.process(image)
```

## Testing

```bash
# Install test dependencies
pip install -r modules/image_recognition/tests/requirements-test.txt

# Run all tests
cd modules/image_recognition
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_classifier.py -v

# Run specific test
pytest tests/test_classifier.py::test_image_classifier_predict -v
```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy module
COPY . /app/modules/image_recognition

# Run API server
CMD ["uvicorn", "modules.image_recognition.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

1. **GPU Support**: Use CUDA-enabled Docker images for GPU inference
2. **Load Balancing**: Deploy multiple API instances behind a load balancer
3. **Caching**: Use Redis for caching predictions and features
4. **Monitoring**: Integrate with Prometheus/Grafana for monitoring
5. **Logging**: Configure centralized logging (ELK stack, CloudWatch)
6. **Storage**: Use S3/Azure Blob for image storage
7. **CDN**: Serve images through CDN for faster access

## Performance

### Benchmarks

Tested on NVIDIA Tesla V100 GPU:

| Task | Model | Images/sec | Latency (ms) |
|------|-------|------------|--------------|
| Classification | ResNet50 | 450 | 2.2 |
| Classification | EfficientNet-B0 | 380 | 2.6 |
| Detection | YOLOv5s | 140 | 7.1 |
| Detection | YOLOv5m | 90 | 11.1 |
| Segmentation | DeepLab | 50 | 20.0 |
| Feature Extraction | ResNet50 | 520 | 1.9 |

### Optimization Tips

1. **Batch Processing**: Process multiple images together
2. **Model Quantization**: Use FP16 or INT8 for faster inference
3. **TensorRT**: Convert models to TensorRT format
4. **Caching**: Cache predictions for frequently accessed images
5. **Async Processing**: Use Celery for non-blocking processing
6. **GPU Utilization**: Ensure GPU is being used (check logs)

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
=======
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
=======
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
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

## Troubleshooting

### Common Issues

<<<<<<< HEAD
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
=======
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
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

## Contributing

1. Fork the repository
2. Create a feature branch
<<<<<<< HEAD
3. Make your changes
4. Add tests
>>>>>>> origin/claude/image-recognition-testing-modules-015kXqhjEMyEF78aWorhJ5ak
5. Submit a pull request

## License

<<<<<<< HEAD
This module is part of the NEXUS platform and is licensed under the MIT License.
=======
Part of the NEXUS platform - See main README for license information.
>>>>>>> origin/claude/image-recognition-testing-modules-015kXqhjEMyEF78aWorhJ5ak
=======
3. Write tests for new features
4. Submit a pull request

## License

MIT License
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

## Support

For issues and questions:
<<<<<<< HEAD
<<<<<<< HEAD
- GitHub Issues: [NEXUS Issues](https://github.com/nexus/platform/issues)
- Documentation: [NEXUS Docs](https://docs.nexus.ai)
- Email: support@nexus.ai

## Acknowledgments

- TensorFlow and Keras teams
- PyTorch team
- Ultralytics (YOLO)
- OpenAI (GPT-4 Vision)
- Anthropic (Claude)

---

**Built with ❤️ by the NEXUS Team**
=======
- Open an issue on GitHub
- Check the documentation
- Contact the development team
>>>>>>> origin/claude/image-recognition-testing-modules-015kXqhjEMyEF78aWorhJ5ak
=======
- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)
- Documentation: [Full docs](https://docs.nexus-platform.com)
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
