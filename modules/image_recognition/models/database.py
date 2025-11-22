"""
Database models for Image Recognition module
"""
from datetime import datetime
from typing import Optional, List
<<<<<<< HEAD
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, ForeignKey, Boolean, Enum
=======
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, Text, Enum
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


<<<<<<< HEAD
class AnalysisStatus(enum.Enum):
=======
class AnalysisStatus(str, enum.Enum):
    """Analysis status enumeration"""
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


<<<<<<< HEAD
class AnalysisType(enum.Enum):
=======
class AnalysisType(str, enum.Enum):
    """Analysis type enumeration"""
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
    OBJECT_DETECTION = "object_detection"
    IMAGE_CLASSIFICATION = "image_classification"
    FACE_DETECTION = "face_detection"
    SCENE_RECOGNITION = "scene_recognition"
    CUSTOM_MODEL = "custom_model"


class ImageAnalysis(Base):
<<<<<<< HEAD
    """Image analysis records"""
    __tablename__ = "image_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    image_url = Column(String(500), nullable=False)
    image_name = Column(String(255), nullable=False)
    analysis_type = Column(Enum(AnalysisType), nullable=False)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING, index=True)

    # Results
    results = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # Metadata
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    image_format = Column(String(50), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    detected_objects = relationship("DetectedObject", back_populates="analysis", cascade="all, delete-orphan")
    detected_faces = relationship("DetectedFace", back_populates="analysis", cascade="all, delete-orphan")
=======
    """Main image analysis records"""
    __tablename__ = "image_analyses"

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String(500), nullable=False)
    image_url = Column(String(1000), nullable=True)
    image_hash = Column(String(64), index=True)  # For duplicate detection

    # Analysis metadata
    analysis_type = Column(Enum(AnalysisType), nullable=False)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)
    provider = Column(String(50))  # google_vision, aws_rekognition, custom

    # Results
    results = Column(JSON)  # Store full API response
    confidence_score = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Relationships
    objects = relationship("DetectedObject", back_populates="analysis", cascade="all, delete-orphan")
    faces = relationship("DetectedFace", back_populates="analysis", cascade="all, delete-orphan")
    labels = relationship("ImageLabel", back_populates="analysis", cascade="all, delete-orphan")
    scenes = relationship("DetectedScene", back_populates="analysis", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ImageAnalysis(id={self.id}, type={self.analysis_type}, status={self.status})>"
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a


class DetectedObject(Base):
    """Detected objects in images"""
    __tablename__ = "detected_objects"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("image_analyses.id"), nullable=False)

    # Object details
<<<<<<< HEAD
    label = Column(String(255), nullable=False, index=True)
    confidence = Column(Float, nullable=False)

    # Bounding box coordinates (normalized 0-1)
    bbox_x = Column(Float, nullable=True)
    bbox_y = Column(Float, nullable=True)
    bbox_width = Column(Float, nullable=True)
    bbox_height = Column(Float, nullable=True)

    # Additional metadata
    category = Column(String(100), nullable=True)
    attributes = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis = relationship("ImageAnalysis", back_populates="detected_objects")
=======
    name = Column(String(200), nullable=False, index=True)
    confidence = Column(Float, nullable=False)

    # Bounding box coordinates (normalized 0-1)
    bbox_x = Column(Float)
    bbox_y = Column(Float)
    bbox_width = Column(Float)
    bbox_height = Column(Float)

    # Additional metadata
    attributes = Column(JSON)  # color, size, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis = relationship("ImageAnalysis", back_populates="objects")

    def __repr__(self):
        return f"<DetectedObject(name={self.name}, confidence={self.confidence:.2f})>"
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a


class DetectedFace(Base):
    """Detected faces in images"""
    __tablename__ = "detected_faces"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("image_analyses.id"), nullable=False)

<<<<<<< HEAD
    # Face details
    confidence = Column(Float, nullable=False)

    # Bounding box
    bbox_x = Column(Float, nullable=True)
    bbox_y = Column(Float, nullable=True)
    bbox_width = Column(Float, nullable=True)
    bbox_height = Column(Float, nullable=True)

    # Facial attributes
    age_range_low = Column(Integer, nullable=True)
    age_range_high = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    emotions = Column(JSON, nullable=True)  # {emotion: confidence}

    # Face features
    has_smile = Column(Boolean, nullable=True)
    has_eyeglasses = Column(Boolean, nullable=True)
    has_sunglasses = Column(Boolean, nullable=True)
    has_beard = Column(Boolean, nullable=True)

    # Pose information
    pitch = Column(Float, nullable=True)
    roll = Column(Float, nullable=True)
    yaw = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis = relationship("ImageAnalysis", back_populates="detected_faces")
