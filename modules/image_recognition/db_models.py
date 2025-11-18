"""
Database Models for Image Recognition Module

SQLAlchemy ORM models for storing recognition jobs, images, predictions, labels, and models.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Enum as SQLEnum,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid
import enum


# Base class - this would typically come from core.database.base
# For now, we'll define a simplified version
try:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()
except ImportError:
    from sqlalchemy.orm import DeclarativeBase
    class Base(DeclarativeBase):
        pass


class JobStatus(str, enum.Enum):
    """Recognition job status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, enum.Enum):
    """Recognition job type."""
    CLASSIFICATION = "classification"
    OBJECT_DETECTION = "object_detection"
    FACE_RECOGNITION = "face_recognition"
    LOGO_DETECTION = "logo_detection"
    PRODUCT_DETECTION = "product_detection"
    SEGMENTATION = "segmentation"
    FEATURE_EXTRACTION = "feature_extraction"
    SIMILARITY_SEARCH = "similarity_search"
    SCENE_UNDERSTANDING = "scene_understanding"
    QUALITY_ASSESSMENT = "quality_assessment"
    CUSTOM = "custom"


class ModelType(str, enum.Enum):
    """Pre-trained model types."""
    VGG16 = "vgg16"
    RESNET50 = "resnet50"
    INCEPTIONV3 = "inceptionv3"
    EFFICIENTNET = "efficientnet"
    YOLO = "yolo"
    GPT4_VISION = "gpt4_vision"
    CUSTOM = "custom"


class ImageFormat(str, enum.Enum):
    """Supported image formats."""
    JPEG = "jpeg"
    PNG = "png"
    BMP = "bmp"
    TIFF = "tiff"
    WEBP = "webp"


