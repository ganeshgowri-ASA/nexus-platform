"""
Pydantic schemas for Image Recognition module
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AnalysisStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisTypeEnum(str, Enum):
    OBJECT_DETECTION = "object_detection"
    IMAGE_CLASSIFICATION = "image_classification"
    FACE_DETECTION = "face_detection"
    SCENE_RECOGNITION = "scene_recognition"
    CUSTOM_MODEL = "custom_model"


# Request Schemas
class ImageAnalysisRequest(BaseModel):
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    analysis_type: AnalysisTypeEnum
    user_id: int
    custom_model_id: Optional[int] = None

    class Config:
        use_enum_values = True


class CustomModelTrainingRequest(BaseModel):
    name: str
    description: Optional[str] = None
    model_type: str
    dataset_id: int
    user_id: int
    config: Optional[Dict[str, Any]] = None


# Response Schemas
class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float


class DetectedObjectResponse(BaseModel):
    id: int
    label: str
    confidence: float
    bbox: Optional[BoundingBox] = None
    category: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class DetectedFaceResponse(BaseModel):
    id: int
    confidence: float
    bbox: Optional[BoundingBox] = None
    age_range: Optional[Dict[str, int]] = None
    gender: Optional[str] = None
    emotions: Optional[Dict[str, float]] = None
    has_smile: Optional[bool] = None
    has_eyeglasses: Optional[bool] = None
    has_sunglasses: Optional[bool] = None
    has_beard: Optional[bool] = None
    pose: Optional[Dict[str, float]] = None

    class Config:
        from_attributes = True


class ImageAnalysisResponse(BaseModel):
    id: int
    user_id: int
    image_url: str
    image_name: str
    analysis_type: str
    status: str
    results: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    processing_time_ms: Optional[int] = None
    detected_objects: Optional[List[DetectedObjectResponse]] = None
    detected_faces: Optional[List[DetectedFaceResponse]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CustomModelResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    model_type: str
    training_status: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    created_at: datetime
    trained_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


class AnalyticsResponse(BaseModel):
    total_analyses: int
    analyses_by_type: Dict[str, int]
    analyses_by_status: Dict[str, int]
    average_processing_time_ms: Optional[float] = None
    total_objects_detected: int
    total_faces_detected: int
    most_detected_labels: List[Dict[str, Any]]

    class Config:
        from_attributes = True
