"""
Translation API Endpoints

FastAPI routes for translation operations.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from nexus.core.database import get_db
from nexus.models.user import User
from nexus.modules.translation.translator import Translator, BatchTranslator
from nexus.modules.translation.language_detection import LanguageDetector
from nexus.modules.translation.glossary import GlossaryManager
from nexus.modules.translation.quality import QualityAssessment
from nexus.modules.translation.memory import TranslationMemoryManager
from nexus.modules.translation.schemas import (
    TranslationRequest,
    TranslationResponse,
    BatchTranslationRequest,
    LanguageDetectionRequest,
    LanguageDetectionResponse,
    GlossaryCreateRequest,
    GlossaryTermRequest,
    GlossaryResponse,
    QualityAssessmentRequest,
    QualityAssessmentResponse,
    TranslationMemorySearchRequest,
    TranslationMemoryResponse,
)
from config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/translation", tags=["translation"])


# Dependency to get current user (simplified - implement proper auth)
def get_current_user(db: Session = Depends(get_db)) -> User:
    """Get current authenticated user."""
    # Simplified - implement proper JWT auth
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.post("/translate", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Translate text.

    - **text**: Text to translate
    - **target_language**: Target language code (e.g., 'es', 'fr', 'de')
    - **source_language**: Source language (auto-detect if not provided)
    - **engine**: Translation engine (google, deepl, azure, aws, openai, claude)
    """
    try:
        translator = Translator(
            db=db,
            user_id=current_user.id,
            engine=request.engine,
            use_cache=request.use_cache,
            use_glossary=request.use_glossary,
        )

        translation = translator.translate(
            text=request.text,
            target_lang=request.target_language,
            source_lang=request.source_language,
            context=request.context,
            tone=request.tone,
        )

        return TranslationResponse(
            id=translation.id,
            source_text=translation.source_text,
            translated_text=translation.target_text,
            source_language=translation.source_language,
            target_language=translation.target_language,
            engine=translation.engine.value,
            status=translation.status.value,
            quality_score=translation.quality_score,
            confidence_score=translation.confidence_score,
            cached=translation.cached,
            processing_time_ms=translation.processing_time_ms,
            created_at=translation.created_at,
        )

    except Exception as e:
        logger.error(f"Translation API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate/batch", response_model=List[TranslationResponse])
async def translate_batch(
    request: BatchTranslationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Batch translate multiple texts.

    - **texts**: List of texts to translate
    - **target_language**: Target language code
    - **source_language**: Source language (optional)
    """
    try:
        batch_translator = BatchTranslator(
            db=db,
            user_id=current_user.id,
            engine=request.engine,
        )

        translations = batch_translator.translate_batch(
            texts=request.texts,
            target_lang=request.target_language,
            source_lang=request.source_language,
        )

        return [
            TranslationResponse(
                id=t.id,
                source_text=t.source_text,
                translated_text=t.target_text,
                source_language=t.source_language,
                target_language=t.target_language,
                engine=t.engine.value,
                status=t.status.value,
                quality_score=t.quality_score,
                confidence_score=t.confidence_score,
                cached=t.cached,
                processing_time_ms=t.processing_time_ms,
                created_at=t.created_at,
            )
            for t in translations
        ]

    except Exception as e:
        logger.error(f"Batch translation API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-language", response_model=LanguageDetectionResponse)
async def detect_language(request: LanguageDetectionRequest):
    """
    Detect language of text.

    - **text**: Text to analyze
    - **use_ai**: Whether to use AI-based detection
    """
    try:
        detector = LanguageDetector()
        result = detector.detect(request.text, use_ai=request.use_ai)

        return LanguageDetectionResponse(**result)

    except Exception as e:
        logger.error(f"Language detection API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/glossary", response_model=GlossaryResponse)
async def create_glossary(
    request: GlossaryCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new glossary.

    - **name**: Glossary name
    - **source_language**: Source language code
    - **target_language**: Target language code
    - **domain**: Domain/industry (optional)
    """
    try:
        manager = GlossaryManager(db)
        glossary = manager.create_glossary(
            name=request.name,
            user_id=current_user.id,
            source_lang=request.source_language,
            target_lang=request.target_language,
            description=request.description,
            domain=request.domain,
            is_public=request.is_public,
        )

        return GlossaryResponse(
            id=glossary.id,
            name=glossary.name,
            description=glossary.description,
            source_language=glossary.source_language,
            target_language=glossary.target_language,
            domain=glossary.domain,
            is_public=glossary.is_public,
            created_at=glossary.created_at,
        )

    except Exception as e:
        logger.error(f"Glossary creation API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/glossary/{glossary_id}/terms")
async def add_glossary_term(
    glossary_id: int,
    request: GlossaryTermRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add term to glossary.

    - **source_term**: Term in source language
    - **target_term**: Term in target language
    - **context**: Usage context (optional)
    """
    try:
        manager = GlossaryManager(db)
        term = manager.add_term(
            glossary_id=glossary_id,
            source_term=request.source_term,
            target_term=request.target_term,
            context=request.context,
            case_sensitive=request.case_sensitive,
        )

        return {"id": term.id, "source_term": term.source_term, "target_term": term.target_term}

    except Exception as e:
        logger.error(f"Add glossary term API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quality/assess", response_model=QualityAssessmentResponse)
async def assess_quality(request: QualityAssessmentRequest):
    """
    Assess translation quality.

    - **source_text**: Original text
    - **translated_text**: Translated text
    - **source_language**: Source language code
    - **target_language**: Target language code
    """
    try:
        assessor = QualityAssessment()
        scores = assessor.assess(
            source_text=request.source_text,
            translated_text=request.translated_text,
            source_lang=request.source_language,
            target_lang=request.target_language,
            use_ai=request.use_ai,
        )

        return QualityAssessmentResponse(
            fluency_score=scores.get("fluency_score"),
            adequacy_score=scores.get("adequacy_score"),
            overall_score=scores.get("overall_score", 0.0),
            feedback=scores.get("feedback"),
        )

    except Exception as e:
        logger.error(f"Quality assessment API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/search", response_model=TranslationMemoryResponse)
async def search_translation_memory(
    request: TranslationMemorySearchRequest,
    db: Session = Depends(get_db),
):
    """
    Search translation memory.

    - **source_text**: Text to search for
    - **source_language**: Source language
    - **target_language**: Target language
    - **min_similarity**: Minimum similarity threshold (0-1)
    """
    try:
        tm_manager = TranslationMemoryManager(db)
        match = tm_manager.find_match(
            source_text=request.source_text,
            source_lang=request.source_language,
            target_lang=request.target_language,
            min_similarity=request.min_similarity,
        )

        if not match:
            raise HTTPException(status_code=404, detail="No matching translation found")

        return TranslationMemoryResponse(**match)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TM search API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/engines")
async def list_engines():
    """
    List available translation engines.

    Returns list of configured and available engines.
    """
    from nexus.modules.translation.engines import EngineFactory

    try:
        available = EngineFactory.get_available_engines()
        return {
            "engines": available,
            "total": len(available),
        }
    except Exception as e:
        logger.error(f"List engines API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
