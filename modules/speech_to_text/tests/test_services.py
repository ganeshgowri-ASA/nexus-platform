"""Tests for speech service implementations."""

import pytest
from pathlib import Path
from modules.speech_to_text.services.factory import SpeechServiceFactory
from modules.speech_to_text.services.whisper_service import WhisperService


class TestSpeechServiceFactory:
    """Test SpeechServiceFactory."""

    def test_get_supported_providers(self):
        """Test getting supported providers."""
        providers = SpeechServiceFactory.get_supported_providers()
        assert "whisper" in providers
        assert "google" in providers
        assert "aws" in providers

    def test_create_whisper_service(self):
        """Test creating Whisper service."""
        config = {"model": "base", "device": "cpu"}
        service = SpeechServiceFactory.create("whisper", config)
        assert isinstance(service, WhisperService)

    def test_create_invalid_provider(self):
        """Test creating service with invalid provider."""
        with pytest.raises(ValueError):
            SpeechServiceFactory.create("invalid", {})


class TestWhisperService:
    """Test WhisperService."""

    def test_get_supported_languages(self):
        """Test getting supported languages."""
        service = WhisperService({"model": "base"})
        languages = service.get_supported_languages()
        assert "en" in languages
        assert "es" in languages
        assert len(languages) > 50

    def test_validate_audio_format(self):
        """Test audio format validation."""
        service = WhisperService({"model": "base"})
        assert service.validate_audio_format(Path("test.mp3"))
        assert service.validate_audio_format(Path("test.wav"))
        assert not service.validate_audio_format(Path("test.txt"))


@pytest.mark.asyncio
class TestTranscription:
    """Test transcription functionality."""

    # Note: These tests require actual audio files and models
    # They are skipped by default

    @pytest.mark.skip(reason="Requires audio file and Whisper model")
    async def test_whisper_transcription(self, sample_audio_path):
        """Test Whisper transcription."""
        service = WhisperService({"model": "tiny", "device": "cpu"})
        result = await service.transcribe_file(
            audio_path=Path(sample_audio_path),
            language="en",
        )
        assert result.full_text
        assert result.segments
        assert result.language == "en"
