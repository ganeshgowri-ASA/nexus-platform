"""
Pytest Fixtures for Image Recognition Module Tests

Provides comprehensive fixtures for testing including:
- Database fixtures (session, connection, transaction)
- Model fixtures (mock models, test models)
- Image fixtures (sample images, test data)
- API client fixture
- Mock external services (OpenAI, Celery)
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any, List
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import numpy as np
from PIL import Image
import io
import base64
from unittest.mock import Mock, MagicMock, patch

# SQLAlchemy
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocket

# Database models
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.image_recognition.db_models import (
    Base, RecognitionJob, Image as ImageModel, Prediction,
    Label, RecognitionModel, Annotation, TrainingDataset,
    JobStatus, JobType, ModelType, ImageFormat
)


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def database_url() -> str:
    """Get test database URL."""
    return os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture(scope="session")
def engine(database_url: str):
    """Create test database engine."""
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """Create a new database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def db_connection(engine):
    """Provide database connection."""
    connection = engine.connect()
    yield connection
    connection.close()


@pytest.fixture
def db_transaction(db_connection):
    """Provide database transaction that rolls back after test."""
    transaction = db_connection.begin()
    yield transaction
    transaction.rollback()


# ============================================================================
# MODEL FIXTURES
# ============================================================================

@pytest.fixture
def mock_tensorflow_model():
    """Mock TensorFlow model."""
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([[0.1, 0.7, 0.2]])
    return mock_model


@pytest.fixture
def mock_pytorch_model():
    """Mock PyTorch model."""
    mock_model = MagicMock()
    mock_model.eval.return_value = mock_model
    mock_model.to.return_value = mock_model
    return mock_model


@pytest.fixture
def mock_yolo_model():
    """Mock YOLO model."""
    mock_model = MagicMock()
    mock_model.names = {0: "person", 1: "car", 2: "dog"}
    mock_model.conf = 0.5
    mock_model.iou = 0.45

    # Mock detection results
    mock_result = MagicMock()
    mock_result.xyxy = [np.array([[10, 20, 100, 200, 0.95, 0]])]
    mock_result.names = {0: "person", 1: "car", 2: "dog"}
    mock_model.return_value = mock_result

    return mock_model


@pytest.fixture
def mock_gpt4_vision_client():
    """Mock OpenAI GPT-4 Vision client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a test image description"
    mock_response.usage.total_tokens = 150
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_model_factory():
    """Mock ModelFactory."""
    with patch('modules.image_recognition.models.ModelFactory') as mock:
        mock_wrapper = MagicMock()
        mock_wrapper.load_model.return_value = True
        mock_wrapper.is_loaded = True
        mock_wrapper.predict.return_value = {
            'predictions': [
                {'class_id': '1', 'label': 'cat', 'confidence': 0.95},
                {'class_id': '2', 'label': 'dog', 'confidence': 0.85}
            ],
            'processing_time_ms': 100.5,
            'model_name': 'test_model'
        }
        mock.create_model.return_value = mock_wrapper
        yield mock


# ============================================================================
# IMAGE FIXTURES
# ============================================================================

@pytest.fixture
def sample_image() -> Image.Image:
    """Create a sample PIL image for testing."""
    img = Image.new('RGB', (224, 224), color='red')
    return img


@pytest.fixture
def sample_image_array() -> np.ndarray:
    """Create a sample image as numpy array."""
    return np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)


@pytest.fixture
def sample_image_file(sample_image) -> Generator[Path, None, None]:
    """Create a temporary image file."""
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        sample_image.save(f.name, format='JPEG')
        yield Path(f.name)
    os.unlink(f.name)


@pytest.fixture
def sample_image_bytes(sample_image) -> bytes:
    """Get image as bytes."""
    img_byte_arr = io.BytesIO()
    sample_image.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()


@pytest.fixture
def sample_image_base64(sample_image_bytes) -> str:
    """Get image as base64 string."""
    return base64.b64encode(sample_image_bytes).decode('utf-8')


@pytest.fixture
def multiple_sample_images() -> List[Image.Image]:
    """Create multiple sample images."""
    images = []
    colors = ['red', 'green', 'blue', 'yellow', 'purple']
    for color in colors:
        img = Image.new('RGB', (224, 224), color=color)
        images.append(img)
    return images


@pytest.fixture
def temp_image_directory() -> Generator[Path, None, None]:
    """Create a temporary directory with sample images."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create sample images
    for i in range(5):
        img = Image.new('RGB', (224, 224), color='blue')
        img.save(temp_dir / f"test_image_{i}.jpg", format='JPEG')

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


