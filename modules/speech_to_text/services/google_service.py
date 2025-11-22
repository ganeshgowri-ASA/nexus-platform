"""Google Cloud Speech-to-Text service implementation."""

from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from .base import BaseSpeechService, TranscriptionResult, SegmentResult

logger = logging.getLogger(__name__)


class GoogleSpeechService(BaseSpeechService):
    """Google Cloud Speech-to-Text service."""

    SUPPORTED_FORMATS = [".wav", ".flac", ".mp3", ".ogg"]

    def __init__(self, config: Dict[str, Any]):
        """Initialize Google Speech service."""
        super().__init__(config)
        self.credentials_path = config.get("credentials_path")
        self.project_id = config.get("project_id")
        self._client = None

    def _get_client(self):
        """Lazy load Google Speech client."""
        if self._client is None:
            try:
                from google.cloud import speech
                import os

                if self.credentials_path:
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path

                self._client = speech.SpeechClient()
            except ImportError:
                raise ImportError(
                    "google-cloud-speech not installed. "
                    "Install with: pip install google-cloud-speech"
                )
        return self._client

    async def transcribe_file(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        enable_diarization: bool = False,
        enable_timestamps: bool = True,
        **kwargs
    ) -> TranscriptionResult:
        """Transcribe audio file using Google Speech-to-Text."""
        from google.cloud import speech

        client = self._get_client()

        # Read audio file
        with open(audio_path, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)

        # Configure recognition
        config_params = {
            "language_code": language or "en-US",
            "enable_automatic_punctuation": True,
            "enable_word_time_offsets": enable_timestamps,
        }

        # Enable speaker diarization
        if enable_diarization:
            max_speakers = kwargs.get("max_speakers", 10)
            min_speakers = kwargs.get("min_speakers", 1)
            diarization_config = speech.SpeakerDiarizationConfig(
                enable_speaker_diarization=True,
                min_speaker_count=min_speakers,
                max_speaker_count=max_speakers,
            )
            config_params["diarization_config"] = diarization_config

        # Determine encoding
        encoding = self._get_encoding(audio_path)
        if encoding:
            config_params["encoding"] = encoding

        config_params.update(kwargs)
        recognition_config = speech.RecognitionConfig(**config_params)

        # Perform transcription
        response = client.recognize(config=recognition_config, audio=audio)

        # Parse results
        full_text = ""
        segments = []
        speakers = {}

        for result in response.results:
            alternative = result.alternatives[0]
            full_text += alternative.transcript + " "

            if enable_timestamps and hasattr(alternative, "words"):
                for word_info in alternative.words:
                    # Track speakers
                    if enable_diarization and hasattr(word_info, "speaker_tag"):
                        speaker_tag = word_info.speaker_tag
                        if speaker_tag not in speakers:
                            speakers[speaker_tag] = {
                                "speaker_id": f"SPEAKER_{speaker_tag:02d}",
                                "confidence": result.alternatives[0].confidence
                            }

                    # Create segment for each word (can be grouped later)
                    segments.append(SegmentResult(
                        text=word_info.word,
                        start_time=word_info.start_time.total_seconds(),
                        end_time=word_info.end_time.total_seconds(),
                        confidence=result.alternatives[0].confidence,
                        speaker_id=f"SPEAKER_{word_info.speaker_tag:02d}" if (
                            enable_diarization and hasattr(word_info, "speaker_tag")
                        ) else None,
                        language=language,
                    ))

        return TranscriptionResult(
            full_text=full_text.strip(),
            segments=segments,
            language=language,
            confidence=response.results[0].alternatives[0].confidence if response.results else None,
            speakers=list(speakers.values()) if speakers else None,
            metadata={"provider": "google"}
        )

    async def transcribe_stream(
        self,
        audio_stream,
        language: Optional[str] = None,
        **kwargs
    ) -> TranscriptionResult:
        """Transcribe audio stream using Google Speech-to-Text streaming API."""
        from google.cloud import speech

        client = self._get_client()

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language or "en-US",
            enable_automatic_punctuation=True,
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True,
        )

        # Process stream
        requests = (
            speech.StreamingRecognizeRequest(audio_content=chunk)
            for chunk in audio_stream
        )

        responses = client.streaming_recognize(streaming_config, requests)

        # Collect results
        full_text = ""
        segments = []

        for response in responses:
            for result in response.results:
                if result.is_final:
                    alternative = result.alternatives[0]
                    full_text += alternative.transcript + " "

                    segments.append(SegmentResult(
                        text=alternative.transcript,
                        start_time=0,  # Streaming doesn't provide absolute timestamps
                        end_time=0,
                        confidence=alternative.confidence,
                        language=language,
                    ))

        return TranscriptionResult(
            full_text=full_text.strip(),
            segments=segments,
            language=language,
            metadata={"provider": "google", "streaming": True}
        )

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        # Google Cloud Speech supports 125+ languages
        return [
            "af-ZA", "am-ET", "ar-DZ", "ar-BH", "ar-EG", "ar-IQ", "ar-IL",
            "ar-JO", "ar-KW", "ar-LB", "ar-MA", "ar-OM", "ar-QA", "ar-SA",
            "ar-PS", "ar-TN", "ar-AE", "ar-YE", "hy-AM", "az-AZ", "eu-ES",
            "bn-BD", "bn-IN", "bs-BA", "bg-BG", "my-MM", "ca-ES", "yue-Hant-HK",
            "zh", "zh-CN", "zh-TW", "hr-HR", "cs-CZ", "da-DK", "nl-BE", "nl-NL",
            "en-AU", "en-CA", "en-GH", "en-HK", "en-IN", "en-IE", "en-KE",
            "en-NZ", "en-NG", "en-PK", "en-PH", "en-SG", "en-ZA", "en-TZ",
            "en-GB", "en-US", "et-EE", "fil-PH", "fi-FI", "fr-BE", "fr-CA",
            "fr-FR", "fr-CH", "gl-ES", "ka-GE", "de-AT", "de-DE", "de-CH",
            "el-GR", "gu-IN", "iw-IL", "hi-IN", "hu-HU", "is-IS", "id-ID",
            "it-IT", "it-CH", "ja-JP", "jv-ID", "kn-IN", "kk-KZ", "km-KH",
            "ko-KR", "lo-LA", "lv-LV", "lt-LT", "mk-MK", "ms-MY", "ml-IN",
            "mr-IN", "mn-MN", "ne-NP", "no-NO", "fa-IR", "pl-PL", "pt-BR",
            "pt-PT", "pa-Guru-IN", "ro-RO", "ru-RU", "sr-RS", "si-LK",
            "sk-SK", "sl-SI", "es-AR", "es-BO", "es-CL", "es-CO", "es-CR",
            "es-DO", "es-EC", "es-SV", "es-GT", "es-HN", "es-MX", "es-NI",
            "es-PA", "es-PY", "es-PE", "es-PR", "es-ES", "es-US", "es-UY",
            "es-VE", "su-ID", "sw-KE", "sw-TZ", "sv-SE", "ta-IN", "ta-MY",
            "ta-SG", "ta-LK", "te-IN", "th-TH", "tr-TR", "uk-UA", "ur-IN",
            "ur-PK", "uz-UZ", "vi-VN", "zu-ZA"
        ]

    def validate_audio_format(self, file_path: Path) -> bool:
        """Validate if audio format is supported."""
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS

    def _get_encoding(self, file_path: Path):
        """Determine audio encoding from file extension."""
        from google.cloud import speech

        suffix = file_path.suffix.lower()
        encoding_map = {
            ".wav": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            ".flac": speech.RecognitionConfig.AudioEncoding.FLAC,
            ".mp3": speech.RecognitionConfig.AudioEncoding.MP3,
            ".ogg": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        }
        return encoding_map.get(suffix)
