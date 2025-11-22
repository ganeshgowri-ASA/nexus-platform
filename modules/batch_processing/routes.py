"""FastAPI routes for batch processing module."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models.batch_job import JobStatus, TaskStatus
from .schemas import (
    BatchJobCreate, BatchJobUpdate, BatchJobResponse,
    BatchJobListResponse, BatchJobStats, BatchJobProgress,
    BatchTaskResponse, BatchTaskListResponse,
    ErrorLogResponse, ErrorLogEntry
)
from .service import BatchJobService, BatchTaskService
from .tasks import (
    process_batch_job, update_job_progress,
    retry_failed_tasks, cancel_job
)
from loguru import logger
import math

router = APIRouter(prefix="/api/v1/batch", tags=["Batch Processing"])


@router.post("/jobs", response_model=BatchJobResponse, status_code=status.HTTP_201_CREATED)
def create_batch_job(
    job_data: BatchJobCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new batch job.

    Args:
        job_data: Batch job creation data
        db: Database session

    Returns:
        Created batch job
    """
    try:
        job = BatchJobService.create_job(db, job_data)
        logger.info(f"Created batch job: {job.id} - {job.name}")
        return job
    except Exception as e:
        logger.error(f"Error creating batch job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch job: {str(e)}"
        )


@router.get("/jobs", response_model=BatchJobListResponse)
def list_batch_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[JobStatus] = Query(None, alias="status"),
    job_type: Optional[str] = Query(None),
    created_by: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List batch jobs with pagination and filters.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status_filter: Filter by job status
        job_type: Filter by job type
        created_by: Filter by creator
        db: Database session

    Returns:
        Paginated list of batch jobs
    """
    try:
        jobs, total = BatchJobService.get_jobs(
            db, skip, limit, status_filter, job_type, created_by
        )

        total_pages = math.ceil(total / limit) if limit > 0 else 0
        page = (skip // limit) + 1 if limit > 0 else 1

        return BatchJobListResponse(
            jobs=jobs,
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error(f"Error listing batch jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list batch jobs: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=BatchJobResponse)
def get_batch_job(job_id: int, db: Session = Depends(get_db)):
    """
    Get a specific batch job by ID.

    Args:
        job_id: Batch job ID
        db: Database session

    Returns:
        Batch job details
    """
    job = BatchJobService.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job {job_id} not found"
        )
    return job


@router.patch("/jobs/{job_id}", response_model=BatchJobResponse)
def update_batch_job(
    job_id: int,
    job_data: BatchJobUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a batch job.

    Args:
        job_id: Batch job ID
        job_data: Update data
        db: Database session

    Returns:
        Updated batch job
    """
    job = BatchJobService.update_job(db, job_id, job_data)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job {job_id} not found"
        )

    logger.info(f"Updated batch job: {job_id}")
    return job


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_batch_job(job_id: int, db: Session = Depends(get_db)):
    """
    Delete a batch job.

    Args:
        job_id: Batch job ID
        db: Database session
    """
    success = BatchJobService.delete_job(db, job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job {job_id} not found"
        )

    logger.info(f"Deleted batch job: {job_id}")


@router.post("/jobs/{job_id}/start", response_model=BatchJobResponse)
def start_batch_job(job_id: int, db: Session = Depends(get_db)):
    """
    Start processing a batch job.

    Args:
        job_id: Batch job ID
        db: Database session

    Returns:
        Started batch job
    """
    job = BatchJobService.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job {job_id} not found"
        )

    if job.status != JobStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is in {job.status} state, cannot start"
        )

    # Queue the job for processing
    task = process_batch_job.apply_async(args=[job_id])

    # Update job status
    job = BatchJobService.start_job(db, job_id, celery_task_id=task.id)

    logger.info(f"Started batch job: {job_id} (task: {task.id})")
    return job


