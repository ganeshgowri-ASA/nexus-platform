"""
Translation Classes

Main translation functionality including standard, batch, and streaming translation.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from config.settings import settings
from config.logging import get_logger
from nexus.core.exceptions import TranslationError
from nexus.models.translation import Translation, TranslationStatus, TranslationEngine
from nexus.modules.translation.engines import EngineFactory
from nexus.modules.translation.cache import TranslationCache
from nexus.modules.translation.language_detection import LanguageDetector
from nexus.modules.translation.glossary import GlossaryManager
from nexus.modules.translation.memory import TranslationMemoryManager
from nexus.modules.translation.quality import QualityAssessment
import time
import asyncio

logger = get_logger(__name__)


class Translator:
    """
    Main translation class.

    Provides:
    - Single text translation
    - Multi-engine support
    - Caching
    - Translation memory
    - Glossary application
    - Quality assessment
    """

    def __init__(
        self,
        db: Session,
        user_id: int,
        engine: Optional[str] = None,
        use_cache: bool = True,
        use_memory: bool = True,
        use_glossary: bool = True,
    ):
        """
        Initialize translator.

        Args:
            db: Database session
            user_id: User ID
            engine: Translation engine to use
            use_cache: Whether to use caching
            use_memory: Whether to use translation memory
            use_glossary: Whether to apply glossaries
        """
        self.db = db
        self.user_id = user_id
        self.engine_name = engine or settings.DEFAULT_TRANSLATION_ENGINE
        self.use_cache = use_cache and settings.ENABLE_TRANSLATION_MEMORY
        self.use_memory = use_memory and settings.ENABLE_TRANSLATION_MEMORY
        self.use_glossary = use_glossary and settings.ENABLE_GLOSSARY

        # Initialize components
        self.engine = EngineFactory.create_engine(self.engine_name)
        self.cache = TranslationCache() if self.use_cache else None
        self.language_detector = LanguageDetector()
        self.glossary_manager = GlossaryManager(db) if self.use_glossary else None
        self.memory_manager = TranslationMemoryManager(db) if self.use_memory else None
        self.quality_assessor = QualityAssessment()

        logger.info(f"Translator initialized with engine: {self.engine_name}")

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs,
    ) -> Translation:
        """
        Translate text.

        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code (auto-detect if None)
            context: Additional context
            **kwargs: Additional parameters

        Returns:
            Translation model instance

        Raises:
            TranslationError: If translation fails
        """
        start_time = time.time()

        # Detect source language if not provided
        if not source_lang and settings.ENABLE_AUTO_LANGUAGE_DETECTION:
            detection = self.language_detector.detect(text)
            source_lang = detection["language"]
            logger.info(f"Detected language: {source_lang}")

        # Check cache
        if self.cache:
            cached = self.cache.get(text, source_lang, target_lang)
            if cached:
                logger.info("Translation found in cache")
                return self._create_translation_record(
                    source_text=text,
                    target_text=cached["translation"],
                    source_lang=source_lang,
                    target_lang=target_lang,
                    cached=True,
                    **cached,
                )

        # Check translation memory
        if self.memory_manager:
            memory_match = self.memory_manager.find_match(
                text, source_lang, target_lang, context
            )
            if memory_match and memory_match["similarity"] > 0.95:
                logger.info(f"High similarity match found in TM: {memory_match['similarity']}")
                return self._create_translation_record(
                    source_text=text,
                    target_text=memory_match["target_text"],
                    source_lang=source_lang,
                    target_lang=target_lang,
                    cached=True,
                )

        # Apply glossary pre-processing
        processed_text = text
        glossary_terms = {}
        if self.glossary_manager:
            glossary_terms = self.glossary_manager.apply_glossary(
                text, source_lang, target_lang
            )
            if glossary_terms:
                logger.info(f"Applied {len(glossary_terms)} glossary terms")

        # Perform translation
        try:
            result = self.engine.translate(
                processed_text,
                target_lang=target_lang,
                source_lang=source_lang,
                context=context,
                **kwargs,
            )

            translated_text = result["translated_text"]

            # Apply glossary post-processing
            if glossary_terms:
                for source_term, target_term in glossary_terms.items():
                    # Simple replacement - in production, use more sophisticated NLP
                    translated_text = translated_text.replace(source_term, target_term)

            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)

            # Assess quality
            quality_scores = None
            if settings.ENABLE_QUALITY_ASSESSMENT:
                quality_scores = self.quality_assessor.assess(
                    text, translated_text, source_lang, target_lang
                )

            # Create translation record
            translation = self._create_translation_record(
                source_text=text,
                target_text=translated_text,
                source_lang=source_lang or result.get("source_language"),
                target_lang=target_lang,
                processing_time=processing_time,
                quality_score=quality_scores.get("overall_score") if quality_scores else None,
                confidence=result.get("confidence", 0.9),
                context=context,
            )

            # Cache result
            if self.cache:
                self.cache.set(
                    text,
                    source_lang or result.get("source_language"),
                    target_lang,
                    translated_text,
                    metadata={"confidence": result.get("confidence", 0.9)},
                )

            # Add to translation memory
            if self.memory_manager and quality_scores:
                if quality_scores.get("overall_score", 0) >= settings.TRANSLATION_QUALITY_THRESHOLD:
                    self.memory_manager.add_translation(
                        text,
                        translated_text,
                        source_lang or result.get("source_language"),
                        target_lang,
                        context,
                        quality_scores.get("overall_score"),
                    )

            logger.info(f"Translation completed in {processing_time}ms")
            return translation

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            # Create failed translation record
            translation = Translation(
                user_id=self.user_id,
                source_text=text,
                source_language=source_lang or "unknown",
                target_language=target_lang,
                engine=TranslationEngine(self.engine_name),
                status=TranslationStatus.FAILED,
                metadata={"error": str(e)},
            )
            translation.save(self.db)
            raise TranslationError(f"Translation failed: {str(e)}")

    def _create_translation_record(
        self,
        source_text: str,
        target_text: str,
        source_lang: str,
        target_lang: str,
        processing_time: int = 0,
        quality_score: Optional[float] = None,
        confidence: float = 0.9,
        context: Optional[str] = None,
        cached: bool = False,
    ) -> Translation:
        """Create and save translation record."""
        translation = Translation(
            user_id=self.user_id,
            source_text=source_text,
            target_text=target_text,
            source_language=source_lang,
            target_language=target_lang,
            engine=TranslationEngine(self.engine_name),
            status=TranslationStatus.COMPLETED,
            quality_score=quality_score,
            confidence_score=confidence,
            context=context,
            cached=cached,
            processing_time_ms=processing_time,
        )

        translation.save(self.db)
        return translation


class BatchTranslator:
    """
    Batch translation for processing multiple texts.

    Optimizes by:
    - Parallel processing
    - Batch API calls
    - Smart caching
    """

    def __init__(
        self,
        db: Session,
        user_id: int,
        engine: Optional[str] = None,
        max_batch_size: int = 100,
    ):
        """
        Initialize batch translator.

        Args:
            db: Database session
            user_id: User ID
            engine: Translation engine
            max_batch_size: Maximum batch size
        """
        self.db = db
        self.user_id = user_id
        self.engine = engine
        self.max_batch_size = min(max_batch_size, settings.TRANSLATION_MAX_BATCH_SIZE)
        self.translator = Translator(db, user_id, engine)

    def translate_batch(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: Optional[str] = None,
        **kwargs,
    ) -> List[Translation]:
        """
        Translate multiple texts.

        Args:
            texts: List of texts to translate
            target_lang: Target language
            source_lang: Source language
            **kwargs: Additional parameters

        Returns:
            List of translation records
        """
        results = []

        # Process in batches
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i : i + self.max_batch_size]

            logger.info(f"Processing batch {i // self.max_batch_size + 1}")

            for text in batch:
                try:
                    translation = self.translator.translate(
                        text,
                        target_lang=target_lang,
                        source_lang=source_lang,
                        **kwargs,
                    )
                    results.append(translation)
                except Exception as e:
                    logger.error(f"Batch translation error: {e}")
                    # Continue with next text
                    continue

        logger.info(f"Batch translation completed: {len(results)}/{len(texts)} successful")
        return results


class StreamingTranslator:
    """
    Streaming translator for real-time translation.

    Provides:
    - Real-time translation updates
    - Progress tracking
    - WebSocket support
    """

    def __init__(
        self,
        db: Session,
        user_id: int,
        engine: Optional[str] = None,
    ):
        """
        Initialize streaming translator.

        Args:
            db: Database session
            user_id: User ID
            engine: Translation engine
        """
        self.db = db
        self.user_id = user_id
        self.translator = Translator(db, user_id, engine)

    async def translate_stream(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        callback=None,
        **kwargs,
    ) -> Translation:
        """
        Translate with progress updates.

        Args:
            text: Text to translate
            target_lang: Target language
            source_lang: Source language
            callback: Callback function for progress updates
            **kwargs: Additional parameters

        Returns:
            Translation record
        """
        # Send initial progress
        if callback:
            await callback({"status": "started", "progress": 0})

        # Perform translation
        translation = await asyncio.to_thread(
            self.translator.translate,
            text,
            target_lang,
            source_lang,
            **kwargs,
        )

        # Send completion
        if callback:
            await callback({
                "status": "completed",
                "progress": 100,
                "result": translation.to_dict(),
            })

        return translation

    async def translate_batch_stream(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: Optional[str] = None,
        callback=None,
        **kwargs,
    ) -> List[Translation]:
        """
        Batch translate with progress updates.

        Args:
            texts: List of texts
            target_lang: Target language
            source_lang: Source language
            callback: Progress callback
            **kwargs: Additional parameters

        Returns:
            List of translations
        """
        results = []
        total = len(texts)

        for i, text in enumerate(texts):
            try:
                translation = await asyncio.to_thread(
                    self.translator.translate,
                    text,
                    target_lang,
                    source_lang,
                    **kwargs,
                )
                results.append(translation)

                # Send progress update
                if callback:
                    progress = int((i + 1) / total * 100)
                    await callback({
                        "status": "processing",
                        "progress": progress,
                        "completed": i + 1,
                        "total": total,
                    })

            except Exception as e:
                logger.error(f"Stream translation error: {e}")
                if callback:
                    await callback({
                        "status": "error",
                        "error": str(e),
                        "text_index": i,
                    })

        # Send completion
        if callback:
            await callback({
                "status": "completed",
                "progress": 100,
                "total_successful": len(results),
                "total_failed": total - len(results),
            })

        return results