# ============================================================================
# DATABASE MODEL FIXTURES
# ============================================================================

@pytest.fixture
def sample_user_id() -> UUID:
    """Sample user ID."""
    return uuid4()


@pytest.fixture
def sample_label(db_session: Session) -> Label:
    """Create a sample label."""
    label = Label(
        id=uuid4(),
        name="test_label",
        display_name="Test Label",
        description="A test label",
        category="test",
        color="#FF0000",
        is_active=True,
        usage_count=0,
        metadata={}
    )
    db_session.add(label)
    db_session.commit()
    db_session.refresh(label)
    return label


@pytest.fixture
def sample_recognition_model(db_session: Session, sample_user_id: UUID) -> RecognitionModel:
    """Create a sample recognition model."""
    model = RecognitionModel(
        id=uuid4(),
        name="test_model",
        display_name="Test Model",
        description="A test recognition model",
        model_type=ModelType.RESNET50,
        version="1.0.0",
        is_latest=True,
        model_path="/path/to/model",
        architecture={"layers": 50},
        input_shape=[224, 224, 3],
        output_classes=1000,
        training_accuracy=0.95,
        validation_accuracy=0.92,
        supports_classification=True,
        supports_detection=False,
        supports_segmentation=False,
        user_id=sample_user_id,
        is_public=True,
        is_pretrained=True,
        is_active=True,
        is_deployed=True,
        metadata={},
        tags=["test", "classification"]
    )
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)
    return model


