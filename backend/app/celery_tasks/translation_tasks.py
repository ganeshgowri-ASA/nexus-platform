"""Celery tasks for translation processing"""
from celery import Task
from app.celery_tasks.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


class TranslationTask(Task):
    """Base translation task with error handling"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(f"Translation task {task_id} failed: {exc}", exc_info=einfo)
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        logger.info(f"Translation task {task_id} completed successfully")
        super().on_success(retval, task_id, args, kwargs)


@celery_app.task(base=TranslationTask, bind=True, name="translate_text_async")
def translate_text_async(self, translation_id: str, text: str, source_lang: str, target_lang: str, options: dict):
    """
    Translate text asynchronously

    Args:
        translation_id: Translation ID
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code
        options: Translation options (service, glossary_id, etc.)
    """
    try:
        from app.modules.translation.processor import TranslationProcessor
        from app.db.session import AsyncSessionLocal
        from app.modules.translation.models import Translation, TranslationStatus
        import asyncio

        logger.info(f"Starting async translation for {translation_id}")

        # Update task progress
        self.update_state(state='PROGRESS', meta={'progress': 0})

        # Process translation
        processor = TranslationProcessor(service=options.get('service', 'google'))

        async def process():
            result = await processor.translate(
                text=text,
                source_language=source_lang,
                target_language=target_lang,
                context=options.get('context'),
                glossary=options.get('glossary')
            )

            # Update database
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                query = select(Translation).where(Translation.id == translation_id)
                db_result = await db.execute(query)
                translation = db_result.scalar_one_or_none()

                if translation:
                    translation.status = TranslationStatus.COMPLETED
                    translation.translated_text = result["translated_text"]
                    translation.detected_language = result.get("detected_language")
                    translation.confidence_score = result.get("confidence_score")
                    translation.quality_score = result.get("quality_score")
                    translation.processing_time = result.get("processing_time")

                    await db.commit()

            return result

        result = asyncio.run(process())

        self.update_state(state='SUCCESS', meta={'progress': 100})

        return {
            "translation_id": translation_id,
            "status": "completed",
            "translated_length": len(result.get("translated_text", ""))
        }

    except Exception as e:
        logger.error(f"Translation processing failed: {e}", exc_info=True)
        raise


@celery_app.task(base=TranslationTask, bind=True, name="batch_translate_async")
def batch_translate_async(self, batch_id: str, texts: list, source_lang: str, target_lang: str, options: dict):
    """
    Translate multiple texts in batch asynchronously

    Args:
        batch_id: Batch translation ID
        texts: List of texts to translate
        source_lang: Source language code
        target_lang: Target language code
        options: Translation options
    """
    try:
        from app.modules.translation.processor import TranslationProcessor
        from app.db.session import AsyncSessionLocal
        from app.modules.translation.models import BatchTranslation, TranslationStatus
        import asyncio

        logger.info(f"Starting batch translation {batch_id} with {len(texts)} items")

        processor = TranslationProcessor(service=options.get('service', 'google'))

        async def process():
            results = await processor.batch_translate(
                texts=texts,
                source_language=source_lang,
                target_language=target_lang,
                glossary=options.get('glossary')
            )

            # Update database
            completed = sum(1 for r in results if "error" not in r)
            failed = len(results) - completed

            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                query = select(BatchTranslation).where(BatchTranslation.id == batch_id)
                db_result = await db.execute(query)
                batch = db_result.scalar_one_or_none()

                if batch:
                    batch.status = TranslationStatus.COMPLETED if failed == 0 else TranslationStatus.FAILED
                    batch.completed_items = completed
                    batch.failed_items = failed
                    batch.processing_time = sum(r.get("processing_time", 0) for r in results if "error" not in r)

                    await db.commit()

            return results

        results = asyncio.run(process())

        return {
            "batch_id": batch_id,
            "status": "completed",
            "completed": sum(1 for r in results if "error" not in r),
            "failed": sum(1 for r in results if "error" in r)
        }

    except Exception as e:
        logger.error(f"Batch translation failed: {e}", exc_info=True)
        raise
