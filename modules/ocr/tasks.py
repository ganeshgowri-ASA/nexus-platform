"""
Celery Tasks

Asynchronous task processing for OCR jobs.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from celery import Celery, Task, group, chain
from celery.result import AsyncResult

from .config import config
from .processor import OCRPipeline, BatchProcessor
from .export import ExportManager

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'nexus_ocr',
    broker=config.celery_broker_url,
    backend=config.celery_result_backend
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)


class OCRTask(Task):
    """Base OCR task with error handling"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(f"Task {task_id} failed: {exc}")
        logger.error(f"Error info: {einfo}")

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        logger.info(f"Task {task_id} completed successfully")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry"""
        logger.warning(f"Task {task_id} retrying: {exc}")


@celery_app.task(base=OCRTask, bind=True, name='ocr.process_image')
def process_image_task(self, image_path: str, **kwargs) -> Dict[str, Any]:
    """
    Process single image with OCR

    Args:
        image_path: Path to image
        **kwargs: Processing options

    Returns:
        OCR result dictionary
    """
    try:
        logger.info(f"Processing image: {image_path}")

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'current': 0, 'total': 1, 'status': 'Processing image...'}
        )

        # Create OCR pipeline
        engine_type = kwargs.get('engine_type', 'tesseract')
        pipeline = OCRPipeline(engine_type=engine_type)

        # Process
        result = pipeline.process_file(Path(image_path), **kwargs)

        # Update state
        self.update_state(
            state='SUCCESS',
            meta={'current': 1, 'total': 1, 'status': 'Complete'}
        )

        logger.info(f"Image processing complete: {image_path}")
        return result

    except Exception as e:
        logger.error(f"Error processing image {image_path}: {e}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise


@celery_app.task(base=OCRTask, bind=True, name='ocr.process_document')
def process_document_task(self, file_path: str, **kwargs) -> Dict[str, Any]:
    """
    Process document (PDF or multi-page)

    Args:
        file_path: Path to document
        **kwargs: Processing options

    Returns:
        Processing result
    """
    try:
        logger.info(f"Processing document: {file_path}")

        # Update state
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Starting document processing...'}
        )

        # Create pipeline
        engine_type = kwargs.get('engine_type', 'tesseract')
        pipeline = OCRPipeline(engine_type=engine_type)

        # Process
        result = pipeline.process_file(Path(file_path), **kwargs)

        # Update state for each page
        page_count = result.get('page_count', 1)
        for i in range(page_count):
            self.update_state(
                state='PROCESSING',
                meta={
                    'current': i + 1,
                    'total': page_count,
                    'status': f'Processing page {i + 1}/{page_count}'
                }
            )

        logger.info(f"Document processing complete: {file_path}")
        return result

    except Exception as e:
        logger.error(f"Error processing document {file_path}: {e}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise


@celery_app.task(base=OCRTask, bind=True, name='ocr.batch_process')
def batch_process_task(
    self,
    file_paths: List[str],
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Batch process multiple documents

    Args:
        file_paths: List of file paths
        **kwargs: Processing options

    Returns:
        List of results
    """
    try:
        logger.info(f"Batch processing {len(file_paths)} documents")

        # Update state
        self.update_state(
            state='PROCESSING',
            meta={
                'current': 0,
                'total': len(file_paths),
                'status': 'Starting batch processing...'
            }
        )

        # Create batch processor
        engine_type = kwargs.get('engine_type', 'tesseract')
        max_workers = kwargs.get('max_workers', 4)
        batch_processor = BatchProcessor(
            engine_type=engine_type,
            max_workers=max_workers
        )

        # Process
        results = []
        for i, file_path in enumerate(file_paths):
            self.update_state(
                state='PROCESSING',
                meta={
                    'current': i,
                    'total': len(file_paths),
                    'status': f'Processing {i}/{len(file_paths)}: {Path(file_path).name}'
                }
            )

            try:
                result = batch_processor.document_processor.process_file(
                    Path(file_path),
                    **kwargs
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                results.append({
                    'file_path': file_path,
                    'error': str(e)
                })

        logger.info(f"Batch processing complete: {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise


@celery_app.task(base=OCRTask, name='ocr.export_result')
def export_result_task(
    result: Dict[str, Any],
    output_path: str,
    format: str = "pdf",
    **kwargs
) -> Dict[str, Any]:
    """
    Export OCR result to file

    Args:
        result: OCR result dictionary
        output_path: Output file path
        format: Export format
        **kwargs: Format options

    Returns:
        Export info dictionary
    """
    try:
        logger.info(f"Exporting result to {output_path} ({format})")

        # Export
        export_manager = ExportManager()
        success = export_manager.export(
            result,
            Path(output_path),
            format,
            **kwargs
        )

        if not success:
            raise Exception("Export failed")

        # Get file info
        file_size = Path(output_path).stat().st_size

        return {
            'success': True,
            'output_path': output_path,
            'format': format,
            'file_size': file_size
        }

    except Exception as e:
        logger.error(f"Error exporting result: {e}")
        raise


@celery_app.task(base=OCRTask, name='ocr.process_and_export')
def process_and_export_task(
    file_path: str,
    output_path: str,
    export_format: str = "pdf",
    **kwargs
) -> Dict[str, Any]:
    """
    Process document and export in one task

    Args:
        file_path: Input file path
        output_path: Output file path
        export_format: Export format
        **kwargs: Processing options

    Returns:
        Combined result
    """
    try:
        logger.info(f"Processing and exporting: {file_path} -> {output_path}")

        # Process
        engine_type = kwargs.get('engine_type', 'tesseract')
        pipeline = OCRPipeline(engine_type=engine_type)
        result = pipeline.process_file(Path(file_path), **kwargs)

        # Export
        export_manager = ExportManager()
        success = export_manager.export(
            result,
            Path(output_path),
            export_format,
            **kwargs
        )

        return {
            'success': success,
            'input_path': file_path,
            'output_path': output_path,
            'text': result.get('text', ''),
            'confidence': result.get('confidence', 0.0)
        }

    except Exception as e:
        logger.error(f"Error in process and export: {e}")
        raise


# Task chains and groups
def create_batch_processing_chain(file_paths: List[str], **kwargs):
    """
    Create Celery chain for batch processing

    Args:
        file_paths: List of file paths
        **kwargs: Processing options

    Returns:
        Celery chain
    """
    # Create task group
    job = group(
        process_document_task.s(file_path, **kwargs)
        for file_path in file_paths
    )

    return job


def create_process_and_export_chain(
    file_path: str,
    output_path: str,
    export_format: str = "pdf",
    **kwargs
):
    """
    Create chain for processing and exporting

    Args:
        file_path: Input file path
        output_path: Output file path
        export_format: Export format
        **kwargs: Options

    Returns:
        Celery chain
    """
    return chain(
        process_document_task.s(file_path, **kwargs),
        export_result_task.s(output_path, export_format, **kwargs)
    )


# Task status utilities
def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get task status

    Args:
        task_id: Celery task ID

    Returns:
        Status dictionary
    """
    try:
        result = AsyncResult(task_id, app=celery_app)

        return {
            'task_id': task_id,
            'state': result.state,
            'info': result.info if isinstance(result.info, dict) else {},
            'ready': result.ready(),
            'successful': result.successful() if result.ready() else False,
            'failed': result.failed() if result.ready() else False,
        }

    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        return {
            'task_id': task_id,
            'state': 'UNKNOWN',
            'error': str(e)
        }


def cancel_task(task_id: str) -> bool:
    """
    Cancel running task

    Args:
        task_id: Celery task ID

    Returns:
        Success status
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        logger.info(f"Task {task_id} cancelled")
        return True
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        return False


# Periodic tasks (if using celery beat)
@celery_app.task(name='ocr.cleanup_old_files')
def cleanup_old_files_task():
    """Clean up old processed files"""
    try:
        from datetime import timedelta
        import time

        max_age_days = 7
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)

        deleted_count = 0

        # Clean upload directory
        for file_path in config.upload_path.glob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                deleted_count += 1

        # Clean storage directory
        for file_path in config.storage_path.glob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old files")
        return {'deleted_count': deleted_count}

    except Exception as e:
        logger.error(f"Error cleaning up files: {e}")
        raise


# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'ocr.cleanup_old_files',
        'schedule': 86400.0,  # Once per day
    },
}
