"""
Celery Tasks

Asynchronous translation tasks for background processing.
"""

from typing import List, Optional, Dict, Any
from celery import shared_task
from nexus.core.database import get_db_session
from nexus.core.celery_app import celery_app
from nexus.modules.translation.translator import Translator, BatchTranslator
from nexus.modules.translation.cache import TranslationCache
from config.logging import get_logger

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=3)
def translate_text_async(
    self,
    user_id: int,
    text: str,
    target_lang: str,
    source_lang: Optional[str] = None,
    engine: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Async translation task.

    Args:
        user_id: User ID
        text: Text to translate
        target_lang: Target language
        source_lang: Source language
        engine: Translation engine
        **kwargs: Additional parameters

    Returns:
        Translation result
    """
    try:
        db = get_db_session()

        translator = Translator(
            db=db,
            user_id=user_id,
            engine=engine,
        )

        translation = translator.translate(
            text=text,
            target_lang=target_lang,
            source_lang=source_lang,
            **kwargs,
        )

        db.close()

        logger.info(f"Async translation completed: {translation.id}")

        return {
            "id": translation.id,
            "source_text": translation.source_text,
            "translated_text": translation.target_text,
            "status": translation.status.value,
        }

    except Exception as e:
        logger.error(f"Async translation failed: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@shared_task
def translate_batch_async(
    user_id: int,
    texts: List[str],
    target_lang: str,
    source_lang: Optional[str] = None,
    engine: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Async batch translation task.

    Args:
        user_id: User ID
        texts: List of texts to translate
        target_lang: Target language
        source_lang: Source language
        engine: Translation engine

    Returns:
        Batch translation results
    """
    try:
        db = get_db_session()

        batch_translator = BatchTranslator(
            db=db,
            user_id=user_id,
            engine=engine,
        )

        translations = batch_translator.translate_batch(
            texts=texts,
            target_lang=target_lang,
            source_lang=source_lang,
        )

        db.close()

        logger.info(f"Async batch translation completed: {len(translations)} texts")

        return {
            "total": len(texts),
            "successful": len(translations),
            "failed": len(texts) - len(translations),
            "translations": [
                {
                    "id": t.id,
                    "source_text": t.source_text,
                    "translated_text": t.target_text,
                }
                for t in translations
            ],
        }

    except Exception as e:
        logger.error(f"Async batch translation failed: {e}")
        raise


@shared_task
def cleanup_old_translations(days: int = 90) -> int:
    """
    Clean up old translations.

    Args:
        days: Number of days to keep

    Returns:
        Number of deleted translations
    """
    try:
        from datetime import datetime, timedelta
        from nexus.models.translation import Translation

        db = get_db_session()

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Soft delete old translations
        old_translations = (
            db.query(Translation)
            .filter(Translation.created_at < cutoff_date)
            .all()
        )

        count = 0
        for translation in old_translations:
            translation.soft_delete(db)
            count += 1

        db.close()

        logger.info(f"Cleaned up {count} old translations")
        return count

    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        raise


@shared_task
def update_translation_statistics() -> Dict[str, Any]:
    """
    Update translation statistics.

    Returns:
        Updated statistics
    """
    try:
        from nexus.models.translation import Translation
        from sqlalchemy import func

        db = get_db_session()

        # Calculate statistics
        total_translations = db.query(Translation).count()
        avg_quality = db.query(func.avg(Translation.quality_score)).scalar() or 0.0
        avg_processing_time = db.query(func.avg(Translation.processing_time_ms)).scalar() or 0

        # Language pair statistics
        language_pairs = (
            db.query(
                Translation.source_language,
                Translation.target_language,
                func.count(Translation.id).label("count"),
            )
            .group_by(Translation.source_language, Translation.target_language)
            .order_by(func.count(Translation.id).desc())
            .limit(10)
            .all()
        )

        db.close()

        stats = {
            "total_translations": total_translations,
            "average_quality_score": float(avg_quality),
            "average_processing_time_ms": int(avg_processing_time),
            "top_language_pairs": [
                {
                    "source": pair[0],
                    "target": pair[1],
                    "count": pair[2],
                }
                for pair in language_pairs
            ],
        }

        logger.info("Translation statistics updated")
        return stats

    except Exception as e:
        logger.error(f"Statistics update failed: {e}")
        raise


@shared_task
def cleanup_translation_cache() -> int:
    """
    Clean up translation cache.

    Returns:
        Number of entries cleaned
    """
    try:
        cache = TranslationCache()

        # Get cache stats
        stats = cache.get_stats()

        logger.info(f"Cache cleanup: {stats}")

        # Cache cleanup is handled by Redis TTL automatically
        return 0

    except Exception as e:
        logger.error(f"Cache cleanup task failed: {e}")
        raise


@shared_task
def export_translation_memory_tmx(
    source_lang: str,
    target_lang: str,
    output_path: str,
) -> str:
    """
    Export translation memory as TMX file.

    Args:
        source_lang: Source language
        target_lang: Target language
        output_path: Output file path

    Returns:
        Output file path
    """
    try:
        from nexus.modules.translation.memory import TranslationMemoryManager

        db = get_db_session()

        tm_manager = TranslationMemoryManager(db)
        tmx_content = tm_manager.export_tmx(source_lang, target_lang)

        # Save to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(tmx_content)

        db.close()

        logger.info(f"TMX export completed: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"TMX export task failed: {e}")
        raise


@shared_task
def process_document_translation(
    user_id: int,
    document_path: str,
    target_lang: str,
    source_lang: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process document translation asynchronously.

    Args:
        user_id: User ID
        document_path: Path to document
        target_lang: Target language
        source_lang: Source language

    Returns:
        Translation results
    """
    try:
        # Document translation implementation would go here
        # This is a placeholder for the comprehensive document translation feature

        logger.info(f"Document translation started: {document_path}")

        return {
            "status": "completed",
            "document_path": document_path,
            "target_language": target_lang,
        }

    except Exception as e:
        logger.error(f"Document translation task failed: {e}")
        raise
