"""
FastAPI Routes for Image Recognition Module

Comprehensive REST API endpoints for:
- Job management
- Image processing
- Classification, detection, segmentation
- Feature extraction and similarity search
- Model management
- Annotations and exports
- Real-time WebSocket updates
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID
import asyncio
import json
import io
import base64

# FastAPI imports
from fastapi import (
    APIRouter, Depends, HTTPException, status, UploadFile,
    File, Form, Query, Body, BackgroundTasks, WebSocket,
    WebSocketDisconnect
)
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# SQLAlchemy
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_

# Pydantic schemas
from .schemas import (
    RecognitionJobCreate, RecognitionJobUpdate, RecognitionJobResponse,
    RecognitionJobList, ImageCreate, ImageUpdate, ImageResponse,
    ImageWithPredictions, PredictionCreate, PredictionResponse,
    LabelCreate, LabelUpdate, LabelResponse,
    RecognitionModelCreate, RecognitionModelUpdate, RecognitionModelResponse,
    AnnotationCreate, AnnotationUpdate, AnnotationResponse,
    ClassificationRequest, ClassificationResponse,
    DetectionRequest, DetectionResponse,
    SegmentationRequest, SegmentationResponse,
    SimilaritySearchRequest, SimilaritySearchResponse,
    QualityAssessmentRequest, QualityAssessmentResponse,
    BatchProcessingRequest, BatchProcessingResponse,
    ExportRequest, ExportResponse,
    JobStatistics, ModelStatistics,
    WSMessage, WSJobUpdate,
    JobStatusEnum, JobTypeEnum, ModelTypeEnum
)

# Database models
from .db_models import (
    RecognitionJob, Image, Prediction, Label,
    RecognitionModel, Annotation, TrainingDataset,
    JobStatus, JobType, ModelType
)

# Tasks
from .tasks import (
    classify_image_task, detect_objects_task,
    extract_features_task, assess_quality_task,
    batch_process_job, train_model_task
)

# Recognition modules
from .classifier import ImageClassifier
from .detection import ObjectDetector
from .segmentation import ImageSegmenter
from .features import FeatureExtractor
from .quality import QualityAssessment
from .export import ExportManager

# Logger
logger = logging.getLogger(__name__)

# Router
router = APIRouter(
    prefix="/api/v1/image-recognition",
    tags=["Image Recognition"]
)

# Security
security = HTTPBearer()


# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a WebSocket client."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user {user_id}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket client."""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user."""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        for connections in self.active_connections.values():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting: {e}")


manager = ConnectionManager()


# Dependencies
def get_db() -> Session:
    """
    Get database session dependency.
    Replace with your actual DB session factory.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os

    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/nexus')
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current authenticated user.
    Replace with your actual auth implementation.
    """
    # Placeholder - implement your auth logic
    token = credentials.credentials

    # Mock user for now
    return {
        'user_id': '00000000-0000-0000-0000-000000000000',
        'username': 'testuser',
        'email': 'test@example.com',
        'roles': ['user']
    }


def require_permission(permission: str):
    """Check if user has required permission."""
    def dependency(user: Dict = Depends(get_current_user)):
        # Implement permission checking
        return user
    return dependency


# Rate limiting (basic implementation)
RATE_LIMITS: Dict[str, List[datetime]] = {}


def check_rate_limit(user_id: str, limit: int = 100, window: int = 60) -> bool:
    """
    Check if user has exceeded rate limit.

    Args:
        user_id: User ID
        limit: Max requests
        window: Time window in seconds

    Returns:
        True if within limit
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(seconds=window)

    if user_id not in RATE_LIMITS:
        RATE_LIMITS[user_id] = []

    # Remove old requests
    RATE_LIMITS[user_id] = [
        ts for ts in RATE_LIMITS[user_id]
        if ts > cutoff
    ]

    # Check limit
    if len(RATE_LIMITS[user_id]) >= limit:
        return False

    RATE_LIMITS[user_id].append(now)
    return True


# ============================================================================
# JOB MANAGEMENT ENDPOINTS
# ============================================================================

