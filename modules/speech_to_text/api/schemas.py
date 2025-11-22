"""Pydantic schemas for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TranscriptionStatus(str, Enum):
    """Transcription status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscriptionProvider(str, Enum):
    """Provider enum."""
    WHISPER = "whisper"
    GOOGLE = "google"
    AWS = "aws"


class TranscriptionRequest(BaseModel):
    """Request schema for transcription."""
    language: Optional[str] = Field(None, description="Language code (e.g., 'en', 'es')")
    provider: Optional[TranscriptionProvider] = Field(
        TranscriptionProvider.WHISPER,
        description="Speech-to-text provider"
    )
    enable_diarization: bool = Field(False, description="Enable speaker diarization")
    enable_timestamps: bool = Field(True, description="Include timestamps")
    max_speakers: Optional[int] = Field(None, description="Maximum number of speakers")
    auto_detect_language: bool = Field(True, description="Auto-detect language")


class SegmentResponse(BaseModel):
    """Segment response schema."""
    sequence_number: int
    text: str
    start_time: float
    end_time: float
    confidence: Optional[float] = None
    speaker_id: Optional[str] = None
    language: Optional[str] = None


class SpeakerResponse(BaseModel):
    """Speaker response schema."""
    speaker_id: str
    name: Optional[str] = None
    confidence: Optional[float] = None


class TranscriptionResponse(BaseModel):
    """Response schema for transcription."""
    id: int
    user_id: str
    filename: str
    status: TranscriptionStatus
    language: Optional[str] = None
    provider: TranscriptionProvider
    full_text: Optional[str] = None
    confidence: Optional[float] = None
    duration: Optional[float] = None
    enable_diarization: bool
    segments: Optional[List[SegmentResponse]] = None
    speakers: Optional[List[SpeakerResponse]] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class TranscriptionListResponse(BaseModel):
    """Response schema for transcription list."""
    total: int
    items: List[TranscriptionResponse]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    supported_providers: List[str]
    supported_languages: Dict[str, List[str]]


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
