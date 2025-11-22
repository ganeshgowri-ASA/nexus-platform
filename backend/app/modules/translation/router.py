"""Translation module API endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.db.session import get_db
from app.modules.translation.service import TranslationService
from app.modules.translation.schemas import (
    TranslationRequest,
    TranslationResponse,
    BatchTranslationRequest,
    BatchTranslationResponse,
    GlossaryRequest,
    GlossaryResponse,
    GlossaryDetailResponse,
    TranslationListResponse,
    SupportedLanguagesResponse,
    TranslationStatusEnum
)
from app.modules.translation.models import TranslationStatus
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/translate", response_model=TranslationResponse, status_code=status.HTTP_201_CREATED)
async def translate_text(
    request: TranslationRequest,
    user_id: Optional[str] = Query(None, description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Translate text from one language to another.

    **Supported Features:**
    - 100+ languages supported
    - Automatic language detection (set source_language to 'auto')
    - Multiple translation services (Google, Anthropic, DeepL)
    - Custom glossary support for consistent terminology
    - Context-aware translation
    - Quality scoring

    **Language Codes:**
    - Use ISO 639-1 codes (e.g., 'en' for English, 'es' for Spanish)
    - Set source_language to 'auto' for automatic detection
    - See /languages endpoint for full list of supported languages

    **Translation Services:**
    - `google`: Fast, reliable, supports 100+ languages
    - `anthropic`: High-quality, context-aware translations using Claude
    - `deepl`: Professional-grade translations (requires API key)
    """
    try:
        service = TranslationService(db)
        result = await service.translate_text(request, user_id)
        return result

    except Exception as e:
        logger.error(f"Translation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )


@router.post("/batch", response_model=BatchTranslationResponse, status_code=status.HTTP_201_CREATED)
async def batch_translate(
    request: BatchTranslationRequest,
    user_id: Optional[str] = Query(None, description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Translate multiple texts in a single batch operation.

    **Features:**
    - Process up to 100 texts in one request
    - Parallel processing for faster results
    - Consistent glossary application across all texts
    - Batch progress tracking
    - Individual error handling per text

    **Use Cases:**
    - Translate product descriptions
    - Localize UI strings
    - Process document collections
    - Bulk content translation
    """
    try:
        service = TranslationService(db)
        result = await service.batch_translate(request, user_id)
        return result

    except Exception as e:
        logger.error(f"Batch translation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch translation failed: {str(e)}"
        )


@router.get("/translations/{translation_id}", response_model=TranslationResponse)
async def get_translation(
    translation_id: str,
    user_id: Optional[str] = Query(None, description="User ID for authorization"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get translation details by ID.

    Returns complete information about a translation including:
    - Source and translated text
    - Language codes
    - Quality and confidence scores
    - Processing metadata
    - Glossary usage statistics
    """
    try:
        service = TranslationService(db)
        translation = await service.get_translation(translation_id, user_id)
        return translation

    except Exception as e:
        logger.error(f"Failed to get translation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Translation not found: {str(e)}"
        )


@router.get("/translations", response_model=TranslationListResponse)
async def list_translations(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    source_language: Optional[str] = Query(None, description="Filter by source language"),
    target_language: Optional[str] = Query(None, description="Filter by target language"),
    status: Optional[TranslationStatusEnum] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List translations with pagination and filtering.

    **Filters:**
    - `user_id`: Show only translations for a specific user
    - `source_language`: Filter by source language code
    - `target_language`: Filter by target language code
    - `status`: Filter by processing status (pending, processing, completed, failed)

    **Pagination:**
    - `page`: Page number (starting from 1)
    - `page_size`: Number of items per page (max 100)
    """
    try:
        service = TranslationService(db)
        translation_status = TranslationStatus(status.value) if status else None
        translations = await service.list_translations(
            user_id, source_language, target_language, translation_status, page, page_size
        )
        return translations

    except Exception as e:
        logger.error(f"Failed to list translations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list translations: {str(e)}"
        )


@router.post("/glossaries", response_model=GlossaryDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_glossary(
    request: GlossaryRequest,
    user_id: Optional[str] = Query(None, description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a custom glossary for consistent translations.

    **Glossaries** ensure consistent translation of specific terms across all translations.
    Perfect for:
    - Brand names and product terms
    - Technical terminology
    - Company-specific vocabulary
    - Industry jargon

    **Example:**
    ```json
    {
      "name": "Product Glossary",
      "source_language": "en",
      "target_language": "es",
      "entries": {
        "dashboard": "panel de control",
        "user profile": "perfil de usuario",
        "API key": "clave de API"
      }
    }
    ```
    """
    try:
        service = TranslationService(db)
        glossary = await service.create_glossary(request, user_id)
        return glossary

    except Exception as e:
        logger.error(f"Failed to create glossary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create glossary: {str(e)}"
        )


@router.get("/glossaries/{glossary_id}", response_model=GlossaryDetailResponse)
async def get_glossary(
    glossary_id: str,
    user_id: Optional[str] = Query(None, description="User ID for authorization"),
    db: AsyncSession = Depends(get_db)
):
    """Get glossary details including all entries"""
    try:
        service = TranslationService(db)
        glossary = await service.get_glossary(glossary_id, user_id)
        return glossary

    except Exception as e:
        logger.error(f"Failed to get glossary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Glossary not found: {str(e)}"
        )


@router.get("/glossaries", response_model=List[GlossaryResponse])
async def list_glossaries(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all glossaries.

    Returns summary information for all active glossaries including:
    - Glossary name and description
    - Language pair
    - Number of entries
    - Creation date
    """
    try:
        service = TranslationService(db)
        glossaries = await service.list_glossaries(user_id)
        return glossaries

    except Exception as e:
        logger.error(f"Failed to list glossaries: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list glossaries: {str(e)}"
        )


@router.put("/glossaries/{glossary_id}", response_model=GlossaryDetailResponse)
async def update_glossary(
    glossary_id: str,
    entries: dict = Body(..., description="Updated glossary entries"),
    user_id: Optional[str] = Query(None, description="User ID for authorization"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update glossary entries.

    Replaces all existing entries with the new entries provided.
    Use this to add, remove, or modify glossary terms.
    """
    try:
        service = TranslationService(db)
        glossary = await service.update_glossary(glossary_id, entries, user_id)
        return glossary

    except Exception as e:
        logger.error(f"Failed to update glossary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update glossary: {str(e)}"
        )


@router.delete("/glossaries/{glossary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_glossary(
    glossary_id: str,
    user_id: Optional[str] = Query(None, description="User ID for authorization"),
    db: AsyncSession = Depends(get_db)
):
    """Delete a glossary"""
    try:
        service = TranslationService(db)
        await service.delete_glossary(glossary_id, user_id)
        return None

    except Exception as e:
        logger.error(f"Failed to delete glossary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Glossary not found: {str(e)}"
        )


@router.get("/languages", response_model=SupportedLanguagesResponse)
async def get_supported_languages(db: AsyncSession = Depends(get_db)):
    """
    Get list of all supported languages.

    Returns language codes and names for all supported translation languages.
    Use these codes in the `source_language` and `target_language` fields.

    **Supported Languages:** 100+
    Including all major world languages and many regional dialects.
    """
    try:
        service = TranslationService(db)
        languages = service.get_supported_languages()
        return SupportedLanguagesResponse(
            languages=languages,
            count=len(languages)
        )

    except Exception as e:
        logger.error(f"Failed to get languages: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get languages: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for Translation module"""
    return {
        "status": "healthy",
        "module": "translation",
        "version": "0.1.0"
    }
