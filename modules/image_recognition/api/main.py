"""
FastAPI application for Image Recognition module
"""
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    }


@app.get("/health")
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
            analysis_type=analysis_type,
            provider=provider
        )

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
