"""
Database models for Image Recognition module
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, ForeignKey, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class AnalysisStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisType(enum.Enum):
    OBJECT_DETECTION = "object_detection"
    IMAGE_CLASSIFICATION = "image_classification"
    FACE_DETECTION = "face_detection"
    SCENE_RECOGNITION = "scene_recognition"
    CUSTOM_MODEL = "custom_model"


class ImageAnalysis(Base):
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


class DetectedObject(Base):
    """Detected objects in images"""
    __tablename__ = "detected_objects"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("image_analyses.id"), nullable=False)

    # Object details
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


class DetectedFace(Base):
    """Detected faces in images"""
    __tablename__ = "detected_faces"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("image_analyses.id"), nullable=False)

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


class CustomModel(Base):
    """Custom trained models"""
    __tablename__ = "custom_models"

    id = Column(Integer, primary_key=True, index=True)
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

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    is_active = Column(Boolean, default=True)
