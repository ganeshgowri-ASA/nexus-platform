"""
Pydantic Schemas

Request/response schemas for API validation.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class JobStatusEnum(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OCREngineEnum(str, Enum):
    """OCR engine enumeration"""
    TESSERACT = "tesseract"
    GOOGLE_VISION = "google_vision"
    AZURE = "azure"
    AWS = "aws"
    OPENAI = "openai"


# Base schemas
class OCRJobBase(BaseModel):
    """Base OCR job schema"""
    engine_type: OCREngineEnum = Field(default=OCREngineEnum.TESSERACT)
    language: str = Field(default="eng", max_length=50)
    options: Optional[Dict[str, Any]] = None


class OCRJobCreate(OCRJobBase):
    """Schema for creating OCR job"""
    file_name: str = Field(..., max_length=255)
    file_path: Optional[str] = None
    user_id: Optional[int] = None


class OCRJobUpdate(BaseModel):
    """Schema for updating OCR job"""
    status: Optional[JobStatusEnum] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None


class OCRJobResponse(OCRJobBase):
    """Schema for OCR job response"""
    id: int
    job_id: str
    user_id: Optional[int]
    status: JobStatusEnum
    file_name: str
    file_type: Optional[str]
    page_count: int
    total_confidence: float
    processing_time: Optional[float]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Document schemas
class BoundingBox(BaseModel):
    """Bounding box coordinates"""
    x: int
    y: int
    width: int
    height: int


class Word(BaseModel):
    """Word with confidence and position"""
    text: str
    confidence: float
    bbox: Optional[BoundingBox] = None


class Line(BaseModel):
    """Text line"""
    text: str
    confidence: float
    words: List[Word] = []


class TextBlockSchema(BaseModel):
    """Text block schema"""
    text: str
    confidence: float
    bbox: Optional[BoundingBox] = None
    block_type: Optional[str] = None
    font_size: Optional[float] = None
    is_bold: bool = False
    is_italic: bool = False


class PageSchema(BaseModel):
    """Page schema"""
    page_number: int
    text_content: str
    confidence: float
    image_width: Optional[int] = None
    image_height: Optional[int] = None


class DocumentSchema(BaseModel):
    """Document schema"""
    document_id: str
    file_name: str
    text_content: str
    confidence: float
    language: str
    pages: List[PageSchema] = []
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# OCR request/response schemas
class OCRRequest(BaseModel):
    """OCR processing request"""
    engine: OCREngineEnum = Field(default=OCREngineEnum.TESSERACT)
    language: str = Field(default="eng")
    preprocess: bool = Field(default=True)
    detect_layout: bool = Field(default=False)
    extract_tables: bool = Field(default=False)
    detect_handwriting: bool = Field(default=False)
    post_process: bool = Field(default=True)
    export_format: Optional[str] = None

    @validator('language')
    def validate_language(cls, v):
        if not v or len(v) > 50:
            raise ValueError('Invalid language code')
        return v


class OCRResponse(BaseModel):
    """OCR processing response"""
    job_id: str
    status: JobStatusEnum
    text: str
    confidence: float
    language: str
    page_count: int
    processing_time: Optional[float] = None
    words: List[Word] = []
    lines: List[Line] = []
    blocks: List[TextBlockSchema] = []
    metadata: Dict[str, Any] = {}
    quality_metrics: Optional[Dict[str, Any]] = None


class BatchOCRRequest(BaseModel):
    """Batch OCR request"""
    file_ids: List[str]
    engine: OCREngineEnum = Field(default=OCREngineEnum.TESSERACT)
    language: str = Field(default="eng")
    parallel: bool = Field(default=True)
    options: Optional[Dict[str, Any]] = None


class BatchOCRResponse(BaseModel):
    """Batch OCR response"""
    batch_id: str
    job_ids: List[str]
    total_files: int
    status: JobStatusEnum


# Export schemas
class ExportRequest(BaseModel):
    """Export request"""
    job_id: str
    format: str = Field(..., regex="^(pdf|word|excel|json|txt|csv)$")
    options: Optional[Dict[str, Any]] = None


class ExportResponse(BaseModel):
    """Export response"""
    job_id: str
    format: str
    file_path: str
    file_size: int
    created_at: datetime


# Quality metrics schemas
class QualityMetricsSchema(BaseModel):
    """Quality metrics schema"""
    overall_quality: float = Field(..., ge=0.0, le=1.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    image_quality: float = Field(..., ge=0.0, le=1.0)
    text_clarity: float = Field(..., ge=0.0, le=1.0)
    layout_complexity: float = Field(..., ge=0.0, le=1.0)
    estimated_accuracy: float = Field(..., ge=0.0, le=1.0)
    issues: List[str] = []


# Table extraction schemas
class TableCell(BaseModel):
    """Table cell"""
    row: int
    col: int
    text: str
    confidence: float


class TableSchema(BaseModel):
    """Table schema"""
    table_id: int
    rows: int
    cols: int
    cells: List[TableCell]
    bbox: Optional[BoundingBox] = None


# WebSocket schemas
class WSMessage(BaseModel):
    """WebSocket message"""
    type: str
    job_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSProgressUpdate(BaseModel):
    """WebSocket progress update"""
    job_id: str
    status: JobStatusEnum
    progress: float = Field(..., ge=0.0, le=100.0)
    message: str
    current_page: Optional[int] = None
    total_pages: Optional[int] = None


# Statistics schemas
class OCRStatistics(BaseModel):
    """OCR processing statistics"""
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    average_confidence: float
    average_processing_time: float
    total_pages_processed: int
    languages_processed: Dict[str, int]
    engines_used: Dict[str, int]


# Health check schema
class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    version: str
    available_engines: List[str]
    database_connected: bool
    redis_connected: bool
    celery_workers: int
