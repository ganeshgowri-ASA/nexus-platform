"""
Celery tasks for asynchronous image processing
"""
from celery import Celery
import os
from typing import Dict, Any

from modules.image_recognition.models.db_connection import get_db_context
from modules.image_recognition.services.analysis_service import AnalysisService

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "image_recognition",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes
    task_soft_time_limit=540,  # 9 minutes
)


@celery_app.task(bind=True, name="image_recognition.analyze_image")
def analyze_image_task(self, analysis_id: int) -> Dict[str, Any]:
    """
    Asynchronous task to analyze an image

    Args:
        analysis_id: ID of the ImageAnalysis record

    Returns:
        Dict with analysis results
    """
    try:
        with get_db_context() as db:
            service = AnalysisService(db)
            analysis = service.process_analysis(analysis_id)

            return {
                "status": "success",
                "analysis_id": analysis.id,
                "analysis_status": analysis.status.value,
                "confidence_score": analysis.confidence_score
            }

    except Exception as e:
        # Update task state
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise


@celery_app.task(bind=True, name="image_recognition.batch_analyze")
def batch_analyze_task(self, analysis_ids: list) -> Dict[str, Any]:
    """
    Asynchronous task to analyze multiple images in batch

    Args:
        analysis_ids: List of ImageAnalysis IDs

    Returns:
        Dict with batch results
    """
    results = []
    failed = []

    for analysis_id in analysis_ids:
        try:
            result = analyze_image_task.apply(args=[analysis_id])
            results.append(result.get())
        except Exception as e:
            failed.append({
                "analysis_id": analysis_id,
                "error": str(e)
            })

    return {
        "status": "completed",
        "total": len(analysis_ids),
        "successful": len(results),
        "failed": len(failed),
        "results": results,
        "errors": failed
    }


@celery_app.task(name="image_recognition.cleanup_old_analyses")
def cleanup_old_analyses_task(days: int = 30) -> Dict[str, Any]:
    """
    Periodic task to cleanup old analysis records

    Args:
        days: Delete analyses older than this many days

    Returns:
        Dict with cleanup results
    """
    from datetime import datetime, timedelta
    from modules.image_recognition.models.database import ImageAnalysis

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        with get_db_context() as db:
            # Delete old completed analyses
            deleted = db.query(ImageAnalysis).filter(
                ImageAnalysis.created_at < cutoff_date,
                ImageAnalysis.status == "completed"
            ).delete()

            return {
                "status": "success",
                "deleted_count": deleted
            }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(name="image_recognition.retry_failed_analyses")
def retry_failed_analyses_task(max_retries: int = 3) -> Dict[str, Any]:
    """
    Periodic task to retry failed analyses

    Args:
        max_retries: Maximum number of retry attempts

    Returns:
        Dict with retry results
    """
    from modules.image_recognition.models.database import ImageAnalysis, AnalysisStatus

    try:
        with get_db_context() as db:
            # Get failed analyses that haven't exceeded max retries
            failed_analyses = db.query(ImageAnalysis).filter(
                ImageAnalysis.status == AnalysisStatus.FAILED,
                ImageAnalysis.retry_count < max_retries
            ).all()

            retried = []
            for analysis in failed_analyses:
                try:
                    # Queue for retry
                    task = analyze_image_task.delay(analysis.id)
                    retried.append({
                        "analysis_id": analysis.id,
                        "task_id": task.id
                    })
                except Exception as e:
                    pass

            return {
                "status": "success",
                "retried_count": len(retried),
                "tasks": retried
            }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }


# Periodic task schedule (optional - configure in celery beat)
celery_app.conf.beat_schedule = {
    "cleanup-old-analyses": {
        "task": "image_recognition.cleanup_old_analyses",
        "schedule": 86400.0,  # Run daily
        "args": (30,)  # Delete analyses older than 30 days
    },
    "retry-failed-analyses": {
        "task": "image_recognition.retry_failed_analyses",
        "schedule": 3600.0,  # Run hourly
        "args": (3,)  # Max 3 retries
    }
}
