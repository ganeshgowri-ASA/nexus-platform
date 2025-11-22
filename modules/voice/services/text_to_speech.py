"""Text-to-speech service with multiple provider support."""

import os
import io
from typing import Dict, Optional
from pathlib import Path


class TextToSpeechService:
    """Service for converting text to speech using Google Cloud or AWS."""

    def __init__(self, provider: str = "google", config: Optional[Dict] = None):
        """
        Initialize text-to-speech service.

        Args:
            provider: Either 'google' or 'aws'
            config: Provider-specific configuration
        """
        self.provider = provider.lower()
        self.config = config or {}
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the TTS client based on provider."""
        if self.provider == "google":
            self._initialize_google_client()
        elif self.provider == "aws":
            self._initialize_aws_client()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _initialize_google_client(self):
        """Initialize Google Cloud Text-to-Speech client."""
        try:
            from google.cloud import texttospeech
            self._client = texttospeech.TextToSpeechClient()
            self._tts = texttospeech
        except ImportError:
            raise ImportError(
                "Google Cloud Text-to-Speech library not installed. "
                "Install with: pip install google-cloud-texttospeech"
            )

    def _initialize_aws_client(self):
        """Initialize AWS Polly client."""
        try:
            import boto3
            self._client = boto3.client(
                'polly',
                region_name=self.config.get('region', 'us-east-1'),
                aws_access_key_id=self.config.get('aws_access_key_id'),
                aws_secret_access_key=self.config.get('aws_secret_access_key')
            )
        except ImportError:
            raise ImportError(
                "AWS SDK not installed. "
                "Install with: pip install boto3"
            )

    def synthesize_speech(
        self,
        text: str,
        output_file: str,
        voice_name: Optional[str] = None,
        language_code: str = "en-US",
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        volume_gain_db: float = 0.0,
        audio_format: str = "mp3"
    ) -> Dict:
        """
        Convert text to speech and save to file.

        Args:
            text: Text to convert to speech
            output_file: Path to save audio file
            voice_name: Voice to use (provider-specific)
            language_code: Language code (e.g., 'en-US')
            speaking_rate: Speaking rate (0.25 to 4.0)
            pitch: Pitch adjustment (-20.0 to 20.0)
            volume_gain_db: Volume gain in dB
            audio_format: Output format ('mp3', 'wav', 'ogg')

        Returns:
            Dict with synthesis metadata
        """
        if self.provider == "google":
            return self._synthesize_google(
                text, output_file, voice_name, language_code,
                speaking_rate, pitch, volume_gain_db, audio_format
            )
        elif self.provider == "aws":
            return self._synthesize_aws(
                text, output_file, voice_name, language_code,
                audio_format
            )

    def _synthesize_google(
        self,
        text: str,
        output_file: str,
        voice_name: Optional[str],
        language_code: str,
        speaking_rate: float,
        pitch: float,
        volume_gain_db: float,
        audio_format: str
    ) -> Dict:
        """Synthesize speech using Google Cloud Text-to-Speech."""
        # Set default voice if not specified
        if not voice_name:
            voice_name = self._get_default_google_voice(language_code)

        # Prepare synthesis input
        synthesis_input = self._tts.SynthesisInput(text=text)

        # Configure voice
        voice = self._tts.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name
        )

        # Configure audio
        audio_encoding = self._get_google_audio_encoding(audio_format)
        audio_config = self._tts.AudioConfig(
            audio_encoding=audio_encoding,
            speaking_rate=speaking_rate,
            pitch=pitch,
            volume_gain_db=volume_gain_db
        )

        # Perform synthesis
        response = self._client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # Save to file
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "wb") as out:
            out.write(response.audio_content)

        return {
            "output_file": output_file,
            "voice_name": voice_name,
            "language_code": language_code,
            "text_length": len(text),
            "audio_format": audio_format,
            "provider": "google",
            "speaking_rate": speaking_rate,
            "pitch": pitch
        }

    def _synthesize_aws(
        self,
        text: str,
        output_file: str,
        voice_name: Optional[str],
        language_code: str,
        audio_format: str
    ) -> Dict:
        """Synthesize speech using AWS Polly."""
        # Set default voice if not specified
        if not voice_name:
            voice_name = self._get_default_aws_voice(language_code)

        # Map format
        output_format = 'mp3' if audio_format == 'mp3' else 'ogg_vorbis' if audio_format == 'ogg' else 'pcm'

        # Synthesize
        response = self._client.synthesize_speech(
            Text=text,
            OutputFormat=output_format,
            VoiceId=voice_name,
            LanguageCode=language_code
        )

        # Save to file
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'wb') as out:
            out.write(response['AudioStream'].read())

        return {
            "output_file": output_file,
            "voice_name": voice_name,
            "language_code": language_code,
            "text_length": len(text),
            "audio_format": audio_format,
            "provider": "aws"
        }

    def _get_default_google_voice(self, language_code: str) -> str:
        """Get default Google voice for language."""
        voice_map = {
            "en-US": "en-US-Neural2-A",
            "en-GB": "en-GB-Neural2-A",
            "es-ES": "es-ES-Neural2-A",
            "fr-FR": "fr-FR-Neural2-A",
            "de-DE": "de-DE-Neural2-A",
            "it-IT": "it-IT-Neural2-A",
            "ja-JP": "ja-JP-Neural2-B",
            "ko-KR": "ko-KR-Neural2-A",
            "pt-BR": "pt-BR-Neural2-A",
            "zh-CN": "cmn-CN-Wavenet-A"
        }
        return voice_map.get(language_code, "en-US-Neural2-A")

    def _get_default_aws_voice(self, language_code: str) -> str:
        """Get default AWS Polly voice for language."""
        voice_map = {
            "en-US": "Joanna",
            "en-GB": "Emma",
            "es-ES": "Lucia",
            "fr-FR": "Celine",
            "de-DE": "Marlene",
            "it-IT": "Carla",
            "ja-JP": "Mizuki",
            "ko-KR": "Seoyeon",
            "pt-BR": "Camila",
            "zh-CN": "Zhiyu"
        }
        return voice_map.get(language_code, "Joanna")

    def _get_google_audio_encoding(self, audio_format: str):
        """Map audio format to Google encoding."""
        format_map = {
            'mp3': self._tts.AudioEncoding.MP3,
            'wav': self._tts.AudioEncoding.LINEAR16,
            'ogg': self._tts.AudioEncoding.OGG_OPUS
        }
        return format_map.get(audio_format, self._tts.AudioEncoding.MP3)

    def list_voices(self, language_code: Optional[str] = None) -> Dict:
        """
        List available voices.

        Args:
            language_code: Filter by language code

        Returns:
            Dict with available voices
        """
        if self.provider == "google":
            return self._list_google_voices(language_code)
        elif self.provider == "aws":
            return self._list_aws_voices(language_code)

    def _list_google_voices(self, language_code: Optional[str]) -> Dict:
        """List Google Cloud voices."""
        voices = self._client.list_voices(language_code=language_code)

        voice_list = [
            {
                "name": voice.name,
                "language_codes": voice.language_codes,
                "gender": self._tts.SsmlVoiceGender(voice.ssml_gender).name,
                "natural_sample_rate_hertz": voice.natural_sample_rate_hertz
            }
            for voice in voices.voices
        ]

        return {
            "provider": "google",
            "count": len(voice_list),
            "voices": voice_list
        }

    def _list_aws_voices(self, language_code: Optional[str]) -> Dict:
        """List AWS Polly voices."""
        params = {}
        if language_code:
            params['LanguageCode'] = language_code

        response = self._client.describe_voices(**params)

        voice_list = [
            {
                "name": voice['Id'],
                "language_code": voice['LanguageCode'],
                "gender": voice['Gender'],
                "supported_engines": voice.get('SupportedEngines', [])
            }
            for voice in response['Voices']
        ]

        return {
            "provider": "aws",
            "count": len(voice_list),
            "voices": voice_list
        }
