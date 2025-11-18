"""Translation module Pydantic schemas"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TranslationServiceEnum(str, Enum):
    """Available translation services"""
    GOOGLE = "google"
    DEEPL = "deepl"
    ANTHROPIC = "anthropic"


class TranslationStatusEnum(str, Enum):
    """Translation processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranslationTypeEnum(str, Enum):
    """Type of translation"""
    TEXT = "text"
    DOCUMENT = "document"
    BATCH = "batch"
    REALTIME = "realtime"


class TranslationRequest(BaseModel):
    """Translation request"""
    text: str = Field(..., description="Text to translate", min_length=1, max_length=10000)
    source_language: str = Field("auto", description="Source language code (auto for detection)")
    target_language: str = Field(..., description="Target language code")
    service: Optional[TranslationServiceEnum] = TranslationServiceEnum.GOOGLE
    glossary_id: Optional[str] = None
    context: Optional[str] = Field(None, description="Additional context for translation")

    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('Text cannot be empty')
        return v.strip()


class TranslationResponse(BaseModel):
    """Translation response"""
    id: str
    source_text: str
    translated_text: Optional[str] = None
    source_language: str
    target_language: str
    detected_language: Optional[str] = None
    status: TranslationStatusEnum
    service: TranslationServiceEnum
    quality_score: Optional[float] = None
    confidence_score: Optional[float] = None
    character_count: int
    processing_time: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BatchTranslationRequest(BaseModel):
    """Batch translation request"""
    texts: List[str] = Field(..., min_length=1, max_length=100)
    source_language: str = Field("auto", description="Source language code")
    target_language: str = Field(..., description="Target language code")
    service: Optional[TranslationServiceEnum] = TranslationServiceEnum.GOOGLE
    glossary_id: Optional[str] = None


class BatchTranslationResponse(BaseModel):
    """Batch translation response"""
    id: str
    name: str
    source_language: str
    target_language: str
    status: TranslationStatusEnum
    total_items: int
    completed_items: int
    failed_items: int
    total_characters: int
    processing_time: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GlossaryRequest(BaseModel):
    """Glossary creation request"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_language: str
    target_language: str
    entries: Dict[str, str] = Field(..., description="Term to translation mapping")


class GlossaryResponse(BaseModel):
    """Glossary response"""
    id: str
    name: str
    description: Optional[str] = None
    source_language: str
    target_language: str
    entry_count: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class GlossaryDetailResponse(GlossaryResponse):
    """Detailed glossary response with entries"""
    entries: Dict[str, str]


class LanguageDetectionResponse(BaseModel):
    """Language detection response"""
    detected_language: str
    confidence: float
    all_languages: List[Dict[str, float]]


class TranslationListResponse(BaseModel):
    """List of translations"""
    total: int
    items: List[TranslationResponse]
    page: int = 1
    page_size: int = 10


class SupportedLanguagesResponse(BaseModel):
    """Supported languages response"""
    languages: List[Dict[str, str]]
    count: int