=======
    # Face detection details
    confidence = Column(Float, nullable=False)

    # Bounding box
    bbox_x = Column(Float)
    bbox_y = Column(Float)
    bbox_width = Column(Float)
    bbox_height = Column(Float)

    # Face attributes
    age_range_low = Column(Integer, nullable=True)
    age_range_high = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    emotions = Column(JSON)  # {emotion: confidence}
    landmarks = Column(JSON)  # eye, nose, mouth positions

    # Face quality
    brightness = Column(Float, nullable=True)
    sharpness = Column(Float, nullable=True)

    # Additional attributes
    attributes = Column(JSON)  # smile, eyes_open, beard, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis = relationship("ImageAnalysis", back_populates="faces")

    def __repr__(self):
        return f"<DetectedFace(id={self.id}, confidence={self.confidence:.2f})>"


class ImageLabel(Base):
    """Image classification labels"""
    __tablename__ = "image_labels"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("image_analyses.id"), nullable=False)

    # Label details
    name = Column(String(200), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    category = Column(String(100), nullable=True)  # animal, vehicle, food, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis = relationship("ImageAnalysis", back_populates="labels")

    def __repr__(self):
        return f"<ImageLabel(name={self.name}, confidence={self.confidence:.2f})>"


class DetectedScene(Base):
    """Scene recognition results"""
    __tablename__ = "detected_scenes"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("image_analyses.id"), nullable=False)

    # Scene details
    scene_type = Column(String(200), nullable=False, index=True)  # beach, office, street, etc.
    confidence = Column(Float, nullable=False)

    # Scene attributes
    attributes = Column(JSON)  # indoor/outdoor, time_of_day, weather, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis = relationship("ImageAnalysis", back_populates="scenes")

    def __repr__(self):
        return f"<DetectedScene(type={self.scene_type}, confidence={self.confidence:.2f})>"
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a


class CustomModel(Base):
    """Custom trained models"""
    __tablename__ = "custom_models"

    id = Column(Integer, primary_key=True, index=True)
<<<<<<< HEAD
    user_id = Column(Integer, nullable=False, index=True)

    # Model details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    model_type = Column(String(100), nullable=False)  # classification, detection, etc.

    # Training info
    training_status = Column(String(50), default="pending")
    training_dataset_path = Column(String(500), nullable=True)
    num_classes = Column(Integer, nullable=True)
    num_training_images = Column(Integer, nullable=True)

    # Model performance
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)

    # Storage
    model_path = Column(String(500), nullable=True)
    model_version = Column(String(50), nullable=True)

    # Metadata
    config = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    trained_at = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True)


class ImageDataset(Base):
    """Image datasets for training"""
    __tablename__ = "image_datasets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Dataset details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    dataset_type = Column(String(100), nullable=False)

    # Statistics
    num_images = Column(Integer, default=0)
    num_classes = Column(Integer, nullable=True)
    total_size_bytes = Column(Integer, default=0)

    # Storage
    storage_path = Column(String(500), nullable=True)

    # Metadata
    labels = Column(JSON, nullable=True)  # List of class labels
    metadata = Column(JSON, nullable=True)
=======
    name = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Model details
    model_type = Column(String(100))  # classification, detection, segmentation
    model_path = Column(String(500), nullable=False)
    model_version = Column(String(50))

    # Training info
    training_dataset_size = Column(Integer)
    training_accuracy = Column(Float)
    training_completed_at = Column(DateTime, nullable=True)

    # Model metadata
    input_shape = Column(JSON)  # [height, width, channels]
    classes = Column(JSON)  # List of class names
    hyperparameters = Column(JSON)

    # Status
    is_active = Column(Integer, default=1)  # SQLite compatibility (use Integer instead of Boolean)
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

<<<<<<< HEAD
    is_active = Column(Boolean, default=True)
=======
    def __repr__(self):
        return f"<CustomModel(name={self.name}, type={self.model_type})>"
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
