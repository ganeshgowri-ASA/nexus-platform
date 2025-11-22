"""OpenAI Whisper speech-to-text service implementation."""

import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from .base import BaseSpeechService, TranscriptionResult, SegmentResult

logger = logging.getLogger(__name__)


class WhisperService(BaseSpeechService):
    """Whisper (OpenAI) speech-to-text service."""

    SUPPORTED_FORMATS = [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma"]

    def __init__(self, config: Dict[str, Any]):
        """Initialize Whisper service."""
        super().__init__(config)
        self.model_name = config.get("model", "base")
        self.device = config.get("device", "cpu")
        self.compute_type = config.get("compute_type", "int8")
        self._model = None

    def _load_model(self):
        """Lazy load Whisper model."""
        if self._model is None:
            try:
                import whisper
                logger.info(f"Loading Whisper model: {self.model_name}")
                self._model = whisper.load_model(
                    self.model_name,
                    device=self.device
                )
            except ImportError:
                raise ImportError(
                    "openai-whisper not installed. "
                    "Install with: pip install openai-whisper"
                )
        return self._model

    async def transcribe_file(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        enable_diarization: bool = False,
        enable_timestamps: bool = True,
        **kwargs
    ) -> TranscriptionResult:
        """Transcribe audio file using Whisper."""

        model = self._load_model()

        # Prepare options
        options = {
            "language": language,
            "task": "transcribe",
            "verbose": False,
        }
        options.update(kwargs)

        # Run transcription in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: model.transcribe(str(audio_path), **options)
        )

        # Parse segments
        segments = []
        if enable_timestamps and "segments" in result:
            for idx, seg in enumerate(result["segments"]):
                segments.append(SegmentResult(
                    text=seg["text"].strip(),
                    start_time=seg["start"],
                    end_time=seg["end"],
                    confidence=seg.get("confidence"),
                    language=seg.get("language", language),
                    metadata={"id": seg.get("id", idx)}
                ))

        # Calculate overall confidence
        confidence = None
        if segments:
            valid_confidences = [s.confidence for s in segments if s.confidence is not None]
            if valid_confidences:
                confidence = sum(valid_confidences) / len(valid_confidences)

        # Handle diarization (Note: Whisper doesn't natively support diarization)
        speakers = None
        if enable_diarization:
            logger.warning(
                "Whisper doesn't natively support speaker diarization. "
                "Consider using pyannote.audio for diarization."
            )

        return TranscriptionResult(
            full_text=result["text"],
            segments=segments,
            language=result.get("language", language),
            confidence=confidence,
            duration=None,  # Whisper doesn't return duration
            speakers=speakers,
            metadata={
                "model": self.model_name,
                "device": self.device,
            }
        )

    async def transcribe_stream(
        self,
        audio_stream,
        language: Optional[str] = None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcribe audio stream.

        Note: Whisper is designed for batch processing. For real-time streaming,
        consider using whisper-streaming or faster-whisper libraries.
        """
        raise NotImplementedError(
            "Streaming transcription not implemented for Whisper. "
            "Use file-based transcription or implement with faster-whisper."
        )

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        # Whisper supports 99 languages
        return [
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr",
            "pl", "ca", "nl", "ar", "sv", "it", "id", "hi", "fi", "vi",
            "he", "uk", "el", "ms", "cs", "ro", "da", "hu", "ta", "no",
            "th", "ur", "hr", "bg", "lt", "la", "mi", "ml", "cy", "sk",
            "te", "fa", "lv", "bn", "sr", "az", "sl", "kn", "et", "mk",
            "br", "eu", "is", "hy", "ne", "mn", "bs", "kk", "sq", "sw",
            "gl", "mr", "pa", "si", "km", "sn", "yo", "so", "af", "oc",
            "ka", "be", "tg", "sd", "gu", "am", "yi", "lo", "uz", "fo",
            "ht", "ps", "tk", "nn", "mt", "sa", "lb", "my", "bo", "tl",
            "mg", "as", "tt", "haw", "ln", "ha", "ba", "jw", "su"
        ]

    def validate_audio_format(self, file_path: Path) -> bool:
        """Validate if audio format is supported."""
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS
