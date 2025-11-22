"""
FastAPI application for Image Recognition module
"""
<<<<<<< HEAD
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
import logging
from datetime import datetime, timedelta

from ..models.database import Base, ImageAnalysis, DetectedObject, DetectedFace, CustomModel, AnalysisStatus, AnalysisType
from ..models.schemas import (
    ImageAnalysisRequest, ImageAnalysisResponse, CustomModelTrainingRequest,
    CustomModelResponse, AnalyticsResponse, DetectedObjectResponse, DetectedFaceResponse
)
from ..config.settings import settings
from ..services.vision_service import ImageProcessor
from ..services.celery_tasks import analyze_image_task, train_custom_model_task

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="NEXUS Image Recognition API - Object detection, classification, face detection, and scene recognition"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
=======
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from modules.image_recognition.models.db_connection import get_db, init_db
from modules.image_recognition.models.schemas import (
    ImageAnalysisRequest,
    ImageAnalysisResponse,
    AnalysisStatusResponse,
    CustomModelCreate,
    CustomModelResponse,
    AnalyticsResponse,
    BatchAnalysisRequest
)
from modules.image_recognition.services.analysis_service import AnalysisService
from modules.image_recognition.models.database import CustomModel, ImageAnalysis
from modules.image_recognition.tasks.celery_tasks import analyze_image_task, batch_analyze_task

# Create FastAPI app
app = FastAPI(
    title="NEXUS Image Recognition API",
    description="Image recognition and analysis API with support for object detection, classification, face detection, and scene recognition",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "service": "NEXUS Image Recognition API",
        "version": "1.0.0",
        "status": "running"
=======
# Upload directory
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/nexus_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "NEXUS Image Recognition API",
        "version": "1.0.0",
        "status": "active"
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
    }


