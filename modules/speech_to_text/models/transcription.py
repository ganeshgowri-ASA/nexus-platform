"""Database models for transcriptions and speaker diarization."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Enum, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class TranscriptionStatus(str, enum.Enum):
    """Transcription processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscriptionProvider(str, enum.Enum):
    """Speech-to-text service providers."""
    WHISPER = "whisper"
    GOOGLE = "google"
    AWS = "aws"


class Speaker(Base):
    """Speaker identification model."""

    __tablename__ = "speakers"

    id = Column(Integer, primary_key=True, index=True)
    transcription_id = Column(Integer, ForeignKey("transcriptions.id"))
    speaker_id = Column(String(50), nullable=False)  # e.g., "SPEAKER_00"
    name = Column(String(255))  # Optional custom name
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    transcription = relationship("Transcription", back_populates="speakers")
    segments = relationship("TranscriptionSegment", back_populates="speaker")


class Transcription(Base):
    """Main transcription model."""

    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), index=True)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000))
    file_size = Column(Integer)  # in bytes
    duration = Column(Float)  # in seconds
    language = Column(String(10))  # ISO language code
    detected_language = Column(String(10))
    provider = Column(Enum(TranscriptionProvider), default=TranscriptionProvider.WHISPER)
    status = Column(Enum(TranscriptionStatus), default=TranscriptionStatus.PENDING)
    full_text = Column(Text)
    confidence = Column(Float)

    # Processing options
    enable_diarization = Column(Boolean, default=False)
    enable_timestamps = Column(Boolean, default=True)
    max_speakers = Column(Integer)

    # Metadata
    metadata = Column(JSON)  # Additional provider-specific data
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    segments = relationship("TranscriptionSegment", back_populates="transcription", cascade="all, delete-orphan")
    speakers = relationship("Speaker", back_populates="transcription", cascade="all, delete-orphan")


class TranscriptionSegment(Base):
    """Individual transcription segments with timestamps."""

    __tablename__ = "transcription_segments"

    id = Column(Integer, primary_key=True, index=True)
    transcription_id = Column(Integer, ForeignKey("transcriptions.id"), nullable=False)
    speaker_id = Column(Integer, ForeignKey("speakers.id"))
    sequence_number = Column(Integer, nullable=False)  # Order of segment

    # Timing
    start_time = Column(Float, nullable=False)  # in seconds
    end_time = Column(Float, nullable=False)

    # Content
    text = Column(Text, nullable=False)
    confidence = Column(Float)
    language = Column(String(10))

    # Metadata
    metadata = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    transcription = relationship("Transcription", back_populates="segments")
    speaker = relationship("Speaker", back_populates="segments")
