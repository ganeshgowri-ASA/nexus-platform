"""Translation service layer - business logic"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.modules.translation.models import (
    Translation,
    TranslationGlossary,
    DocumentTranslation,
    BatchTranslation,
    TranslationStatus,
    TranslationService as TranslationServiceModel,
    TranslationType
)
from app.modules.translation.processor import TranslationProcessor
from app.modules.translation.schemas import (
    TranslationRequest,
    TranslationResponse,
    BatchTranslationRequest,
    BatchTranslationResponse,
    GlossaryRequest,
    GlossaryResponse,
    GlossaryDetailResponse,
    TranslationListResponse
)
from app.modules.translation.utils import validate_glossary_entries, get_supported_languages
from app.core.config import settings
from app.core.logging import get_logger
from app.utils.exceptions import TranslationError, LanguageNotSupportedError

logger = get_logger(__name__)


class TranslationService:
    """Translation service for text translation operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def translate_text(
        self,
        request: TranslationRequest,
        user_id: Optional[str] = None
    ) -> TranslationResponse:
        """Translate text"""
        try:
            # Get glossary if specified
            glossary_entries = None
            if request.glossary_id:
                glossary_entries = await self._get_glossary_entries(request.glossary_id)

            # Create database record
            translation = Translation(
                user_id=user_id,
                source_text=request.text,
                source_language=request.source_language,
                target_language=request.target_language,
                status=TranslationStatus.PROCESSING,
                service=TranslationServiceModel(request.service.value),
                translation_type=TranslationType.TEXT,
                character_count=len(request.text),
                glossary_id=request.glossary_id,
                context=request.context
            )

            self.db.add(translation)
            await self.db.commit()
            await self.db.refresh(translation)

            logger.info(f"Created translation {translation.id}")

            # Process translation
            try:
                processor = TranslationProcessor(service=request.service.value)
                result = await processor.translate(
                    text=request.text,
                    source_language=request.source_language,
                    target_language=request.target_language,
                    context=request.context,
                    glossary=glossary_entries
                )

                # Update database record with results
                translation.status = TranslationStatus.COMPLETED
                translation.translated_text = result["translated_text"]
                translation.detected_language = result.get("detected_language")
                translation.confidence_score = result.get("confidence_score")
                translation.quality_score = result.get("quality_score")
                translation.processing_time = result.get("processing_time")
                translation.metadata = {
                    "glossary_replacements": result.get("glossary_replacements", 0),
                    "chunks_processed": result.get("chunks_processed", 1)
                }

                await self.db.commit()
                await self.db.refresh(translation)

                logger.info(f"Translation {translation.id} completed successfully")

                return TranslationResponse.model_validate(translation)

            except Exception as e:
                # Update status to failed
                translation.status = TranslationStatus.FAILED
                translation.error_message = str(e)
                await self.db.commit()

                logger.error(f"Translation {translation.id} failed: {e}", exc_info=True)
                raise TranslationError(f"Translation failed: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to create translation: {e}", exc_info=True)
            raise

    async def batch_translate(
        self,
        request: BatchTranslationRequest,
        user_id: Optional[str] = None
    ) -> BatchTranslationResponse:
        """Batch translate multiple texts"""
        try:
            # Get glossary if specified
            glossary_entries = None
            if request.glossary_id:
                glossary_entries = await self._get_glossary_entries(request.glossary_id)

            # Create batch record
            total_chars = sum(len(text) for text in request.texts)
            batch = BatchTranslation(
                user_id=user_id,
                name=f"Batch {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                source_language=request.source_language,
                target_language=request.target_language,
                status=TranslationStatus.PROCESSING,
                service=TranslationServiceModel(request.service.value),
                total_items=len(request.texts),
                total_characters=total_chars,
                glossary_id=request.glossary_id
            )

            self.db.add(batch)
            await self.db.commit()
            await self.db.refresh(batch)

            logger.info(f"Created batch translation {batch.id} with {len(request.texts)} items")

            # Process batch
            processor = TranslationProcessor(service=request.service.value)
            results = await processor.batch_translate(
                texts=request.texts,
                source_language=request.source_language,
                target_language=request.target_language,
                glossary=glossary_entries
            )

            # Count completed and failed
            completed = sum(1 for r in results if "error" not in r)
            failed = len(results) - completed

            # Update batch record
            batch.status = TranslationStatus.COMPLETED if failed == 0 else TranslationStatus.FAILED
            batch.completed_items = completed
            batch.failed_items = failed
            batch.processing_time = sum(r.get("processing_time", 0) for r in results if "error" not in r)

            await self.db.commit()
            await self.db.refresh(batch)

            logger.info(f"Batch translation {batch.id} completed: {completed} succeeded, {failed} failed")

            return BatchTranslationResponse.model_validate(batch)

        except Exception as e:
            logger.error(f"Batch translation failed: {e}", exc_info=True)
            raise TranslationError(f"Batch translation failed: {str(e)}")

    async def get_translation(self, translation_id: str, user_id: Optional[str] = None) -> TranslationResponse:
        """Get translation by ID"""
        query = select(Translation).where(Translation.id == translation_id)

        if user_id:
            query = query.where(Translation.user_id == user_id)

        result = await self.db.execute(query)
        translation = result.scalar_one_or_none()

        if not translation:
            raise TranslationError("Translation not found")

        return TranslationResponse.model_validate(translation)

    async def list_translations(
        self,
        user_id: Optional[str] = None,
        source_language: Optional[str] = None,
        target_language: Optional[str] = None,
        status: Optional[TranslationStatus] = None,
        page: int = 1,
        page_size: int = 10
    ) -> TranslationListResponse:
        """List translations with pagination"""
        query = select(Translation)

        # Apply filters
        conditions = []
        if user_id:
            conditions.append(Translation.user_id == user_id)
        if source_language:
            conditions.append(Translation.source_language == source_language)
        if target_language:
            conditions.append(Translation.target_language == target_language)
        if status:
            conditions.append(Translation.status == status)

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count()).select_from(Translation)
        if conditions:
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(Translation.created_at.desc())

        result = await self.db.execute(query)
        translations = result.scalars().all()

        return TranslationListResponse(
            total=total,
            items=[TranslationResponse.model_validate(t) for t in translations],
            page=page,
            page_size=page_size
        )

    async def create_glossary(
        self,
        request: GlossaryRequest,
        user_id: Optional[str] = None
    ) -> GlossaryDetailResponse:
        """Create a new glossary"""
        # Validate entries
        is_valid, errors = validate_glossary_entries(request.entries)
        if not is_valid:
            raise TranslationError(f"Invalid glossary entries: {', '.join(errors)}")

        glossary = TranslationGlossary(
            user_id=user_id,
            name=request.name,
            description=request.description,
            source_language=request.source_language,
            target_language=request.target_language,
            entries=request.entries,
            entry_count=len(request.entries)
        )

        self.db.add(glossary)
        await self.db.commit()
        await self.db.refresh(glossary)

        logger.info(f"Created glossary {glossary.id} with {glossary.entry_count} entries")

        return GlossaryDetailResponse.model_validate(glossary)

    async def get_glossary(self, glossary_id: str, user_id: Optional[str] = None) -> GlossaryDetailResponse:
        """Get glossary by ID"""
        query = select(TranslationGlossary).where(TranslationGlossary.id == glossary_id)

        if user_id:
            query = query.where(TranslationGlossary.user_id == user_id)

        result = await self.db.execute(query)
        glossary = result.scalar_one_or_none()

        if not glossary:
            raise TranslationError("Glossary not found")

        return GlossaryDetailResponse.model_validate(glossary)

    async def list_glossaries(self, user_id: Optional[str] = None) -> List[GlossaryResponse]:
        """List all glossaries"""
        query = select(TranslationGlossary)

        if user_id:
            query = query.where(TranslationGlossary.user_id == user_id)

        query = query.where(TranslationGlossary.is_active == True)
        query = query.order_by(TranslationGlossary.created_at.desc())

        result = await self.db.execute(query)
        glossaries = result.scalars().all()

        return [GlossaryResponse.model_validate(g) for g in glossaries]

    async def update_glossary(
        self,
        glossary_id: str,
        entries: Dict[str, str],
        user_id: Optional[str] = None
    ) -> GlossaryDetailResponse:
        """Update glossary entries"""
        query = select(TranslationGlossary).where(TranslationGlossary.id == glossary_id)

        if user_id:
            query = query.where(TranslationGlossary.user_id == user_id)

        result = await self.db.execute(query)
        glossary = result.scalar_one_or_none()

        if not glossary:
            raise TranslationError("Glossary not found")

        # Validate new entries
        is_valid, errors = validate_glossary_entries(entries)
        if not is_valid:
            raise TranslationError(f"Invalid glossary entries: {', '.join(errors)}")

        glossary.entries = entries
        glossary.entry_count = len(entries)

        await self.db.commit()
        await self.db.refresh(glossary)

        logger.info(f"Updated glossary {glossary_id}")

        return GlossaryDetailResponse.model_validate(glossary)

    async def delete_glossary(self, glossary_id: str, user_id: Optional[str] = None) -> bool:
        """Delete glossary"""
        query = select(TranslationGlossary).where(TranslationGlossary.id == glossary_id)

        if user_id:
            query = query.where(TranslationGlossary.user_id == user_id)

        result = await self.db.execute(query)
        glossary = result.scalar_one_or_none()

        if not glossary:
            raise TranslationError("Glossary not found")

        await self.db.delete(glossary)
        await self.db.commit()

        logger.info(f"Deleted glossary {glossary_id}")
        return True

    async def _get_glossary_entries(self, glossary_id: str) -> Optional[Dict[str, str]]:
        """Get glossary entries by ID"""
        query = select(TranslationGlossary).where(
            and_(
                TranslationGlossary.id == glossary_id,
                TranslationGlossary.is_active == True
            )
        )

        result = await self.db.execute(query)
        glossary = result.scalar_one_or_none()

        return glossary.entries if glossary else None

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages"""
        return get_supported_languages()