@app.get("/health")
<<<<<<< HEAD
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    analysis_type: str = "object_detection",
    user_id: int = 1,
    provider: str = "aws",
    db: Session = Depends(get_db)
):
    """
    Analyze an uploaded image

    - **file**: Image file to analyze
    - **analysis_type**: Type of analysis (object_detection, image_classification, face_detection, scene_recognition)
    - **user_id**: User ID
    - **provider**: Vision API provider (google or aws)
    """
    try:
        # Read image data
        image_data = await file.read()

        # Get image metadata
        _, metadata = ImageProcessor.load_image(image_data)

        # Create analysis record
        analysis = ImageAnalysis(
            user_id=user_id,
            image_url=f"uploads/{file.filename}",
            image_name=file.filename,
            analysis_type=AnalysisType[analysis_type.upper()],
            status=AnalysisStatus.PENDING,
            image_width=metadata['width'],
            image_height=metadata['height'],
            image_format=metadata['format'],
            file_size_bytes=metadata['size_bytes']
        )

        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        # Queue async task
        task = analyze_image_task.delay(
            analysis_id=analysis.id,
            image_data=image_data,
=======
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Image Analysis Endpoints

@app.post("/analyze", response_model=ImageAnalysisResponse, status_code=201)
async def create_analysis(
    request: ImageAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new image analysis request

    This endpoint creates an analysis record and queues it for processing.
    The actual analysis is performed asynchronously using Celery.
    """
    try:
        service = AnalysisService(db)

        # Create analysis record
        analysis = service.create_analysis(
            image_path=request.image_path,
            image_url=request.image_url,
            analysis_type=request.analysis_type,
            provider=request.provider or "google_vision"
        )

        # Queue for async processing
        task = analyze_image_task.delay(analysis.id)

        # Return immediate response
        return ImageAnalysisResponse(
            id=analysis.id,
            image_path=analysis.image_path,
            image_url=analysis.image_url,
            analysis_type=analysis.analysis_type.value,
            status=analysis.status.value,
            provider=analysis.provider,
            created_at=analysis.created_at,
            objects=[],
            faces=[],
            labels=[],
            scenes=[]
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/analyze/upload", response_model=ImageAnalysisResponse, status_code=201)
async def analyze_uploaded_image(
    file: UploadFile = File(...),
    analysis_type: str = "object_detection",
    provider: str = "google_vision",
    db: Session = Depends(get_db)
):
    """
    Upload and analyze an image file

    Upload an image file and create an analysis request.
    Supported formats: JPG, PNG, GIF, BMP, WEBP
    """
    # Validate file type
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    try:
        # Save uploaded file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create analysis
        service = AnalysisService(db)
        analysis = service.create_analysis(
            image_path=file_path,
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
            analysis_type=analysis_type,
            provider=provider
        )

<<<<<<< HEAD
        # Update with task ID
        analysis.status = AnalysisStatus.PROCESSING
        db.commit()

        return ImageAnalysisResponse.from_orm(analysis)

    except Exception as e:
        logger.error(f"Error in analyze_image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyses", response_model=List[ImageAnalysisResponse])
def get_analyses(
    user_id: Optional[int] = None,
    analysis_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get list of image analyses with filters"""
    try:
        query = db.query(ImageAnalysis)

        if user_id:
            query = query.filter(ImageAnalysis.user_id == user_id)
        if analysis_type:
            query = query.filter(ImageAnalysis.analysis_type == AnalysisType[analysis_type.upper()])
        if status:
            query = query.filter(ImageAnalysis.status == AnalysisStatus[status.upper()])

        analyses = query.order_by(ImageAnalysis.created_at.desc()).offset(offset).limit(limit).all()

        return [ImageAnalysisResponse.from_orm(a) for a in analyses]

    except Exception as e:
        logger.error(f"Error in get_analyses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyses/{analysis_id}", response_model=ImageAnalysisResponse)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Get specific analysis by ID"""
    try:
        analysis = db.query(ImageAnalysis).filter(ImageAnalysis.id == analysis_id).first()

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        return ImageAnalysisResponse.from_orm(analysis)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/analyses/{analysis_id}")
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Delete an analysis"""
    try:
        analysis = db.query(ImageAnalysis).filter(ImageAnalysis.id == analysis_id).first()

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        db.delete(analysis)
        db.commit()

        return {"message": "Analysis deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    user_id: Optional[int] = None,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get analytics for image analyses"""
    try:
        query = db.query(ImageAnalysis)

        if user_id:
            query = query.filter(ImageAnalysis.user_id == user_id)

        # Filter by date range
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ImageAnalysis.created_at >= start_date)

        analyses = query.all()

        # Calculate metrics
        total_analyses = len(analyses)

        analyses_by_type = {}
        for analysis in analyses:
            type_name = analysis.analysis_type.value
            analyses_by_type[type_name] = analyses_by_type.get(type_name, 0) + 1

        analyses_by_status = {}
        for analysis in analyses:
            status_name = analysis.status.value
            analyses_by_status[status_name] = analyses_by_status.get(status_name, 0) + 1

        # Average processing time
        processing_times = [a.processing_time_ms for a in analyses if a.processing_time_ms]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else None

        # Count objects and faces
        total_objects = db.query(func.count(DetectedObject.id)).join(ImageAnalysis).filter(
            ImageAnalysis.created_at >= start_date
        ).scalar()

        total_faces = db.query(func.count(DetectedFace.id)).join(ImageAnalysis).filter(
            ImageAnalysis.created_at >= start_date
        ).scalar()

        # Most detected labels
        most_detected = db.query(
            DetectedObject.label,
            func.count(DetectedObject.id).label('count')
        ).join(ImageAnalysis).filter(
            ImageAnalysis.created_at >= start_date
        ).group_by(DetectedObject.label).order_by(func.count(DetectedObject.id).desc()).limit(10).all()

        most_detected_labels = [{"label": label, "count": count} for label, count in most_detected]

        return AnalyticsResponse(
            total_analyses=total_analyses,
            analyses_by_type=analyses_by_type,
            analyses_by_status=analyses_by_status,
            average_processing_time_ms=avg_processing_time,
            total_objects_detected=total_objects,
            total_faces_detected=total_faces,
            most_detected_labels=most_detected_labels
        )

    except Exception as e:
        logger.error(f"Error in get_analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/models/train", response_model=CustomModelResponse)
def train_model(request: CustomModelTrainingRequest, db: Session = Depends(get_db)):
    """Train a custom model"""
    try:
        # Create model record
        model = CustomModel(
            user_id=request.user_id,
            name=request.name,
            description=request.description,
            model_type=request.model_type,
            training_status="pending",
            config=request.config
        )

        db.add(model)
        db.commit()
        db.refresh(model)

        # Queue training task
        task = train_custom_model_task.delay(
            model_id=model.id,
            dataset_path=f"datasets/{request.dataset_id}",
            config=request.config or {}
        )

        model.training_status = "training"
        db.commit()

        return CustomModelResponse.from_orm(model)

    except Exception as e:
        logger.error(f"Error in train_model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models", response_model=List[CustomModelResponse])
def get_models(
    user_id: Optional[int] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """Get list of custom models"""
    try:
        query = db.query(CustomModel)

        if user_id:
            query = query.filter(CustomModel.user_id == user_id)

        query = query.filter(CustomModel.is_active == is_active)

        models = query.order_by(CustomModel.created_at.desc()).all()

        return [CustomModelResponse.from_orm(m) for m in models]

    except Exception as e:
        logger.error(f"Error in get_models: {e}")
        raise HTTPException(status_code=500, detail=str(e))
=======
        # Queue for processing
        task = analyze_image_task.delay(analysis.id)

        return ImageAnalysisResponse(
            id=analysis.id,
            image_path=analysis.image_path,
            image_url=analysis.image_url,
            analysis_type=analysis.analysis_type.value,
            status=analysis.status.value,
            provider=analysis.provider,
            created_at=analysis.created_at,
            objects=[],
            faces=[],
            labels=[],
            scenes=[]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/batch", status_code=202)
async def batch_analyze(
    request: BatchAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Batch analyze multiple images

    Create analysis requests for multiple images and process them in batch.
    Returns a task ID to track the batch processing status.
    """
    try:
        service = AnalysisService(db)
        analysis_ids = []

        # Create analysis records for all images
        for image in request.images:
            if image.startswith("http"):
                analysis = service.create_analysis(
                    image_url=image,
                    analysis_type=request.analysis_type,
                    provider=request.provider
                )
            else:
                analysis = service.create_analysis(
                    image_path=image,
                    analysis_type=request.analysis_type,
                    provider=request.provider
                )
            analysis_ids.append(analysis.id)

        # Queue batch processing
        task = batch_analyze_task.delay(analysis_ids)

        return {
            "message": "Batch analysis queued",
            "task_id": task.id,
            "total_images": len(analysis_ids),
            "analysis_ids": analysis_ids
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/analyze/{analysis_id}", response_model=ImageAnalysisResponse)
async def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """
    Get analysis results by ID

    Retrieve the complete analysis results including all detected objects,
    faces, labels, and scenes.
    """
    service = AnalysisService(db)
    analysis = service.get_analysis(analysis_id)

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Convert to response model
    from modules.image_recognition.models.schemas import (
        DetectedObjectResponse,
        DetectedFaceResponse,
        ImageLabelResponse,
        DetectedSceneResponse,
        BoundingBox
    )

    return ImageAnalysisResponse(
        id=analysis.id,
        image_path=analysis.image_path,
        image_url=analysis.image_url,
        analysis_type=analysis.analysis_type.value,
        status=analysis.status.value,
        provider=analysis.provider,
        confidence_score=analysis.confidence_score,
        objects=[
            DetectedObjectResponse(
                name=obj.name,
                confidence=obj.confidence,
                bbox=BoundingBox(
                    x=obj.bbox_x,
                    y=obj.bbox_y,
                    width=obj.bbox_width,
                    height=obj.bbox_height
                ) if obj.bbox_x is not None else None,
                attributes=obj.attributes
            )
            for obj in analysis.objects
        ],
        faces=[
            DetectedFaceResponse(
                confidence=face.confidence,
                bbox=BoundingBox(
                    x=face.bbox_x,
                    y=face.bbox_y,
                    width=face.bbox_width,
                    height=face.bbox_height
                ) if face.bbox_x is not None else None,
                age_range={"low": face.age_range_low, "high": face.age_range_high} if face.age_range_low else None,
                gender=face.gender,
                emotions=face.emotions,
                attributes=face.attributes
            )
            for face in analysis.faces
        ],
        labels=[
            ImageLabelResponse(
                name=label.name,
                confidence=label.confidence,
                category=label.category
            )
            for label in analysis.labels
        ],
        scenes=[
            DetectedSceneResponse(
                scene_type=scene.scene_type,
                confidence=scene.confidence,
                attributes=scene.attributes
            )
            for scene in analysis.scenes
        ],
        created_at=analysis.created_at,
        processed_at=analysis.processed_at,
        error_message=analysis.error_message
    )


@app.get("/analyze/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: int, db: Session = Depends(get_db)):
    """Get analysis status"""
    analysis = db.query(ImageAnalysis).filter(ImageAnalysis.id == analysis_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return AnalysisStatusResponse(
        id=analysis.id,
        status=analysis.status.value,
        error_message=analysis.error_message
    )


@app.get("/analyses", response_model=List[ImageAnalysisResponse])
async def list_analyses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all analyses with pagination"""
    service = AnalysisService(db)
    analyses = service.list_analyses(skip=skip, limit=limit)

    return [
        ImageAnalysisResponse(
            id=a.id,
            image_path=a.image_path,
            image_url=a.image_url,
            analysis_type=a.analysis_type.value,
            status=a.status.value,
            provider=a.provider,
            confidence_score=a.confidence_score,
            created_at=a.created_at,
            processed_at=a.processed_at,
            error_message=a.error_message,
            objects=[],
            faces=[],
            labels=[],
            scenes=[]
        )
        for a in analyses
    ]


@app.delete("/analyze/{analysis_id}", status_code=204)
async def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Delete an analysis record"""
    analysis = db.query(ImageAnalysis).filter(ImageAnalysis.id == analysis_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    db.delete(analysis)
    db.commit()

    return None


# Analytics Endpoints

@app.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(db: Session = Depends(get_db)):
    """Get analytics and statistics"""
    service = AnalysisService(db)
    return service.get_analytics()


# Custom Models Endpoints

@app.post("/models", response_model=CustomModelResponse, status_code=201)
async def create_custom_model(
    model_data: CustomModelCreate,
    db: Session = Depends(get_db)
):
    """Create a custom trained model"""
    # Check if model name already exists
    existing = db.query(CustomModel).filter(CustomModel.name == model_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Model name already exists")

    model = CustomModel(
        name=model_data.name,
        description=model_data.description,
        model_type=model_data.model_type,
        model_path=model_data.model_path,
        model_version=model_data.model_version,
        classes=model_data.classes,
        input_shape=model_data.input_shape,
        training_dataset_size=model_data.training_dataset_size,
        training_accuracy=model_data.training_accuracy,
        training_completed_at=datetime.utcnow() if model_data.training_accuracy else None
    )

    db.add(model)
    db.commit()
    db.refresh(model)

    return CustomModelResponse(
        id=model.id,
        name=model.name,
        description=model.description,
        model_type=model.model_type,
        model_version=model.model_version,
        classes=model.classes,
        is_active=bool(model.is_active),
        created_at=model.created_at,
        training_accuracy=model.training_accuracy
    )


@app.get("/models", response_model=List[CustomModelResponse])
async def list_custom_models(db: Session = Depends(get_db)):
    """List all custom models"""
    models = db.query(CustomModel).filter(CustomModel.is_active == 1).all()

    return [
        CustomModelResponse(
            id=m.id,
            name=m.name,
            description=m.description,
            model_type=m.model_type,
            model_version=m.model_version,
            classes=m.classes,
            is_active=bool(m.is_active),
            created_at=m.created_at,
            training_accuracy=m.training_accuracy
        )
        for m in models
    ]
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a


if __name__ == "__main__":
    import uvicorn
<<<<<<< HEAD
    uvicorn.run(app, host="0.0.0.0", port=8001)
=======
    uvicorn.run(app, host="0.0.0.0", port=8000)
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
