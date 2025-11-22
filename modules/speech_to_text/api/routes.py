"""FastAPI routes for speech-to-text endpoints."""

import os
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from ..config.database import get_db
from ..config.settings import get_settings
from ..models.transcription import Transcription, TranscriptionStatus, TranscriptionProvider
from ..services.factory import SpeechServiceFactory
from .schemas import (
    TranscriptionRequest,
    TranscriptionResponse,
    TranscriptionListResponse,
    HealthResponse,
    ErrorResponse,
    SegmentResponse,
    SpeakerResponse,
)

settings = get_settings()
router = APIRouter(prefix="/api/v1/speech", tags=["speech-to-text"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    # Get supported languages for each provider
    supported_languages = {}
    for provider in SpeechServiceFactory.get_supported_providers():
        try:
            service = SpeechServiceFactory.create(provider, {})
            supported_languages[provider] = service.get_supported_languages()
        except Exception:
            supported_languages[provider] = []

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        supported_providers=SpeechServiceFactory.get_supported_providers(),
        supported_languages=supported_languages,
    )


@router.post("/transcribe", response_model=TranscriptionResponse, status_code=201)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language: Optional[str] = Query(None, description="Language code"),
    provider: Optional[str] = Query("whisper", description="Provider (whisper/google/aws)"),
    enable_diarization: bool = Query(False, description="Enable speaker diarization"),
    enable_timestamps: bool = Query(True, description="Enable timestamps"),
    max_speakers: Optional[int] = Query(None, description="Max speakers for diarization"),
    user_id: str = Query("default", description="User ID"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    """
    Upload and transcribe audio file.

    Supports multiple providers: Whisper (local), Google Cloud, AWS Transcribe.
    """
    # Validate file format
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.allowed_audio_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {file_ext}. "
            f"Supported: {', '.join(settings.allowed_audio_formats)}"
        )

    # Create upload directory
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded file
    file_path = upload_dir / f"{user_id}_{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Validate file size
    file_size = os.path.getsize(file_path)
    if file_size > settings.max_upload_size:
        os.remove(file_path)
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {file_size} bytes. Max: {settings.max_upload_size}"
        )

    # Create transcription record
    transcription = Transcription(
        user_id=user_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        language=language,
        provider=TranscriptionProvider(provider.lower()),
        status=TranscriptionStatus.PENDING,
        enable_diarization=enable_diarization,
        enable_timestamps=enable_timestamps,
        max_speakers=max_speakers,
    )

    db.add(transcription)
    db.commit()
    db.refresh(transcription)

    # Queue transcription task (async processing)
    from ..tasks.transcription_tasks import process_transcription_task
    background_tasks.add_task(
        process_transcription_task,
        transcription.id,
        str(file_path),
        provider,
        language,
        enable_diarization,
        enable_timestamps,
        max_speakers,
    )

    return _transcription_to_response(transcription)


@router.get("/transcriptions", response_model=TranscriptionListResponse)
async def list_transcriptions(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[TranscriptionStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset"),
    db: Session = Depends(get_db),
):
    """List transcriptions with optional filtering."""
    query = db.query(Transcription)

    if user_id:
        query = query.filter(Transcription.user_id == user_id)
    if status:
        query = query.filter(Transcription.status == status)

    total = query.count()
    items = query.order_by(Transcription.created_at.desc()).offset(offset).limit(limit).all()

    return TranscriptionListResponse(
        total=total,
        items=[_transcription_to_response(t) for t in items]
    )


@router.get("/transcriptions/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription(
    transcription_id: int,
    include_segments: bool = Query(False, description="Include segments"),
    db: Session = Depends(get_db),
):
    """Get transcription by ID."""
    transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()

    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    return _transcription_to_response(transcription, include_segments=include_segments)


@router.delete("/transcriptions/{transcription_id}", status_code=204)
async def delete_transcription(
    transcription_id: int,
    db: Session = Depends(get_db),
):
    """Delete transcription and associated file."""
    transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()

    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    # Delete file
    if transcription.file_path and os.path.exists(transcription.file_path):
        os.remove(transcription.file_path)

    # Delete record
    db.delete(transcription)
    db.commit()

    return None


@router.get("/providers", response_model=List[str])
async def list_providers():
    """List available speech-to-text providers."""
    return SpeechServiceFactory.get_supported_providers()


@router.get("/providers/{provider}/languages", response_model=List[str])
async def get_provider_languages(provider: str):
    """Get supported languages for a provider."""
    try:
        service = SpeechServiceFactory.create(provider, {})
        return service.get_supported_languages()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def _transcription_to_response(
    transcription: Transcription,
    include_segments: bool = False
) -> TranscriptionResponse:
    """Convert transcription model to response schema."""
    segments = None
    speakers = None

    if include_segments and transcription.segments:
        segments = [
            SegmentResponse(
                sequence_number=seg.sequence_number,
                text=seg.text,
                start_time=seg.start_time,
                end_time=seg.end_time,
                confidence=seg.confidence,
                speaker_id=seg.speaker.speaker_id if seg.speaker else None,
                language=seg.language,
            )
            for seg in sorted(transcription.segments, key=lambda s: s.sequence_number)
        ]

    if include_segments and transcription.speakers:
        speakers = [
            SpeakerResponse(
                speaker_id=spk.speaker_id,
                name=spk.name,
                confidence=spk.confidence,
            )
            for spk in transcription.speakers
        ]

    return TranscriptionResponse(
        id=transcription.id,
        user_id=transcription.user_id,
        filename=transcription.filename,
        status=transcription.status,
        language=transcription.language,
        provider=transcription.provider,
        full_text=transcription.full_text,
        confidence=transcription.confidence,
        duration=transcription.duration,
        enable_diarization=transcription.enable_diarization,
        segments=segments,
        speakers=speakers,
        created_at=transcription.created_at,
        updated_at=transcription.updated_at,
        completed_at=transcription.completed_at,
        error_message=transcription.error_message,
    )