@router.post("/jobs/{job_id}/cancel", response_model=BatchJobResponse)
def cancel_batch_job(job_id: int, db: Session = Depends(get_db)):
    """
    Cancel a running batch job.

    Args:
        job_id: Batch job ID
        db: Database session

    Returns:
        Cancelled batch job
    """
    job = BatchJobService.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job {job_id} not found"
        )

    if job.is_terminal_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is in terminal state {job.status}, cannot cancel"
        )

    # Cancel the job
    cancel_job.apply_async(args=[job_id])

    logger.info(f"Cancelling batch job: {job_id}")
    return job


@router.post("/jobs/{job_id}/retry", response_model=dict)
def retry_batch_job(job_id: int, db: Session = Depends(get_db)):
    """
    Retry failed tasks in a batch job.

    Args:
        job_id: Batch job ID
        db: Database session

    Returns:
        Retry result
    """
    job = BatchJobService.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job {job_id} not found"
        )

    # Queue retry task
    task = retry_failed_tasks.apply_async(args=[job_id])

    logger.info(f"Retrying failed tasks for job: {job_id}")
    return {
        "job_id": job_id,
        "message": "Retry task queued",
        "task_id": task.id
    }


@router.get("/jobs/{job_id}/progress", response_model=BatchJobProgress)
def get_batch_job_progress(job_id: int, db: Session = Depends(get_db)):
    """
    Get real-time progress for a batch job.

    Args:
        job_id: Batch job ID
        db: Database session

    Returns:
        Job progress information
    """
    job = BatchJobService.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job {job_id} not found"
        )

    return BatchJobProgress(
        job_id=job.id,
        status=job.status,
        progress_percentage=job.progress_percentage,
        processed_items=job.processed_items,
        total_items=job.total_items,
        successful_items=job.successful_items,
        failed_items=job.failed_items,
        estimated_completion=job.estimated_completion,
        current_message=f"Processing {job.processed_items}/{job.total_items} items"
    )


@router.get("/jobs/{job_id}/tasks", response_model=BatchTaskListResponse)
def list_batch_tasks(
    job_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """
    List tasks for a specific batch job.

    Args:
        job_id: Batch job ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        status_filter: Filter by task status
        db: Database session

    Returns:
        Paginated list of batch tasks
    """
    # Verify job exists
    job = BatchJobService.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job {job_id} not found"
        )

    tasks, total = BatchTaskService.get_tasks_by_job(
        db, job_id, skip, limit, status_filter
    )

    total_pages = math.ceil(total / limit) if limit > 0 else 0
    page = (skip // limit) + 1 if limit > 0 else 1

    return BatchTaskListResponse(
        tasks=tasks,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages
    )


@router.get("/jobs/{job_id}/errors", response_model=ErrorLogResponse)
def get_batch_job_errors(job_id: int, db: Session = Depends(get_db)):
    """
    Get error logs for a batch job.

    Args:
        job_id: Batch job ID
        db: Database session

    Returns:
        Error log entries
    """
    job = BatchJobService.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job {job_id} not found"
        )

    # Get failed tasks
    failed_tasks = BatchTaskService.get_failed_tasks(db, job_id)

    errors = [
        ErrorLogEntry(
            task_id=task.id,
            task_number=task.task_number,
            timestamp=task.updated_at,
            error_message=task.error_message or "Unknown error",
            error_traceback=task.error_traceback,
            input_data=task.input_data
        )
        for task in failed_tasks
    ]

    return ErrorLogResponse(
        job_id=job_id,
        total_errors=len(errors),
        errors=errors
    )


@router.get("/stats", response_model=BatchJobStats)
def get_batch_stats(db: Session = Depends(get_db)):
    """
    Get overall batch processing statistics.

    Args:
        db: Database session

    Returns:
        Batch processing statistics
    """
    try:
        stats = BatchJobService.get_stats(db)
        return stats
    except Exception as e:
        logger.error(f"Error getting batch stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/health")
def health_check():
    """
    Health check endpoint for batch processing service.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "batch_processing",
        "version": "1.0.0"
    }
