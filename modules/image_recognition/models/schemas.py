"""
<<<<<<< HEAD
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
=======
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
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
    x: float
    y: float
    width: float
    height: float


class DetectedObjectResponse(BaseModel):
<<<<<<< HEAD
    id: int
    label: str
    confidence: float
    bbox: Optional[BoundingBox] = None
    category: Optional[str] = None
=======
    """Detected object response"""
    name: str
    confidence: float
    bbox: Optional[BoundingBox] = None
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
    attributes: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class DetectedFaceResponse(BaseModel):
<<<<<<< HEAD
    id: int
=======
    """Detected face response"""
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
    confidence: float
    bbox: Optional[BoundingBox] = None
    age_range: Optional[Dict[str, int]] = None
    gender: Optional[str] = None
    emotions: Optional[Dict[str, float]] = None
<<<<<<< HEAD
    has_smile: Optional[bool] = None
    has_eyeglasses: Optional[bool] = None
    has_sunglasses: Optional[bool] = None
    has_beard: Optional[bool] = None
    pose: Optional[Dict[str, float]] = None
=======
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
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

    class Config:
        from_attributes = True


class ImageAnalysisResponse(BaseModel):
<<<<<<< HEAD
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
=======
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
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

    class Config:
        from_attributes = True


<<<<<<< HEAD
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
=======
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
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

    class Config:
        from_attributes = True


<<<<<<< HEAD
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
=======
# Statistics schemas
class AnalyticsResponse(BaseModel):
    """Analytics response"""
    total_analyses: int
    analyses_by_type: Dict[str, int]
    analyses_by_status: Dict[str, int]
    average_confidence: float
    most_detected_objects: List[Dict[str, Any]]
    most_detected_labels: List[Dict[str, Any]]
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
