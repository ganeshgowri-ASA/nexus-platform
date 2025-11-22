"""
FastAPI REST API for ETL module.

This module provides comprehensive REST API endpoints for managing
ETL jobs, data sources, targets, and monitoring.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
import io
import json
import yaml

from modules.etl import schemas
from modules.etl.models import (
    ETLJob, DataSource, DataTarget, Mapping, JobRun, JobStatus,
    ETLTemplate, DataQualityRule
)
from modules.etl.jobs import JobExecutor, JobScheduler, JobMonitor, JobHistory
from modules.etl.monitoring import ETLMetrics, Alerting
from modules.etl.extractors import ExtractorFactory
from modules.etl.loaders import LoaderFactory

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/etl", tags=["ETL"])


# Dependency to get database session
def get_db() -> Session:
    """Get database session."""
    # TODO: Implement actual database session management
    # This is a placeholder
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///etl.db")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Data Source endpoints
@router.post("/sources", response_model=schemas.DataSourceResponse, status_code=201)
def create_data_source(
    source: schemas.DataSourceCreate,
    db: Session = Depends(get_db)
):
    """Create a new data source."""
    try:
        db_source = DataSource(**source.dict())
        db.add(db_source)
        db.commit()
        db.refresh(db_source)
        return db_source
    except Exception as e:
        logger.error(f"Error creating data source: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sources", response_model=List[schemas.DataSourceResponse])
def list_data_sources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all data sources."""
    query = db.query(DataSource)

    if source_type:
        query = query.filter(DataSource.source_type == source_type)
    if is_active is not None:
        query = query.filter(DataSource.is_active == is_active)

    sources = query.offset(skip).limit(limit).all()
    return sources


@router.get("/sources/{source_id}", response_model=schemas.DataSourceResponse)
def get_data_source(source_id: int, db: Session = Depends(get_db)):
    """Get a specific data source."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return source


@router.put("/sources/{source_id}", response_model=schemas.DataSourceResponse)
def update_data_source(
    source_id: int,
    source_update: schemas.DataSourceUpdate,
    db: Session = Depends(get_db)
):
    """Update a data source."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    for key, value in source_update.dict(exclude_unset=True).items():
        setattr(source, key, value)

    db.commit()
    db.refresh(source)
    return source


@router.delete("/sources/{source_id}", status_code=204)
def delete_data_source(source_id: int, db: Session = Depends(get_db)):
    """Delete a data source."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    db.delete(source)
    db.commit()
    return None


@router.post("/sources/{source_id}/test")
def test_data_source_connection(source_id: int, db: Session = Depends(get_db)):
    """Test connection to a data source."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    try:
        extractor = ExtractorFactory.create_extractor(source)
        success = extractor.test_connection()

        return {
            "success": success,
            "message": "Connection successful" if success else "Connection failed"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}"
        }


@router.post("/sources/{source_id}/preview")
def preview_data_source(
    source_id: int,
    request: schemas.DataPreviewRequest,
    db: Session = Depends(get_db)
):
    """Preview data from a data source."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    try:
        extractor = ExtractorFactory.create_extractor(source)
        with extractor:
            data = extractor.extract(
                query=request.query,
                limit=request.limit
            )

        columns = list(data[0].keys()) if data else []

        return schemas.DataPreviewResponse(
            columns=columns,
            data=data,
            total_count=len(data)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Preview failed: {str(e)}")


# Data Target endpoints
@router.post("/targets", response_model=schemas.DataTargetResponse, status_code=201)
def create_data_target(
    target: schemas.DataTargetCreate,
    db: Session = Depends(get_db)
):
    """Create a new data target."""
    try:
        db_target = DataTarget(**target.dict())
        db.add(db_target)
        db.commit()
        db.refresh(db_target)
        return db_target
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/targets", response_model=List[schemas.DataTargetResponse])
def list_data_targets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all data targets."""
    targets = db.query(DataTarget).offset(skip).limit(limit).all()
    return targets


@router.get("/targets/{target_id}", response_model=schemas.DataTargetResponse)
def get_data_target(target_id: int, db: Session = Depends(get_db)):
    """Get a specific data target."""
    target = db.query(DataTarget).filter(DataTarget.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Data target not found")
    return target


# Mapping endpoints
@router.post("/mappings", response_model=schemas.MappingResponse, status_code=201)
def create_mapping(
    mapping: schemas.MappingCreate,
    db: Session = Depends(get_db)
):
    """Create a new field mapping."""
    try:
        db_mapping = Mapping(**mapping.dict())
        db.add(db_mapping)
        db.commit()
        db.refresh(db_mapping)
        return db_mapping
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/mappings", response_model=List[schemas.MappingResponse])
def list_mappings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all mappings."""
    mappings = db.query(Mapping).offset(skip).limit(limit).all()
    return mappings


# ETL Job endpoints
@router.post("/jobs", response_model=schemas.ETLJobResponse, status_code=201)
def create_etl_job(
    job: schemas.ETLJobCreate,
    db: Session = Depends(get_db)
):
    """Create a new ETL job."""
    try:
        db_job = ETLJob(**job.dict())
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/jobs", response_model=List[schemas.ETLJobResponse])
def list_etl_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    is_scheduled: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all ETL jobs."""
    query = db.query(ETLJob)

    if is_active is not None:
        query = query.filter(ETLJob.is_active == is_active)
    if is_scheduled is not None:
        query = query.filter(ETLJob.is_scheduled == is_scheduled)

    jobs = query.offset(skip).limit(limit).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=schemas.ETLJobResponse)
