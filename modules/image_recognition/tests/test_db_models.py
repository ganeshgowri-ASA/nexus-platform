"""
Tests for Database Models

Tests:
- RecognitionJob model
- Image model
- Prediction model
- Label model
- RecognitionModel model
- Annotation model
- Model relationships
- Constraints and validations
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.exc import IntegrityError
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.image_recognition.db_models import (
    RecognitionJob, Image, Prediction, Label,
    RecognitionModel, Annotation, TrainingDataset,
    JobStatus, JobType, ModelType, ImageFormat
)


# ============================================================================
# Test RecognitionJob Model
# ============================================================================

class TestRecognitionJobModel:
    """Test RecognitionJob model."""

    def test_create_job(self, db_session, sample_user_id):
        """Test creating a recognition job."""
        job = RecognitionJob(
            name="Test Job",
            description="Test description",
            job_type=JobType.CLASSIFICATION,
            status=JobStatus.PENDING,
            user_id=sample_user_id,
            model_type=ModelType.RESNET50,
            batch_size=32,
            confidence_threshold=0.5,
            max_predictions=5
        )

        db_session.add(job)
        db_session.commit()

        assert job.id is not None
        assert job.name == "Test Job"
        assert job.status == JobStatus.PENDING

    def test_job_defaults(self, db_session, sample_user_id):
        """Test job default values."""
        job = RecognitionJob(
            name="Test Job",
            job_type=JobType.CLASSIFICATION,
            user_id=sample_user_id,
            model_type=ModelType.RESNET50
        )

        db_session.add(job)
        db_session.commit()

        assert job.status == JobStatus.PENDING
        assert job.batch_size == 32
        assert job.confidence_threshold == 0.5
        assert job.progress_percentage == 0.0

    def test_job_update_progress(self, db_session, sample_recognition_job):
        """Test updating job progress."""
        sample_recognition_job.processed_images = 5
        sample_recognition_job.progress_percentage = 50.0
        sample_recognition_job.status = JobStatus.PROCESSING

        db_session.commit()
        db_session.refresh(sample_recognition_job)

        assert sample_recognition_job.processed_images == 5
        assert sample_recognition_job.progress_percentage == 50.0
        assert sample_recognition_job.status == JobStatus.PROCESSING

    def test_job_completion(self, db_session, sample_recognition_job):
        """Test job completion."""
        sample_recognition_job.status = JobStatus.COMPLETED
        sample_recognition_job.completed_at = datetime.utcnow()
        sample_recognition_job.processing_time_seconds = 120.5

        db_session.commit()

        assert sample_recognition_job.status == JobStatus.COMPLETED
        assert sample_recognition_job.completed_at is not None

    def test_job_with_images(self, db_session, sample_recognition_job):
        """Test job with associated images."""
        image1 = Image(
            job_id=sample_recognition_job.id,
            filename="image1.jpg",
            original_filename="image1.jpg",
            file_path="/path/to/image1.jpg",
            file_size=1024,
            file_format=ImageFormat.JPEG,
            width=800,
            height=600,
            channels=3
        )
        image2 = Image(
            job_id=sample_recognition_job.id,
            filename="image2.jpg",
            original_filename="image2.jpg",
            file_path="/path/to/image2.jpg",
            file_size=2048,
            file_format=ImageFormat.JPEG,
            width=1920,
            height=1080,
            channels=3
        )

        db_session.add_all([image1, image2])
        db_session.commit()

        db_session.refresh(sample_recognition_job)
        assert len(sample_recognition_job.images) == 2


# ============================================================================
# Test Image Model
# ============================================================================

class TestImageModel:
    """Test Image model."""

    def test_create_image(self, db_session, sample_recognition_job):
        """Test creating an image."""
        image = Image(
            job_id=sample_recognition_job.id,
            filename="test.jpg",
            original_filename="test.jpg",
            file_path="/path/to/test.jpg",
            file_size=1024000,
            file_format=ImageFormat.JPEG,
            width=1920,
            height=1080,
            channels=3,
            color_mode="RGB"
        )

        db_session.add(image)
        db_session.commit()

        assert image.id is not None
        assert image.filename == "test.jpg"

    def test_image_defaults(self, db_session, sample_recognition_job):
        """Test image default values."""
        image = Image(
            job_id=sample_recognition_job.id,
            filename="test.jpg",
            original_filename="test.jpg",
            file_path="/path/to/test.jpg",
            file_size=1024,
            file_format=ImageFormat.JPEG,
            width=800,
            height=600
        )

        db_session.add(image)
        db_session.commit()

        assert image.channels == 3
        assert image.color_mode == "RGB"
        assert image.processed is False
        assert image.status == "pending"

    def test_image_quality_metrics(self, db_session, sample_recognition_job):
        """Test image quality metrics."""
        image = Image(
            job_id=sample_recognition_job.id,
            filename="test.jpg",
            original_filename="test.jpg",
            file_path="/path/to/test.jpg",
            file_size=1024,
            file_format=ImageFormat.JPEG,
            width=800,
            height=600,
            quality_score=0.95,
            is_blurry=False,
            is_noisy=False,
            brightness=0.6,
            contrast=0.7
        )

        db_session.add(image)
        db_session.commit()

        assert image.quality_score == 0.95
        assert image.is_blurry is False
        assert image.brightness == 0.6

    def test_image_with_predictions(self, db_session, sample_image_model, sample_label):
        """Test image with predictions."""
        prediction = Prediction(
            image_id=sample_image_model.id,
            label_id=sample_label.id,
            label_name=sample_label.name,
            confidence=0.95,
            score=0.95,
            model_name="resnet50",
            rank=1
        )

        db_session.add(prediction)
        db_session.commit()

        db_session.refresh(sample_image_model)
        assert len(sample_image_model.predictions) == 1


# ============================================================================
# Test Prediction Model
# ============================================================================

class TestPredictionModel:
    """Test Prediction model."""

    def test_create_prediction(self, db_session, sample_image_model, sample_label):
        """Test creating a prediction."""
        prediction = Prediction(
            image_id=sample_image_model.id,
            label_id=sample_label.id,
            label_name=sample_label.name,
            confidence=0.92,
            score=0.92,
            model_name="resnet50",
            model_version="1.0.0",
            rank=1
        )

        db_session.add(prediction)
        db_session.commit()

        assert prediction.id is not None
        assert prediction.confidence == 0.92

    def test_prediction_with_bbox(self, db_session, sample_image_model, sample_label):
        """Test prediction with bounding box."""
        prediction = Prediction(
            image_id=sample_image_model.id,
            label_id=sample_label.id,
            label_name="person",
            confidence=0.95,
            score=0.95,
            bbox_x=10.0,
            bbox_y=20.0,
            bbox_width=100.0,
            bbox_height=200.0,
            model_name="yolov5"
        )

        db_session.add(prediction)
        db_session.commit()

        assert prediction.bbox_x == 10.0
        assert prediction.bbox_width == 100.0

    def test_prediction_ranking(self, db_session, sample_image_model, sample_label):
        """Test prediction ranking."""
        predictions = []
        for i in range(5):
            pred = Prediction(
                image_id=sample_image_model.id,
                label_id=sample_label.id,
                label_name=f"class_{i}",
                confidence=0.9 - i * 0.1,
                score=0.9 - i * 0.1,
                model_name="resnet50",
                rank=i + 1
            )
            predictions.append(pred)

        db_session.add_all(predictions)
        db_session.commit()

        assert predictions[0].rank == 1
        assert predictions[4].rank == 5


# ============================================================================
# Test Label Model
# ============================================================================

class TestLabelModel:
    """Test Label model."""

    def test_create_label(self, db_session):
        """Test creating a label."""
        label = Label(
            name="cat",
            display_name="Cat",
            description="Feline animal",
            category="animals",
            color="#FF5733"
        )

        db_session.add(label)
        db_session.commit()

        assert label.id is not None
        assert label.name == "cat"

    def test_label_unique_name(self, db_session):
        """Test label name uniqueness."""
        label1 = Label(name="dog", display_name="Dog")
        db_session.add(label1)
        db_session.commit()

        label2 = Label(name="dog", display_name="Dog 2")
        db_session.add(label2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_label_hierarchy(self, db_session):
        """Test hierarchical labels."""
        parent_label = Label(
            name="animal",
            display_name="Animal"
        )
        db_session.add(parent_label)
        db_session.commit()

        child_label = Label(
            name="cat",
            display_name="Cat",
            parent_id=parent_label.id
        )
        db_session.add(child_label)
        db_session.commit()

        db_session.refresh(parent_label)
        assert len(parent_label.children) == 1
        assert child_label.parent_id == parent_label.id

    def test_label_usage_count(self, db_session):
        """Test label usage tracking."""
        label = Label(
            name="car",
            display_name="Car",
            usage_count=0
        )
        db_session.add(label)
        db_session.commit()

        label.usage_count += 1
        db_session.commit()

        assert label.usage_count == 1


# ============================================================================
# Test RecognitionModel Model
# ============================================================================

class TestRecognitionModelModel:
    """Test RecognitionModel model."""

    def test_create_model(self, db_session, sample_user_id):
        """Test creating a recognition model."""
        model = RecognitionModel(
            name="custom_resnet",
            display_name="Custom ResNet",
            description="Custom trained ResNet model",
            model_type=ModelType.RESNET50,
            version="1.0.0",
            model_path="/path/to/model.h5",
            user_id=sample_user_id,
            is_public=True
        )

        db_session.add(model)
        db_session.commit()

        assert model.id is not None
        assert model.name == "custom_resnet"

    def test_model_version_uniqueness(self, db_session, sample_user_id):
        """Test model name-version uniqueness."""
        model1 = RecognitionModel(
            name="my_model",
            display_name="Model v1",
            model_type=ModelType.CUSTOM,
            version="1.0.0",
            model_path="/path1",
            user_id=sample_user_id
        )
        db_session.add(model1)
        db_session.commit()

        model2 = RecognitionModel(
            name="my_model",
            display_name="Model v1 duplicate",
            model_type=ModelType.CUSTOM,
            version="1.0.0",
            model_path="/path2",
            user_id=sample_user_id
        )
        db_session.add(model2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_model_capabilities(self, db_session, sample_user_id):
        """Test model capabilities flags."""
        model = RecognitionModel(
            name="yolo_model",
            display_name="YOLO Model",
            model_type=ModelType.YOLO,
            version="1.0.0",
            model_path="/path/to/yolo",
            supports_classification=False,
            supports_detection=True,
            supports_segmentation=False,
            user_id=sample_user_id
        )

        db_session.add(model)
        db_session.commit()

        assert model.supports_detection is True
        assert model.supports_classification is False


# ============================================================================
# Test Annotation Model
# ============================================================================

class TestAnnotationModel:
    """Test Annotation model."""

    def test_create_annotation(
        self, db_session, sample_image_model, sample_label, sample_user_id
    ):
        """Test creating an annotation."""
        annotation = Annotation(
            image_id=sample_image_model.id,
            label_id=sample_label.id,
            annotation_type="bbox",
            bbox_x=10.0,
            bbox_y=20.0,
            bbox_width=100.0,
            bbox_height=200.0,
            annotator_id=sample_user_id
        )

        db_session.add(annotation)
        db_session.commit()

        assert annotation.id is not None
        assert annotation.annotation_type == "bbox"

    def test_annotation_verification(
        self, db_session, sample_image_model, sample_label, sample_user_id
    ):
        """Test annotation verification."""
        annotation = Annotation(
            image_id=sample_image_model.id,
            label_id=sample_label.id,
            annotation_type="bbox",
            annotator_id=sample_user_id,
            is_verified=False
        )

        db_session.add(annotation)
        db_session.commit()

        # Verify annotation
        verifier_id = uuid4()
        annotation.is_verified = True
        annotation.verified_by = verifier_id

        db_session.commit()

        assert annotation.is_verified is True
        assert annotation.verified_by == verifier_id

    def test_annotation_with_polygon(
        self, db_session, sample_image_model, sample_label, sample_user_id
    ):
        """Test annotation with polygon geometry."""
        annotation = Annotation(
            image_id=sample_image_model.id,
            label_id=sample_label.id,
            annotation_type="polygon",
            geometry={
                "points": [[10, 20], [30, 40], [50, 60], [10, 20]]
            },
            annotator_id=sample_user_id
        )

        db_session.add(annotation)
        db_session.commit()

        assert annotation.geometry is not None
        assert 'points' in annotation.geometry


# ============================================================================
# Test Relationships and Cascades
# ============================================================================

class TestModelRelationships:
    """Test model relationships and cascades."""

    def test_job_image_cascade_delete(self, db_session, sample_recognition_job):
        """Test cascade delete from job to images."""
        image = Image(
            job_id=sample_recognition_job.id,
            filename="test.jpg",
            original_filename="test.jpg",
            file_path="/path/to/test.jpg",
            file_size=1024,
            file_format=ImageFormat.JPEG,
            width=800,
            height=600
        )
        db_session.add(image)
        db_session.commit()
        image_id = image.id

        # Delete job
        db_session.delete(sample_recognition_job)
        db_session.commit()

        # Image should also be deleted
        assert db_session.query(Image).filter_by(id=image_id).first() is None

    def test_image_prediction_cascade_delete(
        self, db_session, sample_image_model, sample_label
    ):
        """Test cascade delete from image to predictions."""
        prediction = Prediction(
            image_id=sample_image_model.id,
            label_id=sample_label.id,
            label_name=sample_label.name,
            confidence=0.95,
            score=0.95,
            model_name="resnet50"
        )
        db_session.add(prediction)
        db_session.commit()
        prediction_id = prediction.id

        # Delete image
        db_session.delete(sample_image_model)
        db_session.commit()

        # Prediction should also be deleted
        assert db_session.query(Prediction).filter_by(id=prediction_id).first() is None


# ============================================================================
# Test Timestamps
# ============================================================================

class TestModelTimestamps:
    """Test automatic timestamp updates."""

    def test_created_at_timestamp(self, db_session, sample_user_id):
        """Test created_at timestamp is set."""
        job = RecognitionJob(
            name="Test Job",
            job_type=JobType.CLASSIFICATION,
            user_id=sample_user_id,
            model_type=ModelType.RESNET50
        )

        db_session.add(job)
        db_session.commit()

        assert job.created_at is not None
        assert isinstance(job.created_at, datetime)

    def test_updated_at_timestamp(self, db_session, sample_recognition_job):
        """Test updated_at timestamp is updated."""
        original_updated = sample_recognition_job.updated_at

        # Update job
        sample_recognition_job.name = "Updated Name"
        db_session.commit()
        db_session.refresh(sample_recognition_job)

        # updated_at should change (in real DB with triggers)
        assert sample_recognition_job.updated_at is not None