@router.post(
    "/jobs",
    response_model=RecognitionJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Recognition Job",
    description="Create a new image recognition job"
)
async def create_job(
    job_data: RecognitionJobCreate,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Create a new recognition job."""
    try:
        # Check rate limit
        if not check_rate_limit(user['user_id']):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )

        # Create job
        job = RecognitionJob(
            name=job_data.name,
            description=job_data.description,
            job_type=job_data.job_type,
            user_id=user['user_id'],
            project_id=job_data.project_id,
            model_id=job_data.model_id,
            model_type=job_data.model_type,
            model_config=job_data.model_config,
            batch_size=job_data.batch_size,
            confidence_threshold=job_data.confidence_threshold,
            max_predictions=job_data.max_predictions,
            preprocessing_config=job_data.preprocessing_config,
            metadata=job_data.metadata,
            tags=job_data.tags
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(f"Created job {job.id} for user {user['user_id']}")

        return job

    except Exception as e:
        logger.error(f"Error creating job: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/jobs/{job_id}",
    response_model=RecognitionJobResponse,
    summary="Get Job",
    description="Get recognition job by ID"
)
async def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Get job by ID."""
    job = db.query(RecognitionJob).filter(
        RecognitionJob.id == job_id,
        RecognitionJob.user_id == user['user_id']
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return job


@router.get(
    "/jobs",
    response_model=RecognitionJobList,
    summary="List Jobs",
    description="List all recognition jobs for current user"
)
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[JobStatusEnum] = None,
    job_type_filter: Optional[JobTypeEnum] = None,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """List jobs with pagination and filtering."""
    query = db.query(RecognitionJob).filter(
        RecognitionJob.user_id == user['user_id']
    )

    # Apply filters
    if status_filter:
        query = query.filter(RecognitionJob.status == status_filter)
    if job_type_filter:
        query = query.filter(RecognitionJob.job_type == job_type_filter)

    # Get total count
    total = query.count()

    # Get paginated results
    jobs = query.order_by(desc(RecognitionJob.created_at)).offset(skip).limit(limit).all()

    return {
        'jobs': jobs,
        'total': total,
        'page': skip // limit + 1,
        'page_size': limit
    }


@router.patch(
    "/jobs/{job_id}",
    response_model=RecognitionJobResponse,
    summary="Update Job",
    description="Update recognition job"
)
async def update_job(
    job_id: UUID,
    job_update: RecognitionJobUpdate,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Update job."""
    job = db.query(RecognitionJob).filter(
        RecognitionJob.id == job_id,
        RecognitionJob.user_id == user['user_id']
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Update fields
    update_data = job_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)

    return job


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Job",
    description="Delete recognition job and all associated data"
)
async def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Delete job."""
    job = db.query(RecognitionJob).filter(
        RecognitionJob.id == job_id,
        RecognitionJob.user_id == user['user_id']
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    db.delete(job)
    db.commit()

    logger.info(f"Deleted job {job_id}")


@router.post(
    "/jobs/{job_id}/cancel",
    response_model=RecognitionJobResponse,
    summary="Cancel Job",
    description="Cancel a running job"
)
async def cancel_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Cancel job."""
    job = db.query(RecognitionJob).filter(
        RecognitionJob.id == job_id,
        RecognitionJob.user_id == user['user_id']
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job cannot be cancelled"
        )

    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(job)

    return job


@router.post(
    "/jobs/{job_id}/start",
    response_model=Dict[str, Any],
    summary="Start Job Processing",
    description="Start processing images in job"
)
async def start_job(
    job_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Start job processing."""
    job = db.query(RecognitionJob).filter(
        RecognitionJob.id == job_id,
        RecognitionJob.user_id == user['user_id']
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if job.status != JobStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job already started or completed"
        )

    # Start batch processing task
    task = batch_process_job.delay(str(job_id))

    return {
        'success': True,
        'job_id': str(job_id),
        'task_id': task.id if hasattr(task, 'id') else None,
        'message': 'Job processing started'
    }


# ============================================================================
# IMAGE UPLOAD AND PROCESSING ENDPOINTS
# ============================================================================

@router.post(
    "/jobs/{job_id}/upload",
    response_model=ImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Image",
    description="Upload an image to a job"
)
async def upload_image(
    job_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Upload image to job."""
    import os
    from PIL import Image as PILImage

    # Verify job exists and belongs to user
    job = db.query(RecognitionJob).filter(
        RecognitionJob.id == job_id,
        RecognitionJob.user_id == user['user_id']
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    try:
        # Read file
        contents = await file.read()

        # Validate image
        try:
            img = PILImage.open(io.BytesIO(contents))
            width, height = img.size
            channels = len(img.getbands())
            color_mode = img.mode
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image file: {e}"
            )

        # Generate filename
        import uuid
        file_ext = Path(file.filename).suffix
        filename = f"{uuid.uuid4()}{file_ext}"

        # Save file (implement your storage logic)
        storage_path = os.getenv('STORAGE_PATH', '/tmp/nexus/images')
        os.makedirs(storage_path, exist_ok=True)
        file_path = os.path.join(storage_path, filename)

        with open(file_path, 'wb') as f:
            f.write(contents)

        # Create image record
        image = Image(
            job_id=job_id,
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(contents),
            file_format=file_ext.lstrip('.'),
            width=width,
            height=height,
            channels=channels,
            color_mode=color_mode
        )

        db.add(image)

        # Update job total images
        job.total_images += 1

        db.commit()
        db.refresh(image)

        logger.info(f"Uploaded image {image.id} to job {job_id}")

        return image

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/images/{image_id}",
    response_model=ImageWithPredictions,
    summary="Get Image",
    description="Get image with predictions"
)
async def get_image(
    image_id: UUID,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Get image with predictions."""
    image = db.query(Image).join(RecognitionJob).filter(
        Image.id == image_id,
        RecognitionJob.user_id == user['user_id']
    ).first()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )

    return image


# ============================================================================
# CLASSIFICATION ENDPOINTS
# ============================================================================

@router.post(
    "/classify",
    response_model=ClassificationResponse,
    summary="Classify Image",
    description="Classify a single image (synchronous)"
)
async def classify_image(
    request: ClassificationRequest,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Classify image synchronously."""
    try:
        # Load image
        from PIL import Image as PILImage
        import requests

        if request.image_url:
            response = requests.get(str(request.image_url))
            image = PILImage.open(io.BytesIO(response.content))
        elif request.image_base64:
            image_data = base64.b64decode(request.image_base64)
            image = PILImage.open(io.BytesIO(image_data))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No image provided"
            )

        # Classify
        classifier = ImageClassifier(model_type=request.model_type.value)
        result = classifier.classify(
            image,
            top_k=request.top_k,
            confidence_threshold=request.confidence_threshold
        )

        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Classification failed')
            )

        return ClassificationResponse(
            success=True,
            predictions=result['predictions'],
            processing_time_ms=result['processing_time_ms'],
            model_name=result['model_name'],
            model_version=result.get('model_version'),
            image_properties={
                'width': image.width,
                'height': image.height,
                'mode': image.mode
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in classification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/classify/batch",
    response_model=BatchProcessingResponse,
    summary="Batch Classify",
    description="Classify multiple images (asynchronous)"
)
async def batch_classify(
    request: BatchProcessingRequest,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Batch classify images."""
    # Get job
    job = db.query(RecognitionJob).filter(
        RecognitionJob.id == request.job_id,
        RecognitionJob.user_id == user['user_id']
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Start processing
    task = batch_process_job.delay(str(request.job_id))

    return BatchProcessingResponse(
        success=True,
        job_id=request.job_id,
        total_images=len(request.image_urls),
        status=JobStatusEnum.PROCESSING,
        message="Batch processing started"
    )


# ============================================================================
# OBJECT DETECTION ENDPOINTS
# ============================================================================

@router.post(
    "/detect",
    response_model=DetectionResponse,
    summary="Detect Objects",
    description="Detect objects in an image (synchronous)"
)
async def detect_objects(
    request: DetectionRequest,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Detect objects in image."""
    try:
        # Load image
        from PIL import Image as PILImage
        import requests

        if request.image_url:
            response = requests.get(str(request.image_url))
            image = PILImage.open(io.BytesIO(response.content))
        elif request.image_base64:
            image_data = base64.b64decode(request.image_base64)
            image = PILImage.open(io.BytesIO(image_data))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No image provided"
            )

        # Detect
        detector = ObjectDetector(model_type=request.model_type.value)
        result = detector.detect(
            image,
            confidence_threshold=request.confidence_threshold,
            iou_threshold=request.iou_threshold
        )

        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Detection failed')
            )

        return DetectionResponse(
            success=True,
            detections=result['detections'],
            num_detections=result.get('num_detections', len(result['detections'])),
            processing_time_ms=result['processing_time_ms'],
            model_name=result['model_name'],
            model_version=result.get('model_version'),
            image_properties={
                'width': image.width,
                'height': image.height,
                'mode': image.mode
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# SEGMENTATION ENDPOINTS
# ============================================================================

@router.post(
    "/segment",
    response_model=SegmentationResponse,
    summary="Segment Image",
    description="Perform image segmentation"
)
async def segment_image(
    request: SegmentationRequest,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Segment image."""
    try:
        # Load image
        from PIL import Image as PILImage
        import requests

        if request.image_url:
            response = requests.get(str(request.image_url))
            image = PILImage.open(io.BytesIO(response.content))
        elif request.image_base64:
            image_data = base64.b64decode(request.image_base64)
            image = PILImage.open(io.BytesIO(image_data))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No image provided"
            )

        # Segment
        segmenter = ImageSegmenter(
            segmentation_type=request.segmentation_type
        )
        result = segmenter.segment(
            image,
            confidence_threshold=request.confidence_threshold
        )

        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Segmentation failed')
            )

        return SegmentationResponse(
            success=True,
            segments=result.get('segments', []),
            num_segments=result.get('num_segments', 0),
            mask_url=result.get('mask_url'),
            processing_time_ms=result.get('processing_time_ms', 0),
            model_name=result.get('model_name', 'segmentation'),
            image_properties={
                'width': image.width,
                'height': image.height,
                'mode': image.mode
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in segmentation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# FEATURE EXTRACTION AND SIMILARITY ENDPOINTS
# ============================================================================

@router.post(
    "/features/extract",
    response_model=Dict[str, Any],
    summary="Extract Features",
    description="Extract feature embeddings from image"
)
async def extract_features(
    image_id: UUID,
    model_type: str = "resnet50",
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Extract features from image."""
    image = db.query(Image).join(RecognitionJob).filter(
        Image.id == image_id,
        RecognitionJob.user_id == user['user_id']
    ).first()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )

    try:
        extractor = FeatureExtractor(model_type=model_type)
        result = extractor.extract(image.file_path)

        if result.get('success'):
            # Update image with embeddings
            image.embedding_vector = result['features'].tolist()
            image.embedding_model = model_type
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
        logger.error(f"Error extracting features: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/features/similarity",
    response_model=SimilaritySearchResponse,
    summary="Find Similar Images",
    description="Find similar images using feature embeddings"
)
async def find_similar_images(
    request: SimilaritySearchRequest,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Find similar images."""
    try:
        # Get query image embeddings
        if request.image_id:
            query_image = db.query(Image).join(RecognitionJob).filter(
                Image.id == request.image_id,
                RecognitionJob.user_id == user['user_id']
            ).first()

            if not query_image or not query_image.embedding_vector:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Image or embeddings not found"
                )

            query_vector = query_image.embedding_vector
        else:
            # Extract from provided image
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image ID required for similarity search"
            )

        # Find similar images using cosine similarity
        # This is a simple implementation - in production use vector DB
        import numpy as np

        query_np = np.array(query_vector)

        # Get candidate images
        candidates_query = db.query(Image).join(RecognitionJob).filter(
            RecognitionJob.user_id == user['user_id'],
            Image.embedding_vector.isnot(None),
            Image.id != request.image_id
        )

        if request.search_in_job_id:
            candidates_query = candidates_query.filter(
                Image.job_id == request.search_in_job_id
            )

        candidates = candidates_query.limit(1000).all()

        # Calculate similarities
        similarities = []
        for candidate in candidates:
            candidate_np = np.array(candidate.embedding_vector)
            similarity = np.dot(query_np, candidate_np) / (
                np.linalg.norm(query_np) * np.linalg.norm(candidate_np)
            )

            if similarity >= request.threshold:
                similarities.append({
                    'image_id': str(candidate.id),
                    'filename': candidate.filename,
                    'similarity': float(similarity),
                    'file_path': candidate.file_path
                })

        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        similarities = similarities[:request.top_k]

        return SimilaritySearchResponse(
            success=True,
            similar_images=similarities,
            processing_time_ms=0  # Placeholder
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in similarity search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# QUALITY ASSESSMENT ENDPOINTS
# ============================================================================

@router.post(
    "/quality/assess",
    response_model=QualityAssessmentResponse,
    summary="Assess Image Quality",
    description="Assess image quality metrics"
)
async def assess_quality(
    request: QualityAssessmentRequest,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Assess image quality."""
    try:
        # Get image
        if request.image_id:
            image = db.query(Image).join(RecognitionJob).filter(
                Image.id == request.image_id,
                RecognitionJob.user_id == user['user_id']
            ).first()

            if not image:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Image not found"
                )

            image_path = image.file_path
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image ID required"
            )

        # Assess quality
        qa = QualityAssessment()
        result = qa.assess(
            image_path,
            check_blur=request.check_blur,
            check_noise=request.check_noise,
            check_brightness=request.check_brightness,
            check_contrast=request.check_contrast
        )

        if result.get('success'):
            # Update image record
            if request.image_id:
                image.quality_score = result.get('quality_score', 0.0)
                image.is_blurry = result.get('is_blurry', False)
                image.is_noisy = result.get('is_noisy', False)
                image.brightness = result.get('brightness')
                image.contrast = result.get('contrast')
                db.commit()

            return QualityAssessmentResponse(
                success=True,
                quality_score=result['quality_score'],
                is_blurry=result.get('is_blurry', False),
                blur_score=result.get('blur_score'),
                is_noisy=result.get('is_noisy', False),
                noise_score=result.get('noise_score'),
                brightness=result.get('brightness', 0.0),
                contrast=result.get('contrast', 0.0),
                recommendations=result.get('recommendations', []),
                image_properties=result.get('image_properties', {})
            )
        else:
            raise Exception(result.get('error', 'Quality assessment failed'))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quality assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# MODEL MANAGEMENT ENDPOINTS
# ============================================================================

@router.get(
    "/models",
    response_model=List[RecognitionModelResponse],
    summary="List Models",
    description="List all available models"
)
async def list_models(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    model_type: Optional[ModelTypeEnum] = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """List available models."""
    query = db.query(RecognitionModel).filter(
        or_(
            RecognitionModel.is_public == True,
            RecognitionModel.user_id == user['user_id']
        )
    )

    if model_type:
        query = query.filter(RecognitionModel.model_type == model_type)

    if is_active:
        query = query.filter(RecognitionModel.is_active == True)

    models = query.order_by(desc(RecognitionModel.created_at)).offset(skip).limit(limit).all()

    return models


@router.post(
    "/models",
    response_model=RecognitionModelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Model",
    description="Register a new model"
)
async def create_model(
    model_data: RecognitionModelCreate,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Create new model."""
    try:
        model = RecognitionModel(
            name=model_data.name,
            display_name=model_data.display_name,
            description=model_data.description,
            model_type=model_data.model_type,
            version=model_data.version,
            model_path=model_data.model_path,
            weights_path=model_data.weights_path,
            config_path=model_data.config_path,
            architecture=model_data.architecture,
            input_shape=model_data.input_shape,
            output_classes=model_data.output_classes,
            supports_classification=model_data.supports_classification,
            supports_detection=model_data.supports_detection,
            supports_segmentation=model_data.supports_segmentation,
            user_id=user['user_id'],
            is_public=model_data.is_public,
            is_pretrained=model_data.is_pretrained,
            metadata=model_data.metadata,
            tags=model_data.tags
        )

        db.add(model)
        db.commit()
        db.refresh(model)

        logger.info(f"Created model {model.id}")

        return model

    except Exception as e:
        logger.error(f"Error creating model: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# STATISTICS AND ANALYTICS ENDPOINTS
# ============================================================================

@router.get(
    "/stats/jobs",
    response_model=JobStatistics,
    summary="Job Statistics",
    description="Get job statistics for current user"
)
async def get_job_statistics(
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Get job statistics."""
    stats = db.query(
        func.count(RecognitionJob.id).label('total_jobs'),
        func.count(RecognitionJob.id).filter(RecognitionJob.status == JobStatus.PENDING).label('pending_jobs'),
        func.count(RecognitionJob.id).filter(RecognitionJob.status == JobStatus.PROCESSING).label('processing_jobs'),
        func.count(RecognitionJob.id).filter(RecognitionJob.status == JobStatus.COMPLETED).label('completed_jobs'),
        func.count(RecognitionJob.id).filter(RecognitionJob.status == JobStatus.FAILED).label('failed_jobs'),
    ).filter(
        RecognitionJob.user_id == user['user_id']
    ).first()

    # Get image and prediction counts
    image_count = db.query(func.count(Image.id)).join(RecognitionJob).filter(
        RecognitionJob.user_id == user['user_id']
    ).scalar()

    prediction_count = db.query(func.count(Prediction.id)).join(Image).join(RecognitionJob).filter(
        RecognitionJob.user_id == user['user_id']
    ).scalar()

    # Get average confidence and processing time
    avg_confidence = db.query(func.avg(Prediction.confidence)).join(Image).join(RecognitionJob).filter(
        RecognitionJob.user_id == user['user_id']
    ).scalar() or 0.0

    avg_processing_time = db.query(func.avg(Image.processing_time_ms)).join(RecognitionJob).filter(
        RecognitionJob.user_id == user['user_id']
    ).scalar() or 0.0

    return JobStatistics(
        total_jobs=stats.total_jobs or 0,
        pending_jobs=stats.pending_jobs or 0,
        processing_jobs=stats.processing_jobs or 0,
        completed_jobs=stats.completed_jobs or 0,
        failed_jobs=stats.failed_jobs or 0,
        total_images=image_count or 0,
        total_predictions=prediction_count or 0,
        average_confidence=float(avg_confidence),
        average_processing_time_ms=float(avg_processing_time)
    )


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

@router.post(
    "/export",
    response_model=ExportResponse,
    summary="Export Results",
    description="Export job results in various formats"
)
async def export_results(
    request: ExportRequest,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user)
):
    """Export job results."""
    job = db.query(RecognitionJob).filter(
        RecognitionJob.id == request.job_id,
        RecognitionJob.user_id == user['user_id']
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    try:
        exporter = ExportManager()
        result = exporter.export_job(
            job_id=str(request.job_id),
            export_format=request.export_format,
            include_images=request.include_images,
            include_metadata=request.include_metadata,
            filter_confidence=request.filter_confidence
        )

        if result.get('success'):
            return ExportResponse(
                success=True,
                download_url=result['download_url'],
                file_size=result['file_size'],
                format=request.export_format,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
        else:
            raise Exception(result.get('error', 'Export failed'))

    except Exception as e:
        logger.error(f"Error exporting results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str
):
    """
    WebSocket endpoint for real-time updates.

    Clients can connect to receive real-time job progress updates.
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle different message types
                if message.get('type') == 'subscribe_job':
                    job_id = message.get('job_id')
                    # Subscribe to job updates
                    await manager.send_personal_message(
                        {
                            'type': 'subscribed',
                            'job_id': job_id,
                            'timestamp': datetime.utcnow().isoformat()
                        },
                        user_id
                    )

                elif message.get('type') == 'ping':
                    # Heartbeat
                    await manager.send_personal_message(
                        {'type': 'pong', 'timestamp': datetime.utcnow().isoformat()},
                        user_id
                    )

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from WebSocket: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket disconnected: {user_id}")
