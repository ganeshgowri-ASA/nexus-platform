"""
Pydantic Schemas for Image Recognition Module

Request and response schemas for API validation and serialization.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, UUID4, validator, HttpUrl
from enum import Enum


# Enums
class JobStatusEnum(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobTypeEnum(str, Enum):
    """Job type enumeration."""
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


class ModelTypeEnum(str, Enum):
    """Model type enumeration."""
    VGG16 = "vgg16"
    RESNET50 = "resnet50"
    INCEPTIONV3 = "inceptionv3"
    EFFICIENTNET = "efficientnet"
    YOLO = "yolo"
    GPT4_VISION = "gpt4_vision"
    CUSTOM = "custom"


class ImageFormatEnum(str, Enum):
    """Image format enumeration."""
    JPEG = "jpeg"
    PNG = "png"
    BMP = "bmp"
    TIFF = "tiff"
    WEBP = "webp"


# Base Schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    class Config:
        from_attributes = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# Recognition Job Schemas
class RecognitionJobCreate(BaseSchema):
    """Schema for creating a recognition job."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    job_type: JobTypeEnum
    model_type: ModelTypeEnum
    model_id: Optional[UUID4] = None
    model_config: Dict[str, Any] = Field(default_factory=dict)
    batch_size: int = Field(default=32, ge=1, le=256)
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    max_predictions: int = Field(default=5, ge=1, le=100)
    preprocessing_config: Dict[str, Any] = Field(default_factory=dict)
    project_id: Optional[UUID4] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class RecognitionJobUpdate(BaseSchema):
    """Schema for updating a recognition job."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[JobStatusEnum] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class RecognitionJobResponse(BaseSchema):
    """Schema for recognition job response."""
    id: UUID4
    name: str
    description: Optional[str]
    job_type: JobTypeEnum
    status: JobStatusEnum
    user_id: UUID4
    project_id: Optional[UUID4]
    model_id: Optional[UUID4]
    model_type: ModelTypeEnum
    model_config: Dict[str, Any]
    batch_size: int
    confidence_threshold: float
    max_predictions: int
    total_images: int
    processed_images: int
    successful_images: int
    failed_images: int
    progress_percentage: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processing_time_seconds: Optional[float]
    results_summary: Dict[str, Any]
    error_message: Optional[str]
    metadata: Dict[str, Any]
    tags: List[str]
    created_at: datetime
    updated_at: datetime


class RecognitionJobList(BaseSchema):
    """Schema for list of recognition jobs."""
    jobs: List[RecognitionJobResponse]
    total: int
    page: int
    page_size: int


# Image Schemas
class ImageCreate(BaseSchema):
    """Schema for creating an image record."""
    job_id: UUID4
    filename: str
    original_filename: str
    file_path: str
    file_size: int = Field(..., ge=0)
    file_format: ImageFormatEnum
    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)
    channels: int = Field(default=3, ge=1, le=4)
    color_mode: str = Field(default="RGB")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    exif_data: Optional[Dict[str, Any]] = None


class ImageUpdate(BaseSchema):
    """Schema for updating an image."""
    status: Optional[str] = None
    processed: Optional[bool] = None
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_blurry: Optional[bool] = None
    is_noisy: Optional[bool] = None
    brightness: Optional[float] = None
    contrast: Optional[float] = None
    processing_time_ms: Optional[float] = Field(None, ge=0)
    embedding_vector: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ImageResponse(BaseSchema):
    """Schema for image response."""
    id: UUID4
    job_id: UUID4
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_format: ImageFormatEnum
    width: int
    height: int
    channels: int
    color_mode: str
    quality_score: Optional[float]
    is_blurry: bool
    is_noisy: bool
    brightness: Optional[float]
    contrast: Optional[float]
    status: str
    processed: bool
    processing_time_ms: Optional[float]
    metadata: Dict[str, Any]
    exif_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class ImageWithPredictions(ImageResponse):
    """Schema for image with predictions."""
    predictions: List["PredictionResponse"]


# Prediction Schemas
class PredictionCreate(BaseSchema):
    """Schema for creating a prediction."""
    image_id: UUID4
    label_id: Optional[UUID4] = None
    label_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    score: float
    bbox_x: Optional[float] = None
    bbox_y: Optional[float] = None
    bbox_width: Optional[float] = None
    bbox_height: Optional[float] = None
    mask_data: Optional[Dict[str, Any]] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model_name: str
    model_version: Optional[str] = None
    rank: int = Field(default=1, ge=1)


class PredictionResponse(BaseSchema):
    """Schema for prediction response."""
    id: UUID4
    image_id: UUID4
    label_id: Optional[UUID4]
    label_name: str
    confidence: float
    score: float
    bbox_x: Optional[float]
    bbox_y: Optional[float]
    bbox_width: Optional[float]
    bbox_height: Optional[float]
    mask_data: Optional[Dict[str, Any]]
    attributes: Dict[str, Any]
    metadata: Dict[str, Any]
    model_name: str
    model_version: Optional[str]
    rank: int
    created_at: datetime


class BoundingBox(BaseSchema):
    """Bounding box schema."""
    x: float = Field(..., ge=0)
    y: float = Field(..., ge=0)
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)


class DetectionResult(BaseSchema):
    """Object detection result schema."""
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BoundingBox
    attributes: Dict[str, Any] = Field(default_factory=dict)


# Label Schemas
class LabelCreate(BaseSchema):
    """Schema for creating a label."""
    name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    parent_id: Optional[UUID4] = None
    color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')
    icon: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LabelUpdate(BaseSchema):
    """Schema for updating a label."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class LabelResponse(BaseSchema):
    """Schema for label response."""
    id: UUID4
    name: str
    display_name: str
    description: Optional[str]
    category: Optional[str]
    parent_id: Optional[UUID4]
    color: Optional[str]
    icon: Optional[str]
    usage_count: int
    is_active: bool
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# Model Schemas
class RecognitionModelCreate(BaseSchema):
    """Schema for creating a recognition model."""
    name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    model_type: ModelTypeEnum
    version: str = Field(..., min_length=1, max_length=50)
    model_path: str
    weights_path: Optional[str] = None
    config_path: Optional[str] = None
    architecture: Dict[str, Any] = Field(default_factory=dict)
    input_shape: Optional[List[int]] = None
    output_classes: Optional[int] = Field(None, ge=1)
    supports_classification: bool = True
    supports_detection: bool = False
    supports_segmentation: bool = False
    is_public: bool = False
    is_pretrained: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class RecognitionModelUpdate(BaseSchema):
    """Schema for updating a recognition model."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_deployed: Optional[bool] = None
    is_latest: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class RecognitionModelResponse(BaseSchema):
    """Schema for recognition model response."""
    id: UUID4
    name: str
    display_name: str
    description: Optional[str]
    model_type: ModelTypeEnum
    version: str
    is_latest: bool
    model_path: str
    weights_path: Optional[str]
    config_path: Optional[str]
    architecture: Dict[str, Any]
    input_shape: Optional[List[int]]
    output_classes: Optional[int]
    trained_on: Optional[str]
    training_dataset_size: Optional[int]
    training_accuracy: Optional[float]
    validation_accuracy: Optional[float]
    inference_time_ms: Optional[float]
    memory_usage_mb: Optional[float]
    supports_classification: bool
    supports_detection: bool
    supports_segmentation: bool
    user_id: Optional[UUID4]
    is_public: bool
    is_pretrained: bool
    is_active: bool
    is_deployed: bool
    metadata: Dict[str, Any]
    tags: List[str]
    created_at: datetime
    updated_at: datetime


# Annotation Schemas
class AnnotationCreate(BaseSchema):
    """Schema for creating an annotation."""
    image_id: UUID4
    label_id: UUID4
    annotation_type: str = Field(..., regex=r'^(bbox|polygon|mask|point)$')
    bbox_x: Optional[float] = None
    bbox_y: Optional[float] = None
    bbox_width: Optional[float] = None
    bbox_height: Optional[float] = None
    geometry: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class AnnotationUpdate(BaseSchema):
    """Schema for updating an annotation."""
    label_id: Optional[UUID4] = None
    bbox_x: Optional[float] = None
    bbox_y: Optional[float] = None
    bbox_width: Optional[float] = None
    bbox_height: Optional[float] = None
    geometry: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    is_verified: Optional[bool] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class AnnotationResponse(BaseSchema):
    """Schema for annotation response."""
    id: UUID4
    image_id: UUID4
    label_id: UUID4
    annotation_type: str
    bbox_x: Optional[float]
    bbox_y: Optional[float]
    bbox_width: Optional[float]
    bbox_height: Optional[float]
    geometry: Optional[Dict[str, Any]]
    notes: Optional[str]
    attributes: Dict[str, Any]
    annotator_id: UUID4
    verified_by: Optional[UUID4]
    is_verified: bool
    confidence: float
    created_at: datetime
    updated_at: datetime


# Processing Request Schemas
class ClassificationRequest(BaseSchema):
    """Schema for image classification request."""
    image_url: Optional[HttpUrl] = None
    image_base64: Optional[str] = None
    model_type: ModelTypeEnum = ModelTypeEnum.RESNET50
    model_id: Optional[UUID4] = None
    top_k: int = Field(default=5, ge=1, le=100)
    confidence_threshold: float = Field(default=0.1, ge=0.0, le=1.0)
    preprocessing_config: Dict[str, Any] = Field(default_factory=dict)

    @validator('image_url', 'image_base64')
    def check_image_provided(cls, v, values):
        if not v and not values.get('image_base64') and not values.get('image_url'):
            raise ValueError('Either image_url or image_base64 must be provided')
        return v


class DetectionRequest(BaseSchema):
    """Schema for object detection request."""
    image_url: Optional[HttpUrl] = None
    image_base64: Optional[str] = None
    model_type: ModelTypeEnum = ModelTypeEnum.YOLO
    model_id: Optional[UUID4] = None
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    iou_threshold: float = Field(default=0.4, ge=0.0, le=1.0)
    max_detections: int = Field(default=100, ge=1, le=1000)
    preprocessing_config: Dict[str, Any] = Field(default_factory=dict)


class SegmentationRequest(BaseSchema):
    """Schema for image segmentation request."""
    image_url: Optional[HttpUrl] = None
    image_base64: Optional[str] = None
    model_id: Optional[UUID4] = None
    segmentation_type: str = Field(default="semantic", regex=r'^(semantic|instance)$')
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    preprocessing_config: Dict[str, Any] = Field(default_factory=dict)


class SimilaritySearchRequest(BaseSchema):
    """Schema for similarity search request."""
    image_url: Optional[HttpUrl] = None
    image_base64: Optional[str] = None
    image_id: Optional[UUID4] = None
    top_k: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    search_in_job_id: Optional[UUID4] = None


class QualityAssessmentRequest(BaseSchema):
    """Schema for quality assessment request."""
    image_url: Optional[HttpUrl] = None
    image_base64: Optional[str] = None
    image_id: Optional[UUID4] = None
    check_blur: bool = True
    check_noise: bool = True
    check_brightness: bool = True
    check_contrast: bool = True


# Response Schemas
class ClassificationResponse(BaseSchema):
    """Schema for classification response."""
    success: bool
    predictions: List[Dict[str, Any]]
    processing_time_ms: float
    model_name: str
    model_version: Optional[str]
    image_properties: Dict[str, Any]


class DetectionResponse(BaseSchema):
    """Schema for detection response."""
    success: bool
    detections: List[DetectionResult]
    num_detections: int
    processing_time_ms: float
    model_name: str
    model_version: Optional[str]
    image_properties: Dict[str, Any]


class SegmentationResponse(BaseSchema):
    """Schema for segmentation response."""
    success: bool
    segments: List[Dict[str, Any]]
    num_segments: int
    mask_url: Optional[str]
    processing_time_ms: float
    model_name: str
    image_properties: Dict[str, Any]


class SimilaritySearchResponse(BaseSchema):
    """Schema for similarity search response."""
    success: bool
    similar_images: List[Dict[str, Any]]
    processing_time_ms: float


class QualityAssessmentResponse(BaseSchema):
    """Schema for quality assessment response."""
    success: bool
    quality_score: float
    is_blurry: bool
    blur_score: Optional[float]
    is_noisy: bool
    noise_score: Optional[float]
    brightness: float
    contrast: float
    recommendations: List[str]
    image_properties: Dict[str, Any]


# Batch Processing Schemas
class BatchProcessingRequest(BaseSchema):
    """Schema for batch processing request."""
    job_id: UUID4
    image_urls: List[HttpUrl] = Field(..., min_items=1, max_items=1000)
    process_async: bool = True


class BatchProcessingResponse(BaseSchema):
    """Schema for batch processing response."""
    success: bool
    job_id: UUID4
    total_images: int
    status: JobStatusEnum
    message: str


# Training Schemas
class TrainingJobCreate(BaseSchema):
    """Schema for creating a training job."""
    model_name: str
    base_model_type: ModelTypeEnum
    dataset_id: UUID4
    training_config: Dict[str, Any]
    epochs: int = Field(default=10, ge=1, le=1000)
    batch_size: int = Field(default=32, ge=1, le=256)
    learning_rate: float = Field(default=0.001, gt=0)
    validation_split: float = Field(default=0.2, ge=0.0, le=0.5)


class TrainingJobResponse(BaseSchema):
    """Schema for training job response."""
    id: UUID4
    model_name: str
    status: str
    epoch: int
    total_epochs: int
    training_loss: Optional[float]
    validation_loss: Optional[float]
    training_accuracy: Optional[float]
    validation_accuracy: Optional[float]
    progress_percentage: float
    estimated_time_remaining_seconds: Optional[float]
    created_at: datetime
    updated_at: datetime


# Export Schemas
class ExportRequest(BaseSchema):
    """Schema for export request."""
    job_id: UUID4
    export_format: str = Field(..., regex=r'^(json|csv|excel|coco|yolo)$')
    include_images: bool = False
    include_metadata: bool = True
    filter_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class ExportResponse(BaseSchema):
    """Schema for export response."""
    success: bool
    download_url: str
    file_size: int
    format: str
    created_at: datetime
    expires_at: datetime


# Statistics Schemas
class JobStatistics(BaseSchema):
    """Schema for job statistics."""
    total_jobs: int
    pending_jobs: int
    processing_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_images: int
    total_predictions: int
    average_confidence: float
    average_processing_time_ms: float


class ModelStatistics(BaseSchema):
    """Schema for model statistics."""
    total_models: int
    active_models: int
    pretrained_models: int
    custom_models: int
    total_predictions: int
    average_inference_time_ms: float


# WebSocket Message Schemas
class WSMessage(BaseSchema):
    """WebSocket message schema."""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSJobUpdate(BaseSchema):
    """WebSocket job update schema."""
    job_id: UUID4
    status: JobStatusEnum
    progress_percentage: float
    processed_images: int
    total_images: int
    message: Optional[str] = None


# Update forward references
ImageWithPredictions.model_rebuild()
