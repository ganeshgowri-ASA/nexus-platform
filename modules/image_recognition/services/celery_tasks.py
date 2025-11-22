"""
Celery tasks for asynchronous image processing
"""
from celery import Celery
from typing import Dict, Any
import time
import logging
from datetime import datetime

from ..config.settings import settings
from .vision_service import GoogleVisionService, AWSRekognitionService, ImageProcessor

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'image_recognition',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.TASK_TIMEOUT_SECONDS,
)


@celery_app.task(bind=True, name='image_recognition.analyze_image')
def analyze_image_task(self, analysis_id: int, image_data: bytes, analysis_type: str, provider: str = 'aws') -> Dict[str, Any]:
    """
    Async task to analyze image

    Args:
        analysis_id: Database ID of the analysis record
        image_data: Image bytes
        analysis_type: Type of analysis (object_detection, classification, etc.)
        provider: Vision API provider (google or aws)

    Returns:
        Dict with analysis results
    """
    try:
        start_time = time.time()

        # Update task status
        self.update_state(state='PROCESSING', meta={'status': 'loading_image'})

        # Load image and get metadata
        image, metadata = ImageProcessor.load_image(image_data)

        # Initialize service
        self.update_state(state='PROCESSING', meta={'status': 'initializing_service'})

        if provider == 'google':
            service = GoogleVisionService(
                api_key=settings.GOOGLE_VISION_API_KEY,
                credentials_path=settings.GOOGLE_APPLICATION_CREDENTIALS
            )
        else:
            service = AWSRekognitionService(
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                region=settings.AWS_REGION
            )

        # Perform analysis
        self.update_state(state='PROCESSING', meta={'status': f'analyzing_{analysis_type}'})

        results = {}

        if analysis_type == 'object_detection':
            import asyncio
            results['objects'] = asyncio.run(service.detect_objects(image_data))

        elif analysis_type == 'image_classification':
            import asyncio
            results['labels'] = asyncio.run(service.classify_image(image_data))

        elif analysis_type == 'face_detection':
            import asyncio
            results['faces'] = asyncio.run(service.detect_faces(image_data))

        elif analysis_type == 'scene_recognition':
            if hasattr(service, 'recognize_scene'):
                import asyncio
                results['scenes'] = asyncio.run(service.recognize_scene(image_data))
            else:
                import asyncio
                results['scenes'] = asyncio.run(service.classify_image(image_data))

        processing_time_ms = int((time.time() - start_time) * 1000)

        return {
            'status': 'completed',
            'results': results,
            'metadata': metadata,
            'processing_time_ms': processing_time_ms,
            'analysis_id': analysis_id
        }

    except Exception as e:
        logger.error(f"Error in analyze_image_task: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'analysis_id': analysis_id
        }


@celery_app.task(bind=True, name='image_recognition.batch_analyze')
def batch_analyze_task(self, analysis_configs: list) -> Dict[str, Any]:
    """
    Batch process multiple images

    Args:
        analysis_configs: List of analysis configurations

    Returns:
        Dict with batch results
    """
    try:
        results = []

        for i, config in enumerate(analysis_configs):
            self.update_state(
                state='PROCESSING',
                meta={
                    'current': i + 1,
                    'total': len(analysis_configs),
                    'status': f'processing_image_{i + 1}'
                }
            )

            result = analyze_image_task(
                config['analysis_id'],
                config['image_data'],
                config['analysis_type'],
                config.get('provider', 'aws')
            )
            results.append(result)

        return {
            'status': 'completed',
            'total': len(results),
            'successful': len([r for r in results if r['status'] == 'completed']),
            'failed': len([r for r in results if r['status'] == 'failed']),
            'results': results
        }

    except Exception as e:
        logger.error(f"Error in batch_analyze_task: {e}")
        return {
            'status': 'failed',
            'error': str(e)
        }


@celery_app.task(name='image_recognition.train_custom_model')
def train_custom_model_task(model_id: int, dataset_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Train custom model

    Args:
        model_id: Database ID of the model
        dataset_path: Path to training dataset
        config: Training configuration

    Returns:
        Dict with training results
    """
    try:
        start_time = time.time()

        # Placeholder for custom model training logic
        # In production, this would integrate with TensorFlow, PyTorch, etc.

        logger.info(f"Training model {model_id} with dataset {dataset_path}")

        # Simulate training
        time.sleep(5)

        training_time = time.time() - start_time

        return {
            'status': 'completed',
            'model_id': model_id,
            'accuracy': 0.85,
            'precision': 0.83,
            'recall': 0.87,
            'f1_score': 0.85,
            'training_time_seconds': training_time
        }

    except Exception as e:
        logger.error(f"Error in train_custom_model_task: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'model_id': model_id
        }


@celery_app.task(name='image_recognition.cleanup_old_analyses')
def cleanup_old_analyses_task(days_old: int = 30) -> Dict[str, Any]:
    """
    Cleanup old analysis records

    Args:
        days_old: Delete records older than this many days

    Returns:
        Dict with cleanup results
    """
    try:
        # Placeholder for cleanup logic
        logger.info(f"Cleaning up analyses older than {days_old} days")

        return {
            'status': 'completed',
            'deleted_count': 0
        }

    except Exception as e:
        logger.error(f"Error in cleanup_old_analyses_task: {e}")
        return {
            'status': 'failed',
            'error': str(e)
        }
