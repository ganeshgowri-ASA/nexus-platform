"""
Celery Tasks for Image Recognition Module

Asynchronous task processing for:
- Image classification
- Object detection
- Batch processing
- Feature extraction
- Model training
- Quality assessment
"""

import logging
import time
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
from uuid import UUID
import json
import traceback

# Celery imports
try:
    from celery import Task, shared_task, group, chain, chord
    from celery.signals import task_prerun, task_postrun, task_failure
    from celery.utils.log import get_task_logger
except ImportError:
    # Fallback for testing without Celery
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    task_prerun = task_postrun = task_failure = None
    get_task_logger = lambda name: logging.getLogger(name)

# Redis imports
try:
    import redis
    from redis import Redis
except ImportError:
    redis = None
    Redis = None

# Database and models
from sqlalchemy.orm import Session
from .db_models import (
    RecognitionJob, Image, Prediction, Label,
    RecognitionModel, Annotation, JobStatus, JobType
)
from .schemas import (
    RecognitionJobUpdate, ImageCreate, ImageUpdate,
    PredictionCreate, ClassificationRequest, DetectionRequest
)

# Recognition modules
from .classifier import ImageClassifier, MultiLabelClassifier
from .detection import ObjectDetector
from .features import FeatureExtractor
from .quality import QualityAssessment
from .training import ModelTrainer
from .preprocessing import ImagePreprocessor

# Logger
logger = get_task_logger(__name__)


# Redis client for caching
REDIS_CLIENT: Optional[Redis] = None


def get_redis_client() -> Optional[Redis]:
    """Get Redis client instance."""
    global REDIS_CLIENT
    if REDIS_CLIENT is None and redis:
        try:
            import os
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            REDIS_CLIENT = redis.from_url(redis_url, decode_responses=True)
            logger.info("Connected to Redis for caching")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}")
            REDIS_CLIENT = None
    return REDIS_CLIENT


def get_db_session() -> Session:
    """
    Get database session.
    In production, this would use a proper session factory.
    """
    # This is a placeholder - implement based on your DB setup
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os

    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/nexus')
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def cache_result(key: str, value: Any, ttl: int = 3600) -> bool:
    """Cache result in Redis."""
    client = get_redis_client()
    if client:
        try:
            client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
    return False


def get_cached_result(key: str) -> Optional[Any]:
    """Get cached result from Redis."""
    client = get_redis_client()
    if client:
        try:
            value = client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
    return None


