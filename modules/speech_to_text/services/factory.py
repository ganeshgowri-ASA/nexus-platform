"""Factory for creating speech service instances."""

from typing import Dict, Any
from .base import BaseSpeechService
from .whisper_service import WhisperService
from .google_service import GoogleSpeechService
from .aws_service import AWSTranscribeService


class SpeechServiceFactory:
    """Factory for creating speech-to-text service instances."""

    _services = {
        "whisper": WhisperService,
        "google": GoogleSpeechService,
        "aws": AWSTranscribeService,
    }

    @classmethod
    def create(cls, provider: str, config: Dict[str, Any]) -> BaseSpeechService:
        """
        Create speech service instance.

        Args:
            provider: Service provider name (whisper, google, aws)
            config: Configuration dictionary for the service

        Returns:
            BaseSpeechService instance

        Raises:
            ValueError: If provider is not supported
        """
        service_class = cls._services.get(provider.lower())
        if not service_class:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Supported providers: {', '.join(cls._services.keys())}"
            )

        return service_class(config)

    @classmethod
    def get_supported_providers(cls) -> list:
        """Get list of supported provider names."""
        return list(cls._services.keys())
