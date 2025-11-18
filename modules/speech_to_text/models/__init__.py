"""Database models for speech-to-text module."""

from .transcription import Transcription, TranscriptionSegment, Speaker

__all__ = ["Transcription", "TranscriptionSegment", "Speaker"]
