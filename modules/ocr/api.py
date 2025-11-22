"""
FastAPI Endpoints

RESTful API with WebSocket support for OCR operations.
"""

import logging
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import shutil

from .schemas import (
    OCRRequest, OCRResponse, OCRJobResponse, BatchOCRRequest, BatchOCRResponse,
    ExportRequest, ExportResponse, QualityMetricsSchema, HealthCheck,
    WSMessage, WSProgressUpdate, OCRStatistics
)
from .processor import OCRPipeline
from .config import config
from . import models

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NEXUS OCR API",
    description="Production-ready OCR API for the NEXUS platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        """Connect websocket for job"""
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)
        logger.info(f"WebSocket connected for job {job_id}")

    def disconnect(self, websocket: WebSocket, job_id: str):
        """Disconnect websocket"""
        if job_id in self.active_connections:
            self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
        logger.info(f"WebSocket disconnected for job {job_id}")

    async def send_message(self, message: dict, job_id: str):
        """Send message to all connections for job"""
        if job_id in self.active_connections:
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

    async def broadcast(self, message: dict):
        """Broadcast message to all connections"""
        for connections in self.active_connections.values():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except:
                    pass


manager = ConnectionManager()


# Dependency for database session
def get_db():
    """Get database session"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(config.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Health check
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        db_connected = True
        try:
            from sqlalchemy import create_engine
            engine = create_engine(config.database_url)
            connection = engine.connect()
            connection.close()
        except:
            db_connected = False

        # Check Redis
        redis_connected = True
        try:
            import redis
            r = redis.from_url(config.redis_url)
            r.ping()
        except:
            redis_connected = False

        # Get available engines
        from .engines import OCREngineFactory
        available_engines = OCREngineFactory.get_available_engines({
            'tesseract': config.get_engine_config('tesseract'),
            'google_vision': config.get_engine_config('google_vision'),
            'azure': config.get_engine_config('azure'),
            'aws': config.get_engine_config('aws'),
            'openai': config.get_engine_config('openai'),
        })

        return HealthCheck(
            status="healthy",
            version="1.0.0",
            available_engines=available_engines,
            database_connected=db_connected,
            redis_connected=redis_connected,
            celery_workers=0
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# OCR endpoints
@app.post("/ocr/process", response_model=OCRResponse)
async def process_ocr(
    file: UploadFile = File(...),
    request: OCRRequest = Depends(),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Process single file with OCR

    Upload a file and get OCR results.
    """
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())

        # Save uploaded file
        file_path = config.upload_path / f"{job_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create job record
        job = models.OCRJob(
            job_id=job_id,
            file_name=file.filename,
            file_path=str(file_path),
            engine_type=request.engine.value,
            language=request.language,
            status=models.JobStatus.PROCESSING,
            started_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()

        # Process with OCR
        start_time = datetime.utcnow()

        pipeline = OCRPipeline(engine_type=request.engine.value)
        result = pipeline.process_file(
            file_path,
            language=request.language,
            preprocess=request.preprocess,
            detect_layout=request.detect_layout,
            post_process=request.post_process
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        # Update job
        job.status = models.JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.processing_time = processing_time
        job.total_confidence = result.get('confidence', 0.0)
        job.page_count = result.get('page_count', 1)
        db.commit()

        # Build response
        from .schemas import Word, Line, TextBlockSchema, BoundingBox

        words = [
            Word(
                text=w.get('text', ''),
                confidence=w.get('confidence', 0.0),
                bbox=BoundingBox(**w['bbox']) if 'bbox' in w else None
            )
            for w in result.get('words', [])
        ]

        lines = [
            Line(
                text=l.get('text', ''),
                confidence=l.get('confidence', 0.0),
                words=[]
            )
            for l in result.get('lines', [])
        ]

        blocks = [
            TextBlockSchema(
                text=b.get('text', ''),
                confidence=b.get('confidence', 0.0),
                bbox=BoundingBox(**b['bbox']) if 'bbox' in b else None
            )
            for b in result.get('text_blocks', [])
        ]

        response = OCRResponse(
            job_id=job_id,
            status="completed",
            text=result.get('text', ''),
            confidence=result.get('confidence', 0.0),
            language=request.language,
            page_count=result.get('page_count', 1),
            processing_time=processing_time,
            words=words,
            lines=lines,
            blocks=blocks,
            metadata=result.get('metadata', {}),
            quality_metrics=result.get('result_quality', {})
        )

        # Send WebSocket update
        await manager.send_message({
            'type': 'job_completed',
            'job_id': job_id,
            'confidence': result.get('confidence', 0.0)
        }, job_id)

        return response

    except Exception as e:
        logger.error(f"Error processing OCR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr/batch", response_model=BatchOCRResponse)
async def batch_process(
    files: List[UploadFile] = File(...),
    request: BatchOCRRequest = Depends(),
    db: Session = Depends(get_db)
):
    """
    Batch process multiple files

    Upload multiple files and process them in batch.
    """
    try:
        batch_id = str(uuid.uuid4())
        job_ids = []

        # Save files and create jobs
        for file in files:
            job_id = str(uuid.uuid4())
            file_path = config.upload_path / f"{job_id}_{file.filename}"

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Create job
            job = models.OCRJob(
                job_id=job_id,
                file_name=file.filename,
                file_path=str(file_path),
                engine_type=request.engine.value,
                language=request.language,
                status=models.JobStatus.PENDING
            )
            db.add(job)
            job_ids.append(job_id)

        db.commit()

        # Trigger batch processing (would use Celery in production)
        # For now, return pending status

        return BatchOCRResponse(
            batch_id=batch_id,
            job_ids=job_ids,
            total_files=len(files),
            status="pending"
        )

    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ocr/job/{job_id}", response_model=OCRJobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get OCR job status and results"""
    try:
        job = db.query(models.OCRJob).filter(models.OCRJob.job_id == job_id).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return job

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ocr/jobs", response_model=List[OCRJobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List OCR jobs with optional filtering"""
    try:
        query = db.query(models.OCRJob)

        if status:
            query = query.filter(models.OCRJob.status == status)

        jobs = query.offset(skip).limit(limit).all()
        return jobs

    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr/export", response_model=ExportResponse)
async def export_result(request: ExportRequest, db: Session = Depends(get_db)):
    """Export OCR result to specified format"""
    try:
        # Get job
        job = db.query(models.OCRJob).filter(models.OCRJob.job_id == request.job_id).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get document
        document = db.query(models.Document).filter(models.Document.job_id == job.id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Prepare data for export
        export_data = {
            'text': document.text_content,
            'confidence': document.confidence,
            'metadata': document.metadata or {}
        }

        # Export
        from .export import ExportManager
        export_manager = ExportManager()

        output_path = config.storage_path / f"{request.job_id}.{request.format}"
        success = export_manager.export(export_data, output_path, request.format)

        if not success:
            raise HTTPException(status_code=500, detail="Export failed")

        # Get file size
        file_size = output_path.stat().st_size

        return ExportResponse(
            job_id=request.job_id,
            format=request.format,
            file_path=str(output_path),
            file_size=file_size,
            created_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ocr/download/{job_id}")
async def download_result(job_id: str, format: str = "txt"):
    """Download OCR result"""
    try:
        file_path = config.storage_path / f"{job_id}.{format}"

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            path=str(file_path),
            filename=f"ocr_result_{job_id}.{format}",
            media_type="application/octet-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ocr/statistics", response_model=OCRStatistics)
async def get_statistics(db: Session = Depends(get_db)):
    """Get OCR processing statistics"""
    try:
        total_jobs = db.query(models.OCRJob).count()
        completed_jobs = db.query(models.OCRJob).filter(
            models.OCRJob.status == models.JobStatus.COMPLETED
        ).count()
        failed_jobs = db.query(models.OCRJob).filter(
            models.OCRJob.status == models.JobStatus.FAILED
        ).count()

        # Average confidence
        from sqlalchemy import func
        avg_confidence = db.query(func.avg(models.OCRJob.total_confidence)).scalar() or 0.0

        # Average processing time
        avg_time = db.query(func.avg(models.OCRJob.processing_time)).scalar() or 0.0

        # Total pages
        total_pages = db.query(func.sum(models.OCRJob.page_count)).scalar() or 0

        return OCRStatistics(
            total_jobs=total_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs,
            average_confidence=float(avg_confidence),
            average_processing_time=float(avg_time),
            total_pages_processed=int(total_pages),
            languages_processed={},
            engines_used={}
        )

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint
@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time job updates

    Connect to receive real-time updates for OCR jobs.
    """
    await manager.connect(websocket, job_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()

            # Echo back
            await websocket.send_json({
                'type': 'pong',
                'job_id': job_id,
                'timestamp': datetime.utcnow().isoformat()
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, job_id)


# Utility endpoints
@app.get("/engines")
async def list_engines():
    """List available OCR engines"""
    from .engines import OCREngineFactory

    available = OCREngineFactory.get_available_engines({
        'tesseract': config.get_engine_config('tesseract'),
        'google_vision': config.get_engine_config('google_vision'),
        'azure': config.get_engine_config('azure'),
        'aws': config.get_engine_config('aws'),
        'openai': config.get_engine_config('openai'),
    })

    return {"available_engines": available}


@app.get("/languages")
async def list_languages():
    """List supported languages"""
    from .language import MultilingualOCR

    multilingual = MultilingualOCR()
    languages = multilingual.get_supported_languages()

    return {"supported_languages": languages}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.api_host,
        port=config.api_port,
        workers=config.api_workers
    )