class CallbackTask(Task):
    """Base task with callbacks for progress tracking."""

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(f"Task {task_id} completed successfully")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(f"Task {task_id} failed: {exc}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(f"Task {task_id} retrying: {exc}")

    def update_progress(
        self,
        job_id: Union[str, UUID],
        processed: int,
        total: int,
        status: str = "processing"
    ):
        """Update job progress in database."""
        try:
            db = get_db_session()
            try:
                job = db.query(RecognitionJob).filter(
                    RecognitionJob.id == str(job_id)
                ).first()

                if job:
                    job.processed_images = processed
                    job.total_images = total
                    job.progress_percentage = (processed / total * 100) if total > 0 else 0
                    job.status = status
                    db.commit()

                    # Publish progress via Redis pub/sub
                    self.publish_progress(job_id, processed, total)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error updating progress: {e}")

    def publish_progress(self, job_id: Union[str, UUID], processed: int, total: int):
        """Publish progress update via Redis pub/sub."""
        client = get_redis_client()
        if client:
            try:
                message = {
                    'job_id': str(job_id),
                    'processed': processed,
                    'total': total,
                    'progress': (processed / total * 100) if total > 0 else 0,
                    'timestamp': datetime.utcnow().isoformat()
                }
                client.publish(f'job_progress:{job_id}', json.dumps(message))
            except Exception as e:
                logger.warning(f"Could not publish progress: {e}")


@shared_task(
    bind=True,
    base=CallbackTask,
    name='image_recognition.classify_image',
    max_retries=3,
    default_retry_delay=60
)
def classify_image_task(
    self,
    job_id: str,
    image_id: str,
    model_type: str = "resnet50",
    model_id: Optional[str] = None,
    top_k: int = 5,
    confidence_threshold: float = 0.1
) -> Dict[str, Any]:
    """
    Async task for image classification.

    Args:
        job_id: Recognition job ID
        image_id: Image ID to classify
        model_type: Model type to use
        model_id: Optional custom model ID
        top_k: Number of top predictions
        confidence_threshold: Minimum confidence

    Returns:
        Classification results
    """
    logger.info(f"Starting classification for image {image_id}")

    db = get_db_session()
    try:
        # Get image record
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise ValueError(f"Image {image_id} not found")

        # Check cache
        cache_key = f"classification:{image_id}:{model_type}:{top_k}"
        cached = get_cached_result(cache_key)
        if cached:
            logger.info(f"Using cached results for image {image_id}")
            return cached

        # Initialize classifier
        classifier = ImageClassifier(model_type=model_type)

        # Load and classify image
        start_time = time.time()
        result = classifier.classify(
            image.file_path,
            top_k=top_k,
            confidence_threshold=confidence_threshold
        )
        processing_time = (time.time() - start_time) * 1000

        if not result.get('success'):
            raise Exception(result.get('error', 'Classification failed'))

        # Store predictions in database
        predictions_created = []
        for rank, pred in enumerate(result['predictions'], 1):
            # Get or create label
            label = db.query(Label).filter(Label.name == pred['label']).first()
            if not label:
                label = Label(
                    name=pred['label'],
                    display_name=pred['label'].replace('_', ' ').title(),
                    category='imagenet'
                )
                db.add(label)
                db.flush()

            # Create prediction
            prediction = Prediction(
                image_id=image_id,
                label_id=label.id,
                label_name=pred['label'],
                confidence=pred['confidence'],
                score=pred['confidence'],
                model_name=model_type,
                rank=rank,
                metadata={
                    'class_id': pred.get('class_id'),
                    'processing_time_ms': processing_time
                }
            )
            db.add(prediction)
            predictions_created.append({
                'label': pred['label'],
                'confidence': pred['confidence'],
                'rank': rank
            })

        # Update image record
        image.processed = True
        image.status = 'completed'
        image.processing_time_ms = processing_time

        # Update job progress
        job = db.query(RecognitionJob).filter(RecognitionJob.id == job_id).first()
        if job:
            job.processed_images += 1
            job.successful_images += 1
            job.progress_percentage = (job.processed_images / job.total_images * 100) if job.total_images > 0 else 0

        db.commit()

        result_data = {
            'success': True,
            'image_id': str(image_id),
            'predictions': predictions_created,
            'processing_time_ms': processing_time,
            'model_type': model_type
        }

        # Cache results
        cache_result(cache_key, result_data, ttl=3600)

        logger.info(f"Classification completed for image {image_id}")
        return result_data

    except Exception as e:
        logger.error(f"Error in classification task: {e}\n{traceback.format_exc()}")

        # Update job with error
        try:
            job = db.query(RecognitionJob).filter(RecognitionJob.id == job_id).first()
            if job:
                job.failed_images += 1
                job.processed_images += 1

            image = db.query(Image).filter(Image.id == image_id).first()
            if image:
                image.status = 'failed'
                image.metadata['error'] = str(e)

            db.commit()
        except:
            pass

        # Retry if possible
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {
            'success': False,
            'error': str(e),
            'image_id': str(image_id)
        }
    finally:
        db.close()


@shared_task(
    bind=True,
    base=CallbackTask,
    name='image_recognition.detect_objects',
    max_retries=3
)
def detect_objects_task(
    self,
    job_id: str,
    image_id: str,
    model_type: str = "yolo",
    confidence_threshold: float = 0.5,
    iou_threshold: float = 0.4
) -> Dict[str, Any]:
    """
    Async task for object detection.

    Args:
        job_id: Recognition job ID
        image_id: Image ID
        model_type: Detection model type
        confidence_threshold: Detection confidence threshold
        iou_threshold: IOU threshold for NMS

    Returns:
        Detection results
    """
    logger.info(f"Starting object detection for image {image_id}")

    db = get_db_session()
    try:
        # Get image
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise ValueError(f"Image {image_id} not found")

        # Check cache
        cache_key = f"detection:{image_id}:{model_type}"
        cached = get_cached_result(cache_key)
        if cached:
            return cached

        # Initialize detector
        detector = ObjectDetector(model_type=model_type)

        # Run detection
        start_time = time.time()
        result = detector.detect(
            image.file_path,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold
        )
        processing_time = (time.time() - start_time) * 1000

        if not result.get('success'):
            raise Exception(result.get('error', 'Detection failed'))

        # Store detections
        detections_created = []
        for rank, det in enumerate(result['detections'], 1):
            # Get or create label
            label = db.query(Label).filter(Label.name == det['label']).first()
            if not label:
                label = Label(
                    name=det['label'],
                    display_name=det['label'].replace('_', ' ').title(),
                    category='coco'
                )
                db.add(label)
                db.flush()

            # Create prediction with bbox
            bbox = det['bbox']
            prediction = Prediction(
                image_id=image_id,
                label_id=label.id,
                label_name=det['label'],
                confidence=det['confidence'],
                score=det['confidence'],
                bbox_x=bbox['x'],
                bbox_y=bbox['y'],
                bbox_width=bbox['width'],
                bbox_height=bbox['height'],
                model_name=model_type,
                rank=rank,
                attributes=det.get('attributes', {})
            )
            db.add(prediction)
            detections_created.append(det)

        # Update image
        image.processed = True
        image.status = 'completed'
        image.processing_time_ms = processing_time

        # Update job
        job = db.query(RecognitionJob).filter(RecognitionJob.id == job_id).first()
        if job:
            job.processed_images += 1
            job.successful_images += 1

        db.commit()

        result_data = {
            'success': True,
            'image_id': str(image_id),
            'detections': detections_created,
            'num_detections': len(detections_created),
            'processing_time_ms': processing_time
        }

        cache_result(cache_key, result_data)

        return result_data

    except Exception as e:
        logger.error(f"Error in detection task: {e}")

        try:
            job = db.query(RecognitionJob).filter(RecognitionJob.id == job_id).first()
            if job:
                job.failed_images += 1
            db.commit()
        except:
            pass

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@shared_task(
    bind=True,
    base=CallbackTask,
    name='image_recognition.extract_features',
    max_retries=2
)
def extract_features_task(
    self,
    job_id: str,
    image_id: str,
    model_type: str = "resnet50"
) -> Dict[str, Any]:
    """
    Extract feature embeddings from image.

    Args:
        job_id: Recognition job ID
        image_id: Image ID
        model_type: Model for feature extraction

    Returns:
        Feature extraction results
    """
    logger.info(f"Extracting features for image {image_id}")

    db = get_db_session()
    try:
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise ValueError(f"Image {image_id} not found")

        # Initialize feature extractor
        extractor = FeatureExtractor(model_type=model_type)

        # Extract features
        result = extractor.extract(image.file_path)

        if result.get('success'):
            # Store embedding vector
            image.embedding_vector = result['features'].tolist() if hasattr(result['features'], 'tolist') else list(result['features'])
            image.embedding_model = model_type
            image.processed = True
            image.status = 'completed'

            # Update job
            job = db.query(RecognitionJob).filter(RecognitionJob.id == job_id).first()
            if job:
                job.processed_images += 1
                job.successful_images += 1

            db.commit()

            return {
                'success': True,
                'image_id': str(image_id),
                'feature_size': len(image.embedding_vector),
                'model_type': model_type
            }
        else:
            raise Exception(result.get('error', 'Feature extraction failed'))

    except Exception as e:
        logger.error(f"Error in feature extraction: {e}")

        try:
            job = db.query(RecognitionJob).filter(RecognitionJob.id == job_id).first()
            if job:
                job.failed_images += 1
            db.commit()
        except:
            pass

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@shared_task(
    bind=True,
    base=CallbackTask,
    name='image_recognition.assess_quality',
    max_retries=2
)
def assess_quality_task(
    self,
    image_id: str,
    check_blur: bool = True,
    check_noise: bool = True,
    check_brightness: bool = True
) -> Dict[str, Any]:
    """
    Assess image quality.

    Args:
        image_id: Image ID
        check_blur: Check for blur
        check_noise: Check for noise
        check_brightness: Check brightness/contrast

    Returns:
        Quality assessment results
    """
    logger.info(f"Assessing quality for image {image_id}")

    db = get_db_session()
    try:
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise ValueError(f"Image {image_id} not found")

        # Assess quality
        qa = QualityAssessment()
        result = qa.assess(
            image.file_path,
            check_blur=check_blur,
            check_noise=check_noise,
            check_brightness=check_brightness,
            check_contrast=check_brightness
        )

        if result.get('success'):
            # Update image with quality metrics
            image.quality_score = result.get('quality_score', 0.0)
            image.is_blurry = result.get('is_blurry', False)
            image.is_noisy = result.get('is_noisy', False)
            image.brightness = result.get('brightness')
            image.contrast = result.get('contrast')

            db.commit()

            return {
                'success': True,
                'image_id': str(image_id),
                'quality_metrics': result
            }
        else:
            raise Exception(result.get('error', 'Quality assessment failed'))

    except Exception as e:
        logger.error(f"Error in quality assessment: {e}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@shared_task(
    bind=True,
    base=CallbackTask,
    name='image_recognition.batch_process',
    max_retries=1
)
def batch_process_job(
    self,
    job_id: str
) -> Dict[str, Any]:
    """
    Process all images in a job.

    Args:
        job_id: Recognition job ID

    Returns:
        Batch processing results
    """
    logger.info(f"Starting batch processing for job {job_id}")

    db = get_db_session()
    try:
        # Get job
        job = db.query(RecognitionJob).filter(RecognitionJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Update job status
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        db.commit()

        # Get all images in job
        images = db.query(Image).filter(
            Image.job_id == job_id,
            Image.processed == False
        ).all()

        if not images:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            db.commit()
            return {
                'success': True,
                'message': 'No images to process'
            }

        # Create tasks based on job type
        tasks = []
        for image in images:
            if job.job_type == JobType.CLASSIFICATION:
                task = classify_image_task.s(
                    job_id=str(job_id),
                    image_id=str(image.id),
                    model_type=job.model_type.value,
                    top_k=job.max_predictions,
                    confidence_threshold=job.confidence_threshold
                )
            elif job.job_type == JobType.OBJECT_DETECTION:
                task = detect_objects_task.s(
                    job_id=str(job_id),
                    image_id=str(image.id),
                    model_type=job.model_type.value,
                    confidence_threshold=job.confidence_threshold
                )
            elif job.job_type == JobType.FEATURE_EXTRACTION:
                task = extract_features_task.s(
                    job_id=str(job_id),
                    image_id=str(image.id),
                    model_type=job.model_type.value
                )
            elif job.job_type == JobType.QUALITY_ASSESSMENT:
                task = assess_quality_task.s(
                    image_id=str(image.id)
                )
            else:
                continue

            tasks.append(task)

        # Execute tasks in parallel using group
        if tasks:
            job_group = group(tasks)
            result = job_group.apply_async()

            logger.info(f"Created {len(tasks)} tasks for job {job_id}")

        return {
            'success': True,
            'job_id': str(job_id),
            'tasks_created': len(tasks),
            'message': f'Processing {len(tasks)} images'
        }

    except Exception as e:
        logger.error(f"Error in batch processing: {e}")

        try:
            job = db.query(RecognitionJob).filter(RecognitionJob.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
            db.commit()
        except:
            pass

        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@shared_task(
    bind=True,
    base=CallbackTask,
    name='image_recognition.train_model',
    max_retries=0
)
def train_model_task(
    self,
    model_id: str,
    dataset_id: str,
    training_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Train a custom model.

    Args:
        model_id: Model ID to train
        dataset_id: Training dataset ID
        training_config: Training configuration

    Returns:
        Training results
    """
    logger.info(f"Starting model training for model {model_id}")

    db = get_db_session()
    try:
        # Get model
        model = db.query(RecognitionModel).filter(
            RecognitionModel.id == model_id
        ).first()

        if not model:
            raise ValueError(f"Model {model_id} not found")

        # Initialize trainer
        trainer = ModelTrainer(
            model_type=model.model_type.value,
            num_classes=model.output_classes
        )

        # Train model
        result = trainer.train(
            dataset_id=dataset_id,
            **training_config
        )

        if result.get('success'):
            # Update model with training results
            model.training_accuracy = result.get('final_train_accuracy')
            model.validation_accuracy = result.get('final_val_accuracy')
            model.is_deployed = True

            db.commit()

            logger.info(f"Model training completed for {model_id}")

            return {
                'success': True,
                'model_id': str(model_id),
                'training_results': result
            }
        else:
            raise Exception(result.get('error', 'Training failed'))

    except Exception as e:
        logger.error(f"Error in model training: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@shared_task(name='image_recognition.cleanup_old_jobs')
def cleanup_old_jobs(days: int = 30) -> Dict[str, Any]:
    """
    Cleanup completed jobs older than specified days.

    Args:
        days: Number of days to keep

    Returns:
        Cleanup results
    """
    logger.info(f"Cleaning up jobs older than {days} days")

    db = get_db_session()
    try:
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Find old completed jobs
        old_jobs = db.query(RecognitionJob).filter(
            RecognitionJob.status == JobStatus.COMPLETED,
            RecognitionJob.completed_at < cutoff_date
        ).all()

        deleted_count = 0
        for job in old_jobs:
            db.delete(job)
            deleted_count += 1

        db.commit()

        logger.info(f"Deleted {deleted_count} old jobs")

        return {
            'success': True,
            'deleted_jobs': deleted_count
        }

    except Exception as e:
        logger.error(f"Error in cleanup: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


# Celery signal handlers
if task_prerun:
    @task_prerun.connect
    def task_prerun_handler(task_id, task, *args, **kwargs):
        """Called before task execution."""
        logger.info(f"Task starting: {task.name} [{task_id}]")


if task_postrun:
    @task_postrun.connect
    def task_postrun_handler(task_id, task, *args, **kwargs):
        """Called after task execution."""
        logger.info(f"Task finished: {task.name} [{task_id}]")


if task_failure:
    @task_failure.connect
    def task_failure_handler(task_id, exception, *args, **kwargs):
        """Called when task fails."""
        logger.error(f"Task failed [{task_id}]: {exception}")


# Task chains and workflows
def process_image_workflow(
    job_id: str,
    image_id: str,
    include_quality: bool = True,
    include_features: bool = True
) -> Any:
    """
    Create a complete image processing workflow.

    Args:
        job_id: Job ID
        image_id: Image ID
        include_quality: Include quality assessment
        include_features: Include feature extraction

    Returns:
        Celery chain
    """
    tasks = []

    # Quality assessment first
    if include_quality:
        tasks.append(assess_quality_task.s(image_id=image_id))

    # Main processing (classification or detection)
    tasks.append(classify_image_task.s(
        job_id=job_id,
        image_id=image_id
    ))

    # Feature extraction
    if include_features:
        tasks.append(extract_features_task.s(
            job_id=job_id,
            image_id=image_id
        ))

    # Create chain
    return chain(*tasks)
