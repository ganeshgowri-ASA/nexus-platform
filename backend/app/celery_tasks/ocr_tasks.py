"""Celery tasks for OCR processing"""
from celery import Task
from app.celery_tasks.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


class OCRTask(Task):
    """Base OCR task with error handling"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(f"OCR task {task_id} failed: {exc}", exc_info=einfo)
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        logger.info(f"OCR task {task_id} completed successfully")
        super().on_success(retval, task_id, args, kwargs)


@celery_app.task(base=OCRTask, bind=True, name="process_ocr_async")
def process_ocr_async(self, document_id: str, file_path: str, options: dict):
    """
    Process OCR asynchronously

    Args:
        document_id: OCR document ID
        file_path: Path to file to process
        options: OCR processing options
    """
    try:
        from app.modules.ocr.processor import OCRProcessor
        from app.db.session import AsyncSessionLocal
        from app.modules.ocr.models import OCRDocument, OCRStatus
        import asyncio

        logger.info(f"Starting async OCR processing for document {document_id}")

        # Update task progress
        self.update_state(state='PROGRESS', meta={'progress': 0})

        # Process OCR
        processor = OCRProcessor(engine=options.get('engine', 'tesseract'))

        async def process():
            result = await processor.extract_text(
                file_path,
                detect_language=options.get('detect_language', True),
                extract_tables=options.get('extract_tables', True),
                detect_handwriting=options.get('detect_handwriting', True),
                analyze_layout=options.get('analyze_layout', True)
            )

            # Update database
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                query = select(OCRDocument).where(OCRDocument.id == document_id)
                db_result = await db.execute(query)
                doc = db_result.scalar_one_or_none()

                if doc:
                    doc.status = OCRStatus.COMPLETED
                    doc.extracted_text = result["extracted_text"]
                    doc.confidence_score = result.get("confidence_score")
                    doc.detected_language = result.get("detected_language")
                    doc.processing_time = result.get("processing_time")

                    await db.commit()

            return result

        result = asyncio.run(process())

        self.update_state(state='SUCCESS', meta={'progress': 100})

        return {
            "document_id": document_id,
            "status": "completed",
            "text_length": len(result.get("extracted_text", ""))
        }

    except Exception as e:
        logger.error(f"OCR processing failed: {e}", exc_info=True)
        raise


@celery_app.task(base=OCRTask, name="batch_process_ocr")
def batch_process_ocr(document_ids: list, options: dict):
    """
    Process multiple OCR documents in batch

    Args:
        document_ids: List of document IDs to process
        options: OCR processing options
    """
    results = []

    for doc_id in document_ids:
        try:
            result = process_ocr_async.delay(doc_id, options)
            results.append({"document_id": doc_id, "task_id": result.id})
        except Exception as e:
            logger.error(f"Failed to queue OCR task for {doc_id}: {e}")
            results.append({"document_id": doc_id, "error": str(e)})

    return results
