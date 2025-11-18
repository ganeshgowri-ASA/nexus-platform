"""
Pydantic schemas for Image Recognition module API
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


# Request schemas
class ImageAnalysisRequest(BaseModel):
    """Request to analyze an image"""
    image_url: Optional[str] = None
    image_path: Optional[str] = None
    analysis_type: str = Field(..., description="Type of analysis: object_detection, image_classification, face_detection, scene_recognition, custom_model")
    provider: Optional[str] = Field("google_vision", description="Provider: google_vision, aws_rekognition, custom")
    custom_model_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://example.com/image.jpg",
                "analysis_type": "object_detection",
                "provider": "google_vision"
            }
        }


class BatchAnalysisRequest(BaseModel):
    """Request to analyze multiple images"""
    images: List[str] = Field(..., description="List of image URLs or paths")
    analysis_type: str
    provider: Optional[str] = "google_vision"


# Response schemas
class BoundingBox(BaseModel):
    """Bounding box coordinates"""
    x: float
    y: float
    width: float
    height: float


class DetectedObjectResponse(BaseModel):
    """Detected object response"""
    name: str
    confidence: float
    bbox: Optional[BoundingBox] = None
    attributes: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class DetectedFaceResponse(BaseModel):
    """Detected face response"""
    confidence: float
    bbox: Optional[BoundingBox] = None
    age_range: Optional[Dict[str, int]] = None
    gender: Optional[str] = None
    emotions: Optional[Dict[str, float]] = None
    attributes: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ImageLabelResponse(BaseModel):
    """Image label response"""
    name: str
    confidence: float
    category: Optional[str] = None

    class Config:
        from_attributes = True


class DetectedSceneResponse(BaseModel):
    """Scene detection response"""
    scene_type: str
    confidence: float
    attributes: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ImageAnalysisResponse(BaseModel):
    """Image analysis response"""
    id: int
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    analysis_type: str
    status: str
    provider: str
    confidence_score: Optional[float] = None

    # Results
    objects: Optional[List[DetectedObjectResponse]] = None
    faces: Optional[List[DetectedFaceResponse]] = None
    labels: Optional[List[ImageLabelResponse]] = None
    scenes: Optional[List[DetectedSceneResponse]] = None

    # Timestamps
    created_at: datetime
    processed_at: Optional[datetime] = None

    # Error handling
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class AnalysisStatusResponse(BaseModel):
    """Analysis status response"""
    id: int
    status: str
    progress: Optional[float] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


# Custom Model schemas
class CustomModelCreate(BaseModel):
    """Create custom model"""
    name: str
    description: Optional[str] = None
    model_type: str = Field(..., description="classification, detection, segmentation")
    model_path: str
    model_version: Optional[str] = "1.0"
    classes: List[str]
    input_shape: List[int]
    training_dataset_size: Optional[int] = None
    training_accuracy: Optional[float] = None


class CustomModelResponse(BaseModel):
    """Custom model response"""
    id: int
    name: str
    description: Optional[str] = None
    model_type: str
    model_version: Optional[str] = None
    classes: List[str]
    is_active: bool
    created_at: datetime
    training_accuracy: Optional[float] = None

    class Config:
        from_attributes = True


# Statistics schemas
class AnalyticsResponse(BaseModel):
    """Analytics response"""
    total_analyses: int
    analyses_by_type: Dict[str, int]
    analyses_by_status: Dict[str, int]
    average_confidence: float
    most_detected_objects: List[Dict[str, Any]]
    most_detected_labels: List[Dict[str, Any]]
