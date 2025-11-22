"""
Pydantic Schemas

Request and response schemas for translation API.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class TranslationRequest(BaseModel):
    """Request schema for single translation."""

    text: str = Field(..., min_length=1, max_length=100000, description="Text to translate")
    target_language: str = Field(..., min_length=2, max_length=10, description="Target language code")
    source_language: Optional[str] = Field(None, min_length=2, max_length=10, description="Source language code")
    engine: Optional[str] = Field(None, description="Translation engine to use")
    context: Optional[str] = Field(None, max_length=1000, description="Additional context")
    tone: Optional[str] = Field(None, description="Desired tone (formal, casual, etc.)")
    use_cache: bool = Field(True, description="Whether to use caching")
    use_glossary: bool = Field(True, description="Whether to apply glossaries")

    @validator("target_language", "source_language")
    def validate_language_code(cls, v):
        """Validate language code format."""
        if v and not v.islower():
            return v.lower()
        return v


class BatchTranslationRequest(BaseModel):
    """Request schema for batch translation."""

    texts: List[str] = Field(..., min_items=1, max_items=100, description="List of texts to translate")
    target_language: str = Field(..., description="Target language code")
    source_language: Optional[str] = Field(None, description="Source language code")
    engine: Optional[str] = Field(None, description="Translation engine")


class TranslationResponse(BaseModel):
    """Response schema for translation."""

    id: int
    source_text: str
    translated_text: Optional[str]
    source_language: str
    target_language: str
    engine: str
    status: str
    quality_score: Optional[float]
    confidence_score: Optional[float]
    cached: bool
    processing_time_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class LanguageDetectionRequest(BaseModel):
    """Request schema for language detection."""

    text: str = Field(..., min_length=1, max_length=10000)
    use_ai: bool = Field(False, description="Whether to use AI-based detection")


class LanguageDetectionResponse(BaseModel):
    """Response schema for language detection."""

    language: str
    confidence: float
    language_name: str
    detector: Optional[str] = None


class GlossaryCreateRequest(BaseModel):
    """Request schema for creating glossary."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_language: str
    target_language: str
    domain: Optional[str] = None
    is_public: bool = False


class GlossaryTermRequest(BaseModel):
    """Request schema for adding glossary term."""

    source_term: str = Field(..., min_length=1, max_length=255)
    target_term: str = Field(..., min_length=1, max_length=255)
    context: Optional[str] = None
    case_sensitive: bool = False


class GlossaryResponse(BaseModel):
    """Response schema for glossary."""

    id: int
    name: str
    description: Optional[str]
    source_language: str
    target_language: str
    domain: Optional[str]
    is_public: bool
    created_at: datetime

    class Config:
        from_attributes = True


class QualityAssessmentRequest(BaseModel):
    """Request schema for quality assessment."""

    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    use_ai: bool = True


class QualityAssessmentResponse(BaseModel):
    """Response schema for quality assessment."""

    fluency_score: Optional[float]
    adequacy_score: Optional[float]
    overall_score: float
    feedback: Optional[str]


class TranslationMemorySearchRequest(BaseModel):
    """Request schema for TM search."""

    source_text: str
    source_language: str
    target_language: str
    min_similarity: float = Field(0.7, ge=0.0, le=1.0)


class TranslationMemoryResponse(BaseModel):
    """Response schema for TM match."""

    source_text: str
    target_text: str
    similarity: float
    quality_score: Optional[float]
    usage_count: int
    match_type: str


class TranslationStatisticsResponse(BaseModel):
    """Response schema for translation statistics."""

    total_translations: int
    total_users: int
    total_languages: int
    popular_language_pairs: List[Dict[str, Any]]
    average_quality_score: float
    cache_hit_rate: float


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str
    message: str
    status_code: int
    details: Optional[Dict[str, Any]] = None
