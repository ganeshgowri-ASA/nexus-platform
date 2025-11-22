"""
Celery tasks for asynchronous translation processing
"""

import asyncio
from typing import List, Optional
from celery import Celery
from datetime import datetime

from ..config import config
from ..models.database import SessionLocal, TranslationJob
from ..services.translation_service import TranslationService

# Initialize Celery app
app = Celery(
    'nexus_translation',
    broker=config.celery_broker_url,
    backend=config.celery_result_backend
)

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
)


async def process_batch_translation(
    job_id: str,
    texts: List[str],
    source_language: str,
    target_language: str,
    provider: Optional[str] = None,
    glossary_id: Optional[int] = None
):
    """
    Process batch translation job

    Args:
        job_id: Job ID
        texts: List of texts to translate
        source_language: Source language code
        target_language: Target language code
        provider: Translation provider
        glossary_id: Optional glossary ID
    """
    db = SessionLocal()
    translation_service = TranslationService()

    try:
        # Get the job
        job = db.query(TranslationJob).filter(TranslationJob.job_id == job_id).first()
        if not job:
            return

        # Update job status
        job.status = "processing"
        job.started_at = datetime.utcnow()
        db.commit()

        # Process translations
        translated_texts = []
        completed = 0
        failed = 0

        for i, text in enumerate(texts):
            try:
                result = await translation_service.translate(
                    text=text,
                    source_language=source_language,
                    target_language=target_language,
                    provider=provider,
                    glossary_id=glossary_id,
                    db=db,
                    enable_quality_scoring=False  # Disable for batch to improve performance
                )

                translated_texts.append({
                    'original': text,
                    'translated': result['translated_text'],
                    'index': i
                })

                completed += 1

            except Exception as e:
                print(f"Failed to translate text {i}: {str(e)}")
                translated_texts.append({
                    'original': text,
                    'translated': None,
                    'error': str(e),
                    'index': i
                })
                failed += 1

            # Update progress
            progress = ((completed + failed) / len(texts)) * 100
            job.completed_items = completed
            job.failed_items = failed
            job.progress_percentage = progress
            db.commit()

        # Save results to file
        import json
        import os
        from ..config import config

        os.makedirs(config.upload_dir, exist_ok=True)
        result_file = os.path.join(config.upload_dir, f"{job_id}_results.json")

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(translated_texts, f, ensure_ascii=False, indent=2)

        # Update job as completed
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.result_file_path = result_file
        db.commit()

    except Exception as e:
        # Update job as failed
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()

        raise

    finally:
        db.close()


@app.task(name='translation.batch_translate')
def batch_translate_task(
    job_id: str,
    texts: List[str],
    source_language: str,
    target_language: str,
    provider: Optional[str] = None,
    glossary_id: Optional[int] = None
):
    """
    Celery task wrapper for batch translation

    Args:
        job_id: Job ID
        texts: List of texts to translate
        source_language: Source language code
        target_language: Target language code
        provider: Translation provider
        glossary_id: Optional glossary ID
    """
    # Run the async function
    asyncio.run(
        process_batch_translation(
            job_id=job_id,
            texts=texts,
            source_language=source_language,
            target_language=target_language,
            provider=provider,
            glossary_id=glossary_id
        )
    )

    return {
        'job_id': job_id,
        'status': 'completed',
        'total_items': len(texts)
    }


@app.task(name='translation.cleanup_old_jobs')
def cleanup_old_jobs(days: int = 30):
    """
    Clean up old translation jobs

    Args:
        days: Number of days to keep jobs
    """
    from datetime import timedelta
    import os

    db = SessionLocal()

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get old jobs
        old_jobs = db.query(TranslationJob).filter(
            TranslationJob.created_at < cutoff_date
        ).all()

        for job in old_jobs:
            # Delete result file if exists
            if job.result_file_path and os.path.exists(job.result_file_path):
                os.remove(job.result_file_path)

            # Delete job record
            db.delete(job)

        db.commit()

        return {
            'deleted_jobs': len(old_jobs),
            'cutoff_date': cutoff_date.isoformat()
        }

    except Exception as e:
        db.rollback()
        raise

    finally:
        db.close()
