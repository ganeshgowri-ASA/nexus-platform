"""
FastAPI routes for translation API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from .dependencies import (
    get_db,
    get_translation_service,
    get_language_detection_service,
    get_glossary_service,
    get_quality_service
)
from ..models.schemas import (
    TranslationRequest,
    TranslationResponse,
    BatchTranslationRequest,
    BatchTranslationResponse,
    LanguageDetectionRequest,
    LanguageDetectionResponse,
    GlossaryCreate,
    GlossaryResponse,
    GlossaryUpdate,
    GlossaryTermCreate,
    GlossaryTermResponse,
    TranslationJobResponse,
    TranslationStatsResponse,
    QualityScoreResponse
)
from ..services.translation_service import TranslationService
from ..services.language_detection import LanguageDetectionService
from ..services.glossary_service import GlossaryService
from ..services.quality_scoring import QualityScoringService
from ..constants import SUPPORTED_LANGUAGES, SUPPORTED_FILE_FORMATS

router = APIRouter(prefix="/api/translation", tags=["translation"])


# Translation Endpoints
@router.post("/translate", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
    db: Session = Depends(get_db),
    translation_service: TranslationService = Depends(get_translation_service)
):
    """
    Translate text from source language to target language
    """
    try:
        result = await translation_service.translate(
            text=request.text,
            source_language=request.source_language,
            target_language=request.target_language,
            provider=request.provider,
            glossary_id=request.glossary_id,
            db=db,
            enable_quality_scoring=request.enable_quality_scoring
        )

        return TranslationResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.post("/translate/batch", response_model=BatchTranslationResponse)
async def translate_batch(
    request: BatchTranslationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submit a batch translation job
    """
    from ..tasks.celery_tasks import process_batch_translation
    import uuid

    try:
        job_id = str(uuid.uuid4())

        # Create translation job
        from ..models.database import TranslationJob
        job = TranslationJob(
            job_id=job_id,
            status="pending",
            source_language=request.source_language,
            target_language=request.target_language,
            provider=request.provider or "google",
            glossary_id=request.glossary_id,
            total_items=len(request.texts)
        )
        db.add(job)
        db.commit()

        # Queue the batch translation task
        background_tasks.add_task(
            process_batch_translation,
            job_id=job_id,
            texts=request.texts,
            source_language=request.source_language,
            target_language=request.target_language,
            provider=request.provider,
            glossary_id=request.glossary_id
        )

        return BatchTranslationResponse(
            job_id=job_id,
            status="pending",
            total_items=len(request.texts),
            message="Batch translation job submitted successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit batch job: {str(e)}")


@router.get("/jobs/{job_id}", response_model=TranslationJobResponse)
async def get_translation_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get translation job status
    """
    from ..models.database import TranslationJob

    job = db.query(TranslationJob).filter(TranslationJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


# Language Detection Endpoints
@router.post("/detect-language", response_model=LanguageDetectionResponse)
async def detect_language(
    request: LanguageDetectionRequest,
    language_service: LanguageDetectionService = Depends(get_language_detection_service)
):
    """
    Detect the language of the given text
    """
    try:
        result = await language_service.detect_language(request.text)
        return LanguageDetectionResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")


@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages
    """
    return {
        "languages": [
            {"code": code, "name": name}
            for code, name in SUPPORTED_LANGUAGES.items()
        ]
    }


# Glossary Endpoints
@router.post("/glossaries", response_model=GlossaryResponse)
async def create_glossary(
    glossary: GlossaryCreate,
    db: Session = Depends(get_db),
    glossary_service: GlossaryService = Depends(get_glossary_service)
):
    """
    Create a new glossary
    """
    try:
        result = glossary_service.create_glossary(db, glossary)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create glossary: {str(e)}")


