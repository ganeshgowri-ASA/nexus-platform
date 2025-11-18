"""
Database models for Image Recognition module
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class AnalysisStatus(str, enum.Enum):
    """Analysis status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisType(str, enum.Enum):
    """Analysis type enumeration"""
    OBJECT_DETECTION = "object_detection"
    IMAGE_CLASSIFICATION = "image_classification"
    FACE_DETECTION = "face_detection"
    SCENE_RECOGNITION = "scene_recognition"
    CUSTOM_MODEL = "custom_model"


class ImageAnalysis(Base):
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


class DetectedObject(Base):
    """Detected objects in images"""
    __tablename__ = "detected_objects"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("image_analyses.id"), nullable=False)

    # Object details
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


class DetectedFace(Base):
    """Detected faces in images"""
    __tablename__ = "detected_faces"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("image_analyses.id"), nullable=False)

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


class CustomModel(Base):
    """Custom trained models"""
    __tablename__ = "custom_models"

    id = Column(Integer, primary_key=True, index=True)
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

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CustomModel(name={self.name}, type={self.model_type})>"
