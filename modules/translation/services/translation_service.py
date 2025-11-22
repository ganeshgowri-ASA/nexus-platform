"""
Main translation service orchestrator
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from .providers.google_translate import GoogleTranslateProvider
from .providers.deepl_translate import DeepLTranslateProvider
from .providers.base import BaseTranslationProvider
from .glossary_service import GlossaryService
from .quality_scoring import QualityScoringService
from ..models.database import Translation
from ..config import config


class TranslationService:
    """Main service for managing translations"""

    def __init__(self):
        """Initialize translation service with available providers"""
        self.providers: Dict[str, BaseTranslationProvider] = {}

        # Initialize Google Translate provider
        if config.google_api_key:
            self.providers['google'] = GoogleTranslateProvider(
                api_key=config.google_api_key,
                project_id=config.google_project_id
            )

        # Initialize DeepL provider
        if config.deepl_api_key:
            self.providers['deepl'] = DeepLTranslateProvider(
                api_key=config.deepl_api_key
            )

        self.default_provider = config.default_provider
        self.glossary_service = GlossaryService()
        self.quality_service = QualityScoringService()

    def get_provider(self, provider_name: Optional[str] = None) -> BaseTranslationProvider:
        """
        Get translation provider by name

        Args:
            provider_name: Name of the provider (google/deepl)

        Returns:
            Translation provider instance

        Raises:
            ValueError: If provider is not available
        """
        provider = provider_name or self.default_provider

        if provider not in self.providers:
            available = ', '.join(self.providers.keys())
            raise ValueError(
                f"Provider '{provider}' not available. "
                f"Available providers: {available}"
            )

        return self.providers[provider]

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        provider: Optional[str] = None,
        glossary_id: Optional[int] = None,
        db: Optional[Session] = None,
        enable_quality_scoring: bool = True,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Translate text with specified provider

        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            provider: Translation provider name
            glossary_id: Optional glossary ID
            db: Database session
            enable_quality_scoring: Whether to calculate quality score
            user_id: User ID for tracking
            **kwargs: Additional provider-specific parameters

        Returns:
            Dictionary containing translation results
        """
        # Get the translation provider
        translator = self.get_provider(provider)

        # Get glossary terms if specified
        glossary_terms = None
        if glossary_id and db:
            glossary_terms = self.glossary_service.get_glossary_terms_dict(
                db, glossary_id
            )

        # Perform translation
        translated_text = await translator.translate(
            text,
            source_language,
            target_language,
            glossary_terms=glossary_terms,
            **kwargs
        )

        # Calculate quality score if enabled
        quality_score = None
        if enable_quality_scoring and config.enable_quality_scoring:
            quality_result = await self.quality_service.calculate_quality_score(
                source_text=text,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language
            )
            quality_score = quality_result['score']

        # Save translation to database if session provided
        translation_record = None
        if db:
            translation_record = Translation(
                source_text=text,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                provider=provider or self.default_provider,
                quality_score=quality_score,
                character_count=len(text),
                glossary_id=glossary_id,
                user_id=user_id
            )
            db.add(translation_record)
            db.commit()
            db.refresh(translation_record)

        return {
            'translated_text': translated_text,
            'source_text': text,
            'source_language': source_language,
            'target_language': target_language,
            'provider': provider or self.default_provider,
            'quality_score': quality_score,
            'character_count': len(text),
            'id': translation_record.id if translation_record else None
        }

    async def translate_batch(
        self,
        texts: List[str],
        source_language: str,
        target_language: str,
        provider: Optional[str] = None,
        glossary_id: Optional[int] = None,
        db: Optional[Session] = None,
        **kwargs
    ) -> List[str]:
        """
        Translate multiple texts in batch

        Args:
            texts: List of texts to translate
            source_language: Source language code
            target_language: Target language code
            provider: Translation provider name
            glossary_id: Optional glossary ID
            db: Database session
            **kwargs: Additional provider-specific parameters

        Returns:
            List of translated texts
        """
        translator = self.get_provider(provider)

        # Get glossary terms if specified
        glossary_terms = None
        if glossary_id and db:
            glossary_terms = self.glossary_service.get_glossary_terms_dict(
                db, glossary_id
            )

        # Perform batch translation
        translated_texts = await translator.translate_batch(
            texts,
            source_language,
            target_language,
            glossary_terms=glossary_terms,
            **kwargs
        )

        return translated_texts

    async def detect_language(
        self,
        text: str,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect the language of the given text

        Args:
            text: Text to analyze
            provider: Translation provider name

        Returns:
            Dictionary containing detected language info
        """
        translator = self.get_provider(provider)
        return await translator.detect_language(text)

    def get_supported_languages(self, provider: Optional[str] = None) -> List[str]:
        """
        Get list of supported languages

        Args:
            provider: Translation provider name

        Returns:
            List of language codes
        """
        translator = self.get_provider(provider)
        return translator.get_supported_languages()

    async def get_translation_history(
        self,
        db: Session,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Translation]:
        """
        Get translation history

        Args:
            db: Database session
            user_id: Optional user ID filter
            limit: Maximum number of records
            offset: Offset for pagination

        Returns:
            List of translation records
        """
        query = db.query(Translation)

        if user_id:
            query = query.filter(Translation.user_id == user_id)

        query = query.order_by(Translation.created_at.desc())
        query = query.limit(limit).offset(offset)

        return query.all()

    async def get_translation_stats(
        self,
        db: Session,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get translation statistics

        Args:
            db: Database session
            user_id: Optional user ID filter

        Returns:
            Dictionary containing statistics
        """
        from sqlalchemy import func
        from datetime import datetime, timedelta

        query = db.query(Translation)
        if user_id:
            query = query.filter(Translation.user_id == user_id)

        # Total translations
        total_translations = query.count()

        # Total characters
        total_characters = db.query(
            func.sum(Translation.character_count)
        ).scalar() or 0

        # Average quality score
        avg_quality = db.query(
            func.avg(Translation.quality_score)
        ).filter(Translation.quality_score.isnot(None)).scalar()

        # Translations today
        today = datetime.utcnow().date()
        translations_today = query.filter(
            func.date(Translation.created_at) == today
        ).count()

        # Translations this week
        week_ago = datetime.utcnow() - timedelta(days=7)
        translations_this_week = query.filter(
            Translation.created_at >= week_ago
        ).count()

        # Translations this month
        month_ago = datetime.utcnow() - timedelta(days=30)
        translations_this_month = query.filter(
            Translation.created_at >= month_ago
        ).count()

        return {
            'total_translations': total_translations,
            'total_characters': int(total_characters),
            'average_quality_score': float(avg_quality) if avg_quality else None,
            'translations_today': translations_today,
            'translations_this_week': translations_this_week,
            'translations_this_month': translations_this_month
        }