def get_etl_job(job_id: int, db: Session = Depends(get_db)):
    """Get a specific ETL job."""
    job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="ETL job not found")
    return job


@router.put("/jobs/{job_id}", response_model=schemas.ETLJobResponse)
def update_etl_job(
    job_id: int,
    job_update: schemas.ETLJobUpdate,
    db: Session = Depends(get_db)
):
    """Update an ETL job."""
    job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="ETL job not found")

    for key, value in job_update.dict(exclude_unset=True).items():
        setattr(job, key, value)

    db.commit()
    db.refresh(job)
    return job


@router.delete("/jobs/{job_id}", status_code=204)
def delete_etl_job(job_id: int, db: Session = Depends(get_db)):
    """Delete an ETL job."""
    job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="ETL job not found")

    db.delete(job)
    db.commit()
    return None


@router.post("/jobs/{job_id}/execute")
def execute_etl_job(
    job_id: int,
    request: schemas.JobExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Execute an ETL job."""
    job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="ETL job not found")

    try:
        executor = JobExecutor(db)
        # Execute asynchronously
        job_run_id = executor.execute_job_async(
            job_id=job_id,
            triggered_by="api"
        )

        return schemas.JobExecutionResponse(
            job_run_id=job_run_id,
            status=JobStatus.PENDING,
            message="Job submitted for execution"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Execution failed: {str(e)}")


@router.get("/jobs/{job_id}/status")
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Get current status of a job."""
    monitor = JobMonitor(db)
    try:
        return monitor.get_job_status(job_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/jobs/{job_id}/metrics")
def get_job_metrics(
    job_id: int,
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get metrics for a job."""
    monitor = JobMonitor(db)
    try:
        return monitor.get_job_metrics(job_id, days)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Job Run endpoints
@router.get("/runs", response_model=List[schemas.JobRunResponse])
def list_job_runs(
    job_id: Optional[int] = None,
    status: Optional[JobStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List job runs."""
    history = JobHistory(db)
    runs = history.get_job_runs(
        job_id=job_id,
        status=status,
        limit=limit,
        offset=skip
    )
    return runs


@router.get("/runs/{run_id}", response_model=schemas.JobRunResponse)
def get_job_run(run_id: int, db: Session = Depends(get_db)):
    """Get a specific job run."""
    history = JobHistory(db)
    run = history.get_job_run_details(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Job run not found")
    return run


# Metrics endpoints
@router.get("/metrics/overview")
def get_overview_metrics(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get overall ETL metrics."""
    metrics = ETLMetrics(db)
    return metrics.get_overall_metrics(days)


@router.get("/metrics/health")
def get_system_health(db: Session = Depends(get_db)):
    """Get system health status."""
    metrics = ETLMetrics(db)
    return metrics.get_system_health()


# Template endpoints
@router.get("/templates", response_model=List[schemas.ETLTemplateResponse])
def list_templates(
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List ETL templates."""
    query = db.query(ETLTemplate).filter(ETLTemplate.is_active == True)

    if category:
        query = query.filter(ETLTemplate.category == category)

    templates = query.offset(skip).limit(limit).all()
    return templates


# Export/Import endpoints
@router.post("/export")
def export_configuration(
    request: schemas.ExportRequest,
    db: Session = Depends(get_db)
):
    """Export ETL configuration."""
    try:
        # Gather all configuration
        jobs = db.query(ETLJob).all()
        sources = db.query(DataSource).all()
        targets = db.query(DataTarget).all()
        mappings = db.query(Mapping).all()

        config = {
            "version": "1.0",
            "jobs": [
                {
                    "name": job.name,
                    "source_id": job.source_id,
                    "target_id": job.target_id,
                    # Add other fields
                }
                for job in jobs
            ],
            "sources": [{"name": s.name, "type": s.source_type.value} for s in sources],
            "targets": [{"name": t.name, "type": t.target_type.value} for t in targets],
            "mappings": [{"name": m.name} for m in mappings]
        }

        if request.format == "json":
            content = json.dumps(config, indent=2)
            media_type = "application/json"
            filename = "etl_config.json"
        elif request.format == "yaml":
            content = yaml.dump(config)
            media_type = "application/yaml"
            filename = "etl_config.yaml"
        else:
            raise HTTPException(status_code=400, detail="Invalid format")

        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Export failed: {str(e)}")


# Running jobs endpoint
@router.get("/jobs/running/list")
def list_running_jobs(db: Session = Depends(get_db)):
    """List currently running jobs."""
    monitor = JobMonitor(db)
    return monitor.get_running_jobs()


# Bulk operations
@router.post("/jobs/bulk")
def bulk_job_operations(
    request: schemas.BulkOperationRequest,
    db: Session = Depends(get_db)
):
    """Perform bulk operations on jobs."""
    success_count = 0
    failed_count = 0
    failed_ids = []
    errors = []

    for job_id in request.ids:
        try:
            job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
            if not job:
                failed_count += 1
                failed_ids.append(job_id)
                errors.append(f"Job {job_id} not found")
                continue

            if request.action == "activate":
                job.is_active = True
            elif request.action == "deactivate":
                job.is_active = False
            elif request.action == "delete":
                db.delete(job)

            success_count += 1

        except Exception as e:
            failed_count += 1
            failed_ids.append(job_id)
            errors.append(str(e))

    db.commit()

    return schemas.BulkOperationResponse(
        success_count=success_count,
        failed_count=failed_count,
        failed_ids=failed_ids,
        errors=errors
    )