@pytest.fixture
def sample_recognition_job(
    db_session: Session,
    sample_user_id: UUID,
    sample_recognition_model: RecognitionModel
) -> RecognitionJob:
    """Create a sample recognition job."""
    job = RecognitionJob(
        id=uuid4(),
        name="test_job",
        description="A test recognition job",
        job_type=JobType.CLASSIFICATION,
        status=JobStatus.PENDING,
        user_id=sample_user_id,
        project_id=uuid4(),
        model_id=sample_recognition_model.id,
        model_type=ModelType.RESNET50,
        model_config={"batch_size": 32},
        batch_size=32,
        confidence_threshold=0.5,
        max_predictions=5,
        preprocessing_config={},
        total_images=10,
        processed_images=0,
        successful_images=0,
        failed_images=0,
        progress_percentage=0.0,
        results_summary={},
        metadata={},
        tags=["test"]
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture
def sample_image_model(
    db_session: Session,
    sample_recognition_job: RecognitionJob
) -> ImageModel:
    """Create a sample image model."""
    image = ImageModel(
        id=uuid4(),
        job_id=sample_recognition_job.id,
        filename="test_image.jpg",
        original_filename="test_image.jpg",
        file_path="/path/to/test_image.jpg",
        file_size=1024000,
        file_format=ImageFormat.JPEG,
        width=1920,
        height=1080,
        channels=3,
        color_mode="RGB",
        quality_score=0.95,
        is_blurry=False,
        is_noisy=False,
        brightness=0.5,
        contrast=0.6,
        status="pending",
        processed=False,
        metadata={},
        exif_data={}
    )
    db_session.add(image)
    db_session.commit()
    db_session.refresh(image)
    return image


@pytest.fixture
def sample_prediction(
    db_session: Session,
    sample_image_model: ImageModel,
    sample_label: Label
) -> Prediction:
    """Create a sample prediction."""
    prediction = Prediction(
        id=uuid4(),
        image_id=sample_image_model.id,
        label_id=sample_label.id,
        label_name=sample_label.name,
        confidence=0.95,
        score=0.95,
        bbox_x=10.0,
        bbox_y=20.0,
        bbox_width=100.0,
        bbox_height=200.0,
        attributes={},
        metadata={},
        model_name="test_model",
        model_version="1.0.0",
        rank=1
    )
    db_session.add(prediction)
    db_session.commit()
    db_session.refresh(prediction)
    return prediction


@pytest.fixture
def sample_annotation(
    db_session: Session,
    sample_image_model: ImageModel,
    sample_label: Label,
    sample_user_id: UUID
) -> Annotation:
    """Create a sample annotation."""
    annotation = Annotation(
        id=uuid4(),
        image_id=sample_image_model.id,
        label_id=sample_label.id,
        annotation_type="bbox",
        bbox_x=10.0,
        bbox_y=20.0,
        bbox_width=100.0,
        bbox_height=200.0,
        geometry=None,
        notes="Test annotation",
        attributes={},
        annotator_id=sample_user_id,
        is_verified=False,
        confidence=1.0
    )
    db_session.add(annotation)
    db_session.commit()
    db_session.refresh(annotation)
    return annotation


# ============================================================================
# API CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def api_client():
    """Create FastAPI test client."""
    from modules.image_recognition.api import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    with TestClient(app) as client:
        yield client


@pytest.fixture
def auth_headers(sample_user_id: UUID) -> Dict[str, str]:
    """Create authentication headers."""
    # In a real app, this would be a JWT token
    return {
        "Authorization": f"Bearer test_token_{sample_user_id}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    websocket = MagicMock(spec=WebSocket)
    websocket.accept = MagicMock()
    websocket.send_json = MagicMock()
    websocket.receive_json = MagicMock()
    websocket.close = MagicMock()
    return websocket


# ============================================================================
# EXTERNAL SERVICE MOCKS
# ============================================================================

@pytest.fixture
def mock_openai():
    """Mock OpenAI API."""
    with patch('openai.OpenAI') as mock:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test image description"
        mock_response.usage.total_tokens = 150
        mock_instance.chat.completions.create.return_value = mock_response
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_celery():
    """Mock Celery tasks."""
    with patch('modules.image_recognition.tasks.shared_task') as mock:
        def task_decorator(*args, **kwargs):
            def decorator(func):
                func.delay = MagicMock(return_value=MagicMock(id='test-task-id'))
                func.apply_async = MagicMock(return_value=MagicMock(id='test-task-id'))
                return func
            return decorator
        mock.side_effect = task_decorator
        yield mock


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock_client = MagicMock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = True
    mock_client.exists.return_value = False
    return mock_client


@pytest.fixture
def mock_s3():
    """Mock AWS S3 client."""
    with patch('boto3.client') as mock:
        s3_client = MagicMock()
        s3_client.upload_file.return_value = None
        s3_client.download_file.return_value = None
        s3_client.generate_presigned_url.return_value = "https://s3.amazonaws.com/test"
        mock.return_value = s3_client
        yield mock


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def temp_directory() -> Generator[Path, None, None]:
    """Create a temporary directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_logger():
    """Mock logger."""
    return MagicMock()


@pytest.fixture
def freezed_time():
    """Freeze time for consistent testing."""
    frozen_time = datetime(2023, 1, 1, 12, 0, 0)
    with patch('modules.image_recognition.db_models.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = frozen_time
        mock_datetime.now.return_value = frozen_time
        yield frozen_time


# ============================================================================
# PARAMETRIZE DATA
# ============================================================================

@pytest.fixture
def model_types() -> List[str]:
    """List of model types for parametrized tests."""
    return ['vgg16', 'resnet50', 'inceptionv3', 'efficientnet']


@pytest.fixture
def job_statuses() -> List[JobStatus]:
    """List of job statuses for parametrized tests."""
    return [
        JobStatus.PENDING,
        JobStatus.PROCESSING,
        JobStatus.COMPLETED,
        JobStatus.FAILED,
        JobStatus.CANCELLED
    ]


@pytest.fixture
def job_types() -> List[JobType]:
    """List of job types for parametrized tests."""
    return [
        JobType.CLASSIFICATION,
        JobType.OBJECT_DETECTION,
        JobType.FACE_RECOGNITION,
        JobType.LOGO_DETECTION,
        JobType.SEGMENTATION,
        JobType.FEATURE_EXTRACTION
    ]


# ============================================================================
# CLEANUP
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_files():
    """Cleanup any temporary files after each test."""
    yield
    # Cleanup logic here if needed