class RecognitionJob(Base):
    """Image recognition job model."""

    __tablename__ = "recognition_jobs"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Job metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    job_type: Mapped[JobType] = mapped_column(SQLEnum(JobType), nullable=False, index=True)
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus),
        default=JobStatus.PENDING,
        nullable=False,
        index=True
    )

    # User and ownership
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Model configuration
    model_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recognition_models.id", ondelete="SET NULL"),
        nullable=True
    )
    model_type: Mapped[ModelType] = mapped_column(SQLEnum(ModelType), nullable=False)
    model_config: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Processing parameters
    batch_size: Mapped[int] = mapped_column(Integer, default=32)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.5)
    max_predictions: Mapped[int] = mapped_column(Integer, default=5)
    preprocessing_config: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Progress tracking
    total_images: Mapped[int] = mapped_column(Integer, default=0)
    processed_images: Mapped[int] = mapped_column(Integer, default=0)
    successful_images: Mapped[int] = mapped_column(Integer, default=0)
    failed_images: Mapped[int] = mapped_column(Integer, default=0)
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Results
    results_summary: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    images: Mapped[List["Image"]] = relationship(
        "Image",
        back_populates="job",
        cascade="all, delete-orphan"
    )
    model: Mapped[Optional["RecognitionModel"]] = relationship("RecognitionModel", back_populates="jobs")

    # Indexes
    __table_args__ = (
        Index("idx_job_user_status", "user_id", "status"),
        Index("idx_job_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<RecognitionJob(id={self.id}, name={self.name}, status={self.status})>"


class Image(Base):
    """Image model for storing image information and metadata."""

    __tablename__ = "images"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Foreign keys
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recognition_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Image information
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # in bytes
    file_format: Mapped[ImageFormat] = mapped_column(SQLEnum(ImageFormat), nullable=False)

    # Image properties
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    channels: Mapped[int] = mapped_column(Integer, default=3)
    color_mode: Mapped[str] = mapped_column(String(20), default="RGB")

    # Image quality metrics
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_blurry: Mapped[bool] = mapped_column(Boolean, default=False)
    is_noisy: Mapped[bool] = mapped_column(Boolean, default=False)
    brightness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    contrast: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Processing status
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    processing_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Feature embeddings (for similarity search)
    embedding_vector: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    exif_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    job: Mapped["RecognitionJob"] = relationship("RecognitionJob", back_populates="images")
    predictions: Mapped[List["Prediction"]] = relationship(
        "Prediction",
        back_populates="image",
        cascade="all, delete-orphan"
    )
    annotations: Mapped[List["Annotation"]] = relationship(
        "Annotation",
        back_populates="image",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_image_job_status", "job_id", "status"),
        Index("idx_image_processed", "processed"),
    )

    def __repr__(self) -> str:
        return f"<Image(id={self.id}, filename={self.filename})>"


class Prediction(Base):
    """Prediction results for images."""

    __tablename__ = "predictions"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Foreign keys
    image_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    label_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("labels.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Prediction details
    label_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)

    # Bounding box (for object detection)
    bbox_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_width: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Segmentation mask (for segmentation tasks)
    mask_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Additional attributes
    attributes: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Model information
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Ranking
    rank: Mapped[int] = mapped_column(Integer, default=1)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    image: Mapped["Image"] = relationship("Image", back_populates="predictions")
    label: Mapped[Optional["Label"]] = relationship("Label", back_populates="predictions")

    # Indexes
    __table_args__ = (
        Index("idx_prediction_image_confidence", "image_id", "confidence"),
        Index("idx_prediction_label", "label_name"),
    )

    def __repr__(self) -> str:
        return f"<Prediction(id={self.id}, label={self.label_name}, confidence={self.confidence})>"


class Label(Base):
    """Labels/categories for image classification."""

    __tablename__ = "labels"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Label information
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Hierarchical structure
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("labels.id", ondelete="SET NULL"),
        nullable=True
    )

    # Metadata
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Statistics
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    predictions: Mapped[List["Prediction"]] = relationship("Prediction", back_populates="label")
    parent: Mapped[Optional["Label"]] = relationship("Label", remote_side=[id], back_populates="children")
    children: Mapped[List["Label"]] = relationship("Label", back_populates="parent")
    annotations: Mapped[List["Annotation"]] = relationship("Annotation", back_populates="label")

    def __repr__(self) -> str:
        return f"<Label(id={self.id}, name={self.name})>"


class RecognitionModel(Base):
    """Recognition model registry."""

    __tablename__ = "recognition_models"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Model information
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_type: Mapped[ModelType] = mapped_column(SQLEnum(ModelType), nullable=False, index=True)

    # Version control
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True)

    # Model files
    model_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    weights_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    config_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Model architecture
    architecture: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    input_shape: Mapped[List[int]] = mapped_column(ARRAY(Integer), nullable=True)
    output_classes: Mapped[int] = mapped_column(Integer, nullable=True)

    # Training information
    trained_on: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    training_dataset_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    training_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    validation_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Performance metrics
    inference_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_usage_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Supported capabilities
    supports_classification: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_detection: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_segmentation: Mapped[bool] = mapped_column(Boolean, default=False)

    # User and ownership
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pretrained: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_deployed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    jobs: Mapped[List["RecognitionJob"]] = relationship("RecognitionJob", back_populates="model")

    # Constraints
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_model_name_version"),
        Index("idx_model_type_active", "model_type", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<RecognitionModel(id={self.id}, name={self.name}, version={self.version})>"


class Annotation(Base):
    """Manual annotations for training and validation."""

    __tablename__ = "annotations"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Foreign keys
    image_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    label_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("labels.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Annotation details
    annotation_type: Mapped[str] = mapped_column(String(50), nullable=False)  # bbox, polygon, mask, point

    # Bounding box
    bbox_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_width: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Polygon/mask data
    geometry: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Annotation metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attributes: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    # User information
    annotator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Quality
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    image: Mapped["Image"] = relationship("Image", back_populates="annotations")
    label: Mapped["Label"] = relationship("Label", back_populates="annotations")

    # Indexes
    __table_args__ = (
        Index("idx_annotation_image_label", "image_id", "label_id"),
        Index("idx_annotation_verified", "is_verified"),
    )

    def __repr__(self) -> str:
        return f"<Annotation(id={self.id}, type={self.annotation_type})>"


class TrainingDataset(Base):
    """Training dataset management."""

    __tablename__ = "training_datasets"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Dataset information
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dataset_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Dataset statistics
    total_images: Mapped[int] = mapped_column(Integer, default=0)
    total_annotations: Mapped[int] = mapped_column(Integer, default=0)
    num_classes: Mapped[int] = mapped_column(Integer, default=0)

    # Split ratios
    train_split: Mapped[float] = mapped_column(Float, default=0.8)
    val_split: Mapped[float] = mapped_column(Float, default=0.1)
    test_split: Mapped[float] = mapped_column(Float, default=0.1)

    # Storage
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    # User and ownership
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<TrainingDataset(id={self.id}, name={self.name})>"
