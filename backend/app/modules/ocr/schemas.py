"""OCR module Pydantic schemas"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class OCREngineEnum(str, Enum):
    """Available OCR engines"""
    TESSERACT = "tesseract"
    GOOGLE_VISION = "google_vision"
    AWS_TEXTRACT = "aws_textract"


class OCRStatusEnum(str, Enum):
    """OCR processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OCRRequest(BaseModel):
    """OCR extraction request"""
    engine: Optional[OCREngineEnum] = OCREngineEnum.TESSERACT
    detect_language: bool = True
    extract_tables: bool = True
    detect_handwriting: bool = True
    analyze_layout: bool = True


class OCRResponse(BaseModel):
    """OCR extraction response"""
    id: str
    file_name: str
    status: OCRStatusEnum
    extracted_text: Optional[str] = None
    confidence_score: Optional[float] = None
    detected_language: Optional[str] = None
    languages: Optional[List[Dict[str, Any]]] = None
    handwriting_detected: bool = False
    tables_detected: int = 0
    processing_time: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OCRDetailResponse(OCRResponse):
    """Detailed OCR response with full metadata"""
    layout_analysis: Optional[Dict[str, Any]] = None
    table_data: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class TableExtractionResponse(BaseModel):
    """Table extraction response"""
    id: str
    document_id: str
    table_index: int
    rows: int
    columns: int
    data: List[List[str]]
    confidence_score: Optional[float] = None

    class Config:
        from_attributes = True


class OCRListResponse(BaseModel):
    """List of OCR documents"""
    total: int
    items: List[OCRResponse]
    page: int = 1
    page_size: int = 10


class LanguageDetectionResponse(BaseModel):
    """Language detection response"""
    detected_language: str
    confidence: float
    all_languages: List[Dict[str, float]]
