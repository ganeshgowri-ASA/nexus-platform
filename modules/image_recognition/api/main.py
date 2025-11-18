"""
FastAPI application for Image Recognition module
"""
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    }


@app.get("/health")
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
            analysis_type=analysis_type,
            provider=provider
        )

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