@router.get("/glossaries", response_model=List[GlossaryResponse])
async def list_glossaries(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    glossary_service: GlossaryService = Depends(get_glossary_service)
):
    """
    List all glossaries
    """
    glossaries = glossary_service.get_glossaries(
        db,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return glossaries


@router.get("/glossaries/{glossary_id}", response_model=GlossaryResponse)
async def get_glossary(
    glossary_id: int,
    db: Session = Depends(get_db),
    glossary_service: GlossaryService = Depends(get_glossary_service)
):
    """
    Get glossary by ID
    """
    glossary = glossary_service.get_glossary(db, glossary_id)
    if not glossary:
        raise HTTPException(status_code=404, detail="Glossary not found")

    return glossary


@router.put("/glossaries/{glossary_id}", response_model=GlossaryResponse)
async def update_glossary(
    glossary_id: int,
    glossary_update: GlossaryUpdate,
    db: Session = Depends(get_db),
    glossary_service: GlossaryService = Depends(get_glossary_service)
):
    """
    Update glossary
    """
    glossary = glossary_service.update_glossary(db, glossary_id, glossary_update)
    if not glossary:
        raise HTTPException(status_code=404, detail="Glossary not found")

    return glossary


@router.delete("/glossaries/{glossary_id}")
async def delete_glossary(
    glossary_id: int,
    db: Session = Depends(get_db),
    glossary_service: GlossaryService = Depends(get_glossary_service)
):
    """
    Delete glossary
    """
    success = glossary_service.delete_glossary(db, glossary_id)
    if not success:
        raise HTTPException(status_code=404, detail="Glossary not found")

    return {"message": "Glossary deleted successfully"}


@router.post("/glossaries/{glossary_id}/terms", response_model=GlossaryTermResponse)
async def add_glossary_term(
    glossary_id: int,
    term: GlossaryTermCreate,
    db: Session = Depends(get_db),
    glossary_service: GlossaryService = Depends(get_glossary_service)
):
    """
    Add term to glossary
    """
    result = glossary_service.add_term(
        db,
        glossary_id,
        term.source_term,
        term.target_term,
        term.description,
        term.case_sensitive
    )

    if not result:
        raise HTTPException(status_code=404, detail="Glossary not found")

    return result


@router.delete("/glossaries/terms/{term_id}")
async def delete_glossary_term(
    term_id: int,
    db: Session = Depends(get_db),
    glossary_service: GlossaryService = Depends(get_glossary_service)
):
    """
    Delete glossary term
    """
    success = glossary_service.delete_term(db, term_id)
    if not success:
        raise HTTPException(status_code=404, detail="Term not found")

    return {"message": "Term deleted successfully"}


# Quality Scoring Endpoints
@router.post("/quality-score", response_model=QualityScoreResponse)
async def calculate_quality_score(
    source_text: str,
    translated_text: str,
    source_language: str,
    target_language: str,
    quality_service: QualityScoringService = Depends(get_quality_service)
):
    """
    Calculate quality score for a translation
    """
    try:
        result = await quality_service.calculate_quality_score(
            source_text,
            translated_text,
            source_language,
            target_language
        )
        return QualityScoreResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quality scoring failed: {str(e)}")


# Statistics Endpoints
@router.get("/stats", response_model=TranslationStatsResponse)
async def get_translation_stats(
    db: Session = Depends(get_db),
    translation_service: TranslationService = Depends(get_translation_service)
):
    """
    Get translation statistics
    """
    try:
        stats = await translation_service.get_translation_stats(db)
        return TranslationStatsResponse(**stats)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/history", response_model=List[TranslationResponse])
async def get_translation_history(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    translation_service: TranslationService = Depends(get_translation_service)
):
    """
    Get translation history
    """
    try:
        history = await translation_service.get_translation_history(
            db,
            limit=limit,
            offset=offset
        )
        return history

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


# Document Translation Endpoints
@router.post("/translate/document")
async def translate_document(
    file: UploadFile = File(...),
    source_language: str = "auto",
    target_language: str = "en",
    provider: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Translate a document file
    """
    import os
    import tempfile
    from ..config import config

    try:
        # Validate file format
        file_ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
        if file_ext not in SUPPORTED_FILE_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Supported: {', '.join(SUPPORTED_FILE_FORMATS.keys())}"
            )

        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # For now, return success message
        # Actual document translation would be implemented based on file type
        return {
            "message": "Document translation submitted",
            "filename": file.filename,
            "source_language": source_language,
            "target_language": target_language,
            "provider": provider or "google"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document translation failed: {str(e)}")


# Health Check
@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "NEXUS Translation Module",
        "version": "1.0.0"
    }
