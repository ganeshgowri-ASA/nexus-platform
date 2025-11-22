# NEXUS Image Recognition Module

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

## Features

### Core Capabilities

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

## Architecture

```
modules/image_recognition/
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
```

## Installation

### Prerequisites

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

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

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
```

## Configuration

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
5. Submit a pull request

## License

This module is part of the NEXUS platform and is licensed under the MIT License.

## Support

For issues and questions:
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
