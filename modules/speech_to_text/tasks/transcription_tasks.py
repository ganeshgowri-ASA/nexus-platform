"""Celery tasks for transcription processing."""

import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from .celery_app import celery_app
from ..config.database import get_db_context
from ..config.settings import get_settings
from ..models.transcription import (
    Transcription,
    TranscriptionSegment,
    Speaker,
    TranscriptionStatus,
)
from ..services.factory import SpeechServiceFactory

logger = logging.getLogger(__name__)
settings = get_settings()


def process_transcription_task(
    transcription_id: int,
    file_path: str,
    provider: str,
    language: Optional[str],
    enable_diarization: bool,
    enable_timestamps: bool,
    max_speakers: Optional[int],
):
    """
    Process transcription task (non-Celery version for background tasks).

    This can be called directly or wrapped in a Celery task.
    """
    return _process_transcription(
        transcription_id,
        file_path,
        provider,
        language,
        enable_diarization,
        enable_timestamps,
        max_speakers,
    )


@celery_app.task(bind=True, name="transcription.process")
def process_transcription_celery_task(
    self,
    transcription_id: int,
    file_path: str,
    provider: str,
    language: Optional[str],
    enable_diarization: bool,
    enable_timestamps: bool,
    max_speakers: Optional[int],
):
    """
    Celery task for processing transcription.

    Args:
        transcription_id: Database ID of transcription
        file_path: Path to audio file
        provider: Speech service provider
        language: Language code
        enable_diarization: Enable speaker diarization
        enable_timestamps: Include timestamps
        max_speakers: Maximum speakers for diarization
    """
    return _process_transcription(
        transcription_id,
        file_path,
        provider,
        language,
        enable_diarization,
        enable_timestamps,
        max_speakers,
    )


def _process_transcription(
    transcription_id: int,
    file_path: str,
    provider: str,
    language: Optional[str],
    enable_diarization: bool,
    enable_timestamps: bool,
    max_speakers: Optional[int],
):
    """Internal function to process transcription."""
    with get_db_context() as db:
        transcription = db.query(Transcription).filter(
            Transcription.id == transcription_id
        ).first()

        if not transcription:
            logger.error(f"Transcription {transcription_id} not found")
            return

        try:
            # Update status to processing
            transcription.status = TranscriptionStatus.PROCESSING
            db.commit()

            # Create speech service
            service_config = _get_service_config(provider)
            service = SpeechServiceFactory.create(provider, service_config)

            # Perform transcription
            logger.info(f"Starting transcription {transcription_id} with {provider}")

            # Run async transcription in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    service.transcribe_file(
                        audio_path=Path(file_path),
                        language=language,
                        enable_diarization=enable_diarization,
                        enable_timestamps=enable_timestamps,
                        max_speakers=max_speakers,
                    )
                )
            finally:
                loop.close()

            # Save results to database
            transcription.full_text = result.full_text
            transcription.confidence = result.confidence
            transcription.duration = result.duration
            transcription.detected_language = result.language
            transcription.metadata = result.metadata

            # Save speakers
            if result.speakers:
                for speaker_data in result.speakers:
                    speaker = Speaker(
                        transcription_id=transcription.id,
                        speaker_id=speaker_data["speaker_id"],
                        confidence=speaker_data.get("confidence"),
                    )
                    db.add(speaker)

            # Create speaker lookup map
            speaker_map = {}
            if result.speakers:
                for speaker in transcription.speakers:
                    speaker_map[speaker.speaker_id] = speaker.id

            # Save segments
            if result.segments:
                for idx, segment in enumerate(result.segments):
                    # Find speaker database ID
                    speaker_db_id = None
                    if segment.speaker_id and segment.speaker_id in speaker_map:
                        speaker_db_id = speaker_map[segment.speaker_id]

                    seg = TranscriptionSegment(
                        transcription_id=transcription.id,
                        speaker_id=speaker_db_id,
                        sequence_number=idx,
                        start_time=segment.start_time,
                        end_time=segment.end_time,
                        text=segment.text,
                        confidence=segment.confidence,
                        language=segment.language,
                        metadata=segment.metadata,
                    )
                    db.add(seg)

            # Update status to completed
            transcription.status = TranscriptionStatus.COMPLETED
            transcription.completed_at = datetime.utcnow()

            db.commit()

            logger.info(f"Transcription {transcription_id} completed successfully")

        except Exception as e:
            logger.error(f"Transcription {transcription_id} failed: {str(e)}", exc_info=True)

            transcription.status = TranscriptionStatus.FAILED
            transcription.error_message = str(e)
            db.commit()

            raise


def _get_service_config(provider: str) -> dict:
    """Get service configuration for provider."""
    if provider == "whisper":
        return {
            "model": settings.whisper_model,
            "device": settings.whisper_device,
            "compute_type": settings.whisper_compute_type,
        }
    elif provider == "google":
        return {
            "credentials_path": settings.google_credentials_path,
            "project_id": settings.google_project_id,
        }
    elif provider == "aws":
        return {
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
            "region": settings.aws_region,
            "s3_bucket": settings.aws_s3_bucket,
        }
    else:
        return {}
