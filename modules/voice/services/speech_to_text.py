"""Speech-to-text service with multiple provider support."""

import os
import io
import time
from typing import Dict, Optional, Tuple
from pathlib import Path
import json


class SpeechToTextService:
    """Service for converting speech to text using Google Cloud or AWS."""

    def __init__(self, provider: str = "google", config: Optional[Dict] = None):
        """
        Initialize speech-to-text service.

        Args:
            provider: Either 'google' or 'aws'
            config: Provider-specific configuration
        """
        self.provider = provider.lower()
        self.config = config or {}
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the speech recognition client based on provider."""
        if self.provider == "google":
            self._initialize_google_client()
        elif self.provider == "aws":
            self._initialize_aws_client()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _initialize_google_client(self):
        """Initialize Google Cloud Speech-to-Text client."""
        try:
            from google.cloud import speech
            self._client = speech.SpeechClient()
            self._speech = speech
        except ImportError:
            raise ImportError(
                "Google Cloud Speech library not installed. "
                "Install with: pip install google-cloud-speech"
            )

    def _initialize_aws_client(self):
        """Initialize AWS Transcribe client."""
        try:
            import boto3
            self._client = boto3.client(
                'transcribe',
                region_name=self.config.get('region', 'us-east-1'),
                aws_access_key_id=self.config.get('aws_access_key_id'),
                aws_secret_access_key=self.config.get('aws_secret_access_key')
            )
            # Also need S3 for AWS Transcribe
            self._s3_client = boto3.client(
                's3',
                region_name=self.config.get('region', 'us-east-1'),
                aws_access_key_id=self.config.get('aws_access_key_id'),
                aws_secret_access_key=self.config.get('aws_secret_access_key')
            )
        except ImportError:
            raise ImportError(
                "AWS SDK not installed. "
                "Install with: pip install boto3"
            )

    def transcribe_audio(
        self,
        audio_file: str,
        language_code: str = "en-US",
        enable_automatic_punctuation: bool = True,
        enable_profanity_filter: bool = False,
        model: str = "default"
    ) -> Dict:
        """
        Transcribe audio file to text.

        Args:
            audio_file: Path to audio file
            language_code: Language code (e.g., 'en-US', 'es-ES')
            enable_automatic_punctuation: Add punctuation automatically
            enable_profanity_filter: Filter profanity
            model: Model to use ('default', 'command_and_search', 'phone_call')

        Returns:
            Dict with transcript, confidence, and metadata
        """
        if self.provider == "google":
            return self._transcribe_google(
                audio_file, language_code, enable_automatic_punctuation,
                enable_profanity_filter, model
            )
        elif self.provider == "aws":
            return self._transcribe_aws(
                audio_file, language_code, enable_profanity_filter
            )

    def _transcribe_google(
        self,
        audio_file: str,
        language_code: str,
        enable_automatic_punctuation: bool,
        enable_profanity_filter: bool,
        model: str
    ) -> Dict:
        """Transcribe using Google Cloud Speech-to-Text."""
        # Read audio file
        with io.open(audio_file, "rb") as f:
            content = f.read()

        # Detect audio encoding
        audio_encoding = self._detect_audio_encoding(audio_file)

        audio = self._speech.RecognitionAudio(content=content)
        config = self._speech.RecognitionConfig(
            encoding=audio_encoding,
            sample_rate_hertz=16000,
            language_code=language_code,
            enable_automatic_punctuation=enable_automatic_punctuation,
            profanity_filter=enable_profanity_filter,
            model=model,
            use_enhanced=True,
        )

        start_time = time.time()
        response = self._client.recognize(config=config, audio=audio)
        processing_time = (time.time() - start_time) * 1000

        # Process results
        if not response.results:
            return {
                "transcript": "",
                "confidence": 0.0,
                "alternatives": [],
                "words": [],
                "processing_time_ms": processing_time,
                "language_code": language_code,
                "provider": "google"
            }

        result = response.results[0]
        alternative = result.alternatives[0]

        # Extract word-level information
        words = []
        if hasattr(alternative, 'words'):
            words = [
                {
                    "word": word.word,
                    "start_time": word.start_time.total_seconds(),
                    "end_time": word.end_time.total_seconds(),
                    "confidence": word.confidence if hasattr(word, 'confidence') else None
                }
                for word in alternative.words
            ]

        return {
            "transcript": alternative.transcript,
            "confidence": alternative.confidence,
            "alternatives": [
                {
                    "transcript": alt.transcript,
                    "confidence": alt.confidence
                }
                for alt in result.alternatives[:3]
            ],
            "words": words,
            "processing_time_ms": processing_time,
            "language_code": language_code,
            "provider": "google"
        }

    def _transcribe_aws(
        self,
        audio_file: str,
        language_code: str,
        enable_profanity_filter: bool
    ) -> Dict:
        """Transcribe using AWS Transcribe."""
        import uuid

        job_name = f"nexus-transcribe-{uuid.uuid4()}"
        bucket_name = self.config.get('s3_bucket')

        if not bucket_name:
            raise ValueError("S3 bucket name required for AWS Transcribe")

        # Upload to S3
        file_name = Path(audio_file).name
        s3_key = f"transcribe/{job_name}/{file_name}"
        self._s3_client.upload_file(audio_file, bucket_name, s3_key)

        # Start transcription job
        job_uri = f"s3://{bucket_name}/{s3_key}"

        start_time = time.time()
        self._client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': job_uri},
            MediaFormat=self._get_media_format(audio_file),
            LanguageCode=language_code,
            Settings={
                'ShowSpeakerLabels': False,
                'VocabularyFilterMethod': 'mask' if enable_profanity_filter else 'none'
            }
        )

        # Wait for completion
        while True:
            status = self._client.get_transcription_job(TranscriptionJobName=job_name)
            job_status = status['TranscriptionJob']['TranscriptionJobStatus']

            if job_status in ['COMPLETED', 'FAILED']:
                break

            time.sleep(2)

        processing_time = (time.time() - start_time) * 1000

        if job_status == 'FAILED':
            raise Exception("Transcription job failed")

        # Get results
        transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']

        import urllib.request
        with urllib.request.urlopen(transcript_uri) as response:
            transcript_data = json.loads(response.read())

        # Clean up S3
        self._s3_client.delete_object(Bucket=bucket_name, Key=s3_key)

        results = transcript_data['results']
        transcript = results['transcripts'][0]['transcript']

        # Extract confidence and words
        items = results.get('items', [])
        words = [
            {
                "word": item['alternatives'][0]['content'],
                "start_time": float(item.get('start_time', 0)),
                "end_time": float(item.get('end_time', 0)),
                "confidence": float(item['alternatives'][0].get('confidence', 0))
            }
            for item in items if item['type'] == 'pronunciation'
        ]

        avg_confidence = sum(w['confidence'] for w in words) / len(words) if words else 0

        return {
            "transcript": transcript,
            "confidence": avg_confidence,
            "alternatives": [],
            "words": words,
            "processing_time_ms": processing_time,
            "language_code": language_code,
            "provider": "aws"
        }

    def _detect_audio_encoding(self, audio_file: str):
        """Detect audio encoding from file extension."""
        ext = Path(audio_file).suffix.lower()
        encoding_map = {
            '.flac': self._speech.RecognitionConfig.AudioEncoding.FLAC,
            '.wav': self._speech.RecognitionConfig.AudioEncoding.LINEAR16,
            '.mp3': self._speech.RecognitionConfig.AudioEncoding.MP3,
            '.ogg': self._speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        }
        return encoding_map.get(ext, self._speech.RecognitionConfig.AudioEncoding.LINEAR16)

    def _get_media_format(self, audio_file: str) -> str:
        """Get media format for AWS."""
        ext = Path(audio_file).suffix.lower()
        format_map = {
            '.mp3': 'mp3',
            '.mp4': 'mp4',
            '.wav': 'wav',
            '.flac': 'flac',
            '.ogg': 'ogg',
            '.webm': 'webm'
        }
        return format_map.get(ext, 'wav')

    def transcribe_streaming(self, audio_stream):
        """
        Transcribe audio in real-time from a stream.
        This is a placeholder for streaming functionality.
        """
        # TODO: Implement streaming transcription
        raise NotImplementedError("Streaming transcription not yet implemented")
