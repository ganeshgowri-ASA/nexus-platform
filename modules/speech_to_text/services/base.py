"""Base class for speech-to-text services."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class SegmentResult:
    """Individual segment of transcription."""
    text: str
    start_time: float
    end_time: float
    confidence: Optional[float] = None
    speaker_id: Optional[str] = None
    language: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TranscriptionResult:
    """Complete transcription result."""
    full_text: str
    segments: List[SegmentResult]
    language: Optional[str] = None
    confidence: Optional[float] = None
    duration: Optional[float] = None
    speakers: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseSpeechService(ABC):
    """Abstract base class for speech-to-text services."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize service with configuration."""
        self.config = config

    @abstractmethod
    async def transcribe_file(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        enable_diarization: bool = False,
        enable_timestamps: bool = True,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcribe audio file.

        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es')
            enable_diarization: Enable speaker diarization
            enable_timestamps: Include timestamps in results
            **kwargs: Additional provider-specific options

        Returns:
            TranscriptionResult with full text and segments
        """
        pass

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream,
        language: Optional[str] = None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcribe audio stream in real-time.

        Args:
            audio_stream: Audio stream/chunks
            language: Language code
            **kwargs: Additional provider-specific options

        Returns:
            TranscriptionResult
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        pass

    @abstractmethod
    def validate_audio_format(self, file_path: Path) -> bool:
        """Validate if audio format is supported."""
        pass
