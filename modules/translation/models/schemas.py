"""
Pydantic schemas for API request/response validation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


# Translation Schemas
class TranslationRequest(BaseModel):
    """Request schema for text translation"""

    text: str = Field(..., min_length=1, max_length=50000, description="Text to translate")
    source_language: str = Field(..., min_length=2, max_length=10, description="Source language code")
    target_language: str = Field(..., min_length=2, max_length=10, description="Target language code")
    provider: Optional[str] = Field(None, description="Translation provider (google/deepl)")
    glossary_id: Optional[int] = Field(None, description="Glossary ID to use")
    enable_quality_scoring: bool = Field(True, description="Enable quality scoring")

    @validator('text')
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty')
        return v


class TranslationResponse(BaseModel):
    """Response schema for translation"""

    id: int
    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    provider: str
    quality_score: Optional[float] = None
    character_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class BatchTranslationRequest(BaseModel):
    """Request schema for batch translation"""

    texts: List[str] = Field(..., min_items=1, max_items=1000)
    source_language: str
    target_language: str
    provider: Optional[str] = None
    glossary_id: Optional[int] = None
    enable_quality_scoring: bool = True


class BatchTranslationResponse(BaseModel):
    """Response schema for batch translation"""

    job_id: str
    status: str
    total_items: int
    message: str


# Language Detection Schemas
class LanguageDetectionRequest(BaseModel):
    """Request schema for language detection"""

    text: str = Field(..., min_length=1, max_length=10000)


class LanguageDetectionResponse(BaseModel):
    """Response schema for language detection"""

    detected_language: str
    language_name: str
    confidence: float
    alternative_languages: Optional[List[Dict[str, Any]]] = None


# Glossary Schemas
class GlossaryTermCreate(BaseModel):
    """Schema for creating a glossary term"""

    source_term: str = Field(..., min_length=1, max_length=500)
    target_term: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    case_sensitive: bool = False


class GlossaryTermResponse(BaseModel):
    """Response schema for glossary term"""

    id: int
    source_term: str
    target_term: str
    description: Optional[str] = None
    case_sensitive: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GlossaryCreate(BaseModel):
    """Schema for creating a glossary"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_language: str = Field(..., min_length=2, max_length=10)
    target_language: str = Field(..., min_length=2, max_length=10)
    terms: List[GlossaryTermCreate] = Field(default_factory=list)


class GlossaryResponse(BaseModel):
    """Response schema for glossary"""

    id: int
    name: str
    description: Optional[str] = None
    source_language: str
    target_language: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    terms: List[GlossaryTermResponse] = []

    class Config:
        from_attributes = True


class GlossaryUpdate(BaseModel):
    """Schema for updating a glossary"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


# Translation Job Schemas
class TranslationJobResponse(BaseModel):
    """Response schema for translation job"""

    id: int
    job_id: str
    status: str
    source_language: str
    target_language: str
    provider: str
    total_items: int
    completed_items: int
    failed_items: int
    progress_percentage: float
    result_file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Document Translation Schemas
class DocumentTranslationResponse(BaseModel):
    """Response schema for document translation"""

    job_id: str
    status: str
    original_filename: str
    translated_filename: Optional[str] = None
    source_language: str
    target_language: str
    provider: str
    message: str


# Quality Score Schema
class QualityScoreResponse(BaseModel):
    """Response schema for quality score"""

    score: float
    rating: str  # excellent, good, acceptable, poor
    factors: Dict[str, float]
    suggestions: List[str]


# Statistics Schema
class TranslationStatsResponse(BaseModel):
    """Response schema for translation statistics"""

    total_translations: int
    total_characters: int
    languages_used: Dict[str, int]
    providers_used: Dict[str, int]
    average_quality_score: Optional[float] = None
    translations_today: int
    translations_this_week: int
    translations_this_month: int
