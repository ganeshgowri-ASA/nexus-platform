"""AWS Transcribe service implementation."""

import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
import time
import uuid

from .base import BaseSpeechService, TranscriptionResult, SegmentResult

logger = logging.getLogger(__name__)


class AWSTranscribeService(BaseSpeechService):
    """AWS Transcribe speech-to-text service."""

    SUPPORTED_FORMATS = [".mp3", ".mp4", ".wav", ".flac", ".ogg", ".amr", ".webm"]

    def __init__(self, config: Dict[str, Any]):
        """Initialize AWS Transcribe service."""
        super().__init__(config)
        self.aws_access_key = config.get("aws_access_key_id")
        self.aws_secret_key = config.get("aws_secret_access_key")
        self.region = config.get("region", "us-east-1")
        self.s3_bucket = config.get("s3_bucket")
        self._transcribe_client = None
        self._s3_client = None

    def _get_clients(self):
        """Lazy load AWS clients."""
        if self._transcribe_client is None:
            try:
                import boto3

                session_params = {"region_name": self.region}
                if self.aws_access_key and self.aws_secret_key:
                    session_params.update({
                        "aws_access_key_id": self.aws_access_key,
                        "aws_secret_access_key": self.aws_secret_key,
                    })

                self._transcribe_client = boto3.client("transcribe", **session_params)
                self._s3_client = boto3.client("s3", **session_params)

            except ImportError:
                raise ImportError(
                    "boto3 not installed. Install with: pip install boto3"
                )

        return self._transcribe_client, self._s3_client

    async def transcribe_file(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        enable_diarization: bool = False,
        enable_timestamps: bool = True,
        **kwargs
    ) -> TranscriptionResult:
        """Transcribe audio file using AWS Transcribe."""
        transcribe_client, s3_client = self._get_clients()

        if not self.s3_bucket:
            raise ValueError("S3 bucket name is required for AWS Transcribe")

        # Generate unique job name
        job_name = f"transcription-{uuid.uuid4()}"
        s3_key = f"audio/{job_name}/{audio_path.name}"

        # Upload file to S3
        logger.info(f"Uploading {audio_path} to S3: s3://{self.s3_bucket}/{s3_key}")
        s3_client.upload_file(str(audio_path), self.s3_bucket, s3_key)

        # Prepare transcription job parameters
        media_uri = f"s3://{self.s3_bucket}/{s3_key}"
        media_format = self._get_media_format(audio_path)

        job_params = {
            "TranscriptionJobName": job_name,
            "Media": {"MediaFileUri": media_uri},
            "MediaFormat": media_format,
            "LanguageCode": language or "en-US",
        }

        # Enable speaker identification (diarization)
        if enable_diarization:
            max_speakers = kwargs.get("max_speakers", 10)
            job_params["Settings"] = {
                "ShowSpeakerLabels": True,
                "MaxSpeakerLabels": max_speakers,
            }

        # Start transcription job
        logger.info(f"Starting AWS Transcribe job: {job_name}")
        transcribe_client.start_transcription_job(**job_params)

        # Wait for job completion
        while True:
            status = transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            job_status = status["TranscriptionJob"]["TranscriptionJobStatus"]

            if job_status == "COMPLETED":
                logger.info(f"Transcription job {job_name} completed")
                break
            elif job_status == "FAILED":
                failure_reason = status["TranscriptionJob"].get("FailureReason", "Unknown")
                raise Exception(f"Transcription job failed: {failure_reason}")

            await asyncio.sleep(5)

        # Get transcription results
        import requests
        transcript_uri = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
        response = requests.get(transcript_uri)
        result_json = response.json()

        # Parse results
        full_text = ""
        segments = []
        speakers = {}

        # Handle speaker-labeled transcripts
        if enable_diarization and "speaker_labels" in result_json["results"]:
            speaker_labels = result_json["results"]["speaker_labels"]

            # Map speakers
            for segment in speaker_labels.get("segments", []):
                speaker_label = segment["speaker_label"]
                if speaker_label not in speakers:
                    speakers[speaker_label] = {
                        "speaker_id": speaker_label,
                        "confidence": None
                    }

            # Process items
            for item in result_json["results"]["items"]:
                if item["type"] == "pronunciation":
                    speaker_label = item.get("speaker_label")
                    segments.append(SegmentResult(
                        text=item["alternatives"][0]["content"],
                        start_time=float(item.get("start_time", 0)),
                        end_time=float(item.get("end_time", 0)),
                        confidence=float(item["alternatives"][0].get("confidence", 0)),
                        speaker_id=speaker_label,
                        language=language,
                    ))
                    full_text += item["alternatives"][0]["content"] + " "

        else:
            # Handle regular transcripts
            for item in result_json["results"]["items"]:
                if item["type"] == "pronunciation":
                    segments.append(SegmentResult(
                        text=item["alternatives"][0]["content"],
                        start_time=float(item.get("start_time", 0)),
                        end_time=float(item.get("end_time", 0)),
                        confidence=float(item["alternatives"][0].get("confidence", 0)),
                        language=language,
                    ))

            # Get full transcript
            for transcript in result_json["results"]["transcripts"]:
                full_text += transcript["transcript"] + " "

        # Cleanup S3 file (optional)
        if kwargs.get("cleanup_s3", True):
            s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)

        return TranscriptionResult(
            full_text=full_text.strip(),
            segments=segments,
            language=language,
            speakers=list(speakers.values()) if speakers else None,
            metadata={
                "provider": "aws",
                "job_name": job_name,
            }
        )

    async def transcribe_stream(
        self,
        audio_stream,
        language: Optional[str] = None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcribe audio stream using AWS Transcribe Streaming.

        Note: AWS Transcribe Streaming requires specific implementation
        with event streams and is more complex.
        """
        raise NotImplementedError(
            "Streaming transcription not fully implemented for AWS. "
            "Use file-based transcription or implement AWS streaming API."
        )

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        # AWS Transcribe supports 30+ languages
        return [
            "af-ZA", "ar-AE", "ar-SA", "da-DK", "de-CH", "de-DE", "en-AB",
            "en-AU", "en-GB", "en-IE", "en-IN", "en-US", "en-WL", "es-ES",
            "es-US", "fa-IR", "fr-CA", "fr-FR", "he-IL", "hi-IN", "id-ID",
            "it-IT", "ja-JP", "ko-KR", "ms-MY", "nl-NL", "pt-BR", "pt-PT",
            "ru-RU", "ta-IN", "te-IN", "tr-TR", "zh-CN", "zh-TW", "th-TH",
            "en-ZA", "en-NZ", "vi-VN", "sv-SE", "ab-GE", "ast-ES", "az-AZ",
            "ba-RU", "be-BY", "bn-IN", "bs-BA", "bg-BG", "ca-ES", "ckb-IQ",
            "ckb-IR", "hr-HR", "cs-CZ", "et-ET", "eu-ES", "fi-FI", "gl-ES",
            "ka-GE", "el-GR", "gu-IN", "ha-NG", "hu-HU", "hy-AM", "is-IS",
            "kab-DZ", "kn-IN", "kk-KZ", "ky-KG", "lv-LV", "lt-LT", "lg-IN",
            "mk-MK", "ml-IN", "mt-MT", "mr-IN", "mn-MN", "no-NO", "or-IN",
            "ps-AF", "pl-PL", "pa-IN", "ro-RO", "sr-RS", "si-LK", "sk-SK",
            "sl-SI", "so-SO", "su-ID", "sw-BI", "sw-KE", "sw-RW", "sw-TZ",
            "sw-UG", "tl-PH", "tt-RU", "ug-CN", "uk-UA", "uz-UZ", "wo-SN",
            "zu-ZA"
        ]

    def validate_audio_format(self, file_path: Path) -> bool:
        """Validate if audio format is supported."""
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS

    def _get_media_format(self, file_path: Path) -> str:
        """Get AWS media format from file extension."""
        suffix = file_path.suffix.lower()
        format_map = {
            ".mp3": "mp3",
            ".mp4": "mp4",
            ".wav": "wav",
            ".flac": "flac",
            ".ogg": "ogg",
            ".amr": "amr",
            ".webm": "webm",
        }
        return format_map.get(suffix, "mp3")
