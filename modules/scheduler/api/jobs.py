"""Job management API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import List, Optional
from datetime import datetime, timedelta
from modules.scheduler.models import get_db, ScheduledJob, JobExecution
from modules.scheduler.models.pydantic_models import (
    JobCreate, JobUpdate, JobResponse, ExecutionResponse,
    JobExecuteRequest, JobStatsResponse
)
from modules.scheduler.services.scheduler_engine import SchedulerEngine
from modules.scheduler.utils.cron_utils import calculate_next_run

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", response_model=JobResponse, status_code=201)
async def create_job(
    job: JobCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new scheduled job"""
    # Calculate next run time
    next_run = calculate_next_run(
        job_type=job.job_type,
        cron_expression=job.cron_expression,
        interval_seconds=job.interval_seconds,
        scheduled_time=job.scheduled_time,
        timezone=job.timezone
    )

    # Create job instance
    db_job = ScheduledJob(
        **job.model_dump(),
        next_run_at=next_run
    )

    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)

    # Register with scheduler
    scheduler_engine = SchedulerEngine()
    await scheduler_engine.register_job(db_job)

    return db_job


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    job_type: Optional[str] = None,
    tags: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all scheduled jobs with filtering"""
    query = select(ScheduledJob)

    # Apply filters
    filters = []
    if is_active is not None:
        filters.append(ScheduledJob.is_active == is_active)
    if job_type:
        filters.append(ScheduledJob.job_type == job_type)
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        filters.append(ScheduledJob.tags.contains(tag_list))

    if filters:
        query = query.where(and_(*filters))

    query = query.offset(skip).limit(limit).order_by(desc(ScheduledJob.created_at))

    result = await db.execute(query)
    jobs = result.scalars().all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific job by ID"""
    result = await db.execute(
        select(ScheduledJob).where(ScheduledJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_update: JobUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a job"""
    result = await db.execute(
        select(ScheduledJob).where(ScheduledJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Update fields
    update_data = job_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    # Recalculate next run if scheduling changed
    if any(k in update_data for k in ['cron_expression', 'interval_seconds', 'scheduled_time', 'timezone']):
        next_run = calculate_next_run(
            job_type=job.job_type,
            cron_expression=job.cron_expression,
            interval_seconds=job.interval_seconds,
            scheduled_time=job.scheduled_time,
            timezone=job.timezone
        )
        job.next_run_at = next_run

    job.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(job)

    # Update scheduler
    scheduler_engine = SchedulerEngine()
    await scheduler_engine.update_job(job)

    return job


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a job"""
    result = await db.execute(
        select(ScheduledJob).where(ScheduledJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Remove from scheduler
    scheduler_engine = SchedulerEngine()
    await scheduler_engine.remove_job(job.id)

    await db.delete(job)
    await db.commit()


@router.post("/{job_id}/execute")
async def execute_job(
    job_id: int,
    execute_request: Optional[JobExecuteRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """Manually execute a job"""
    result = await db.execute(
        select(ScheduledJob).where(ScheduledJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    scheduler_engine = SchedulerEngine()
    task_id = await scheduler_engine.execute_job_now(
        job,
        task_args=execute_request.task_args if execute_request else None,
        task_kwargs=execute_request.task_kwargs if execute_request else None
    )

    return {"message": "Job execution started", "task_id": task_id}


@router.post("/{job_id}/pause")
async def pause_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Pause a job"""
    result = await db.execute(
        select(ScheduledJob).where(ScheduledJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.is_active = False
    job.status = "paused"
    await db.commit()

    scheduler_engine = SchedulerEngine()
    await scheduler_engine.pause_job(job.id)

    return {"message": "Job paused"}


@router.post("/{job_id}/resume")
async def resume_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Resume a paused job"""
    result = await db.execute(
        select(ScheduledJob).where(ScheduledJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.is_active = True
    job.status = "pending"
    await db.commit()

    scheduler_engine = SchedulerEngine()
    await scheduler_engine.resume_job(job)

    return {"message": "Job resumed"}


@router.get("/{job_id}/executions", response_model=List[ExecutionResponse])
async def get_job_executions(
    job_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Get execution history for a job"""
    result = await db.execute(
        select(JobExecution)
        .where(JobExecution.job_id == job_id)
        .order_by(desc(JobExecution.scheduled_at))
        .offset(skip)
        .limit(limit)
    )
    executions = result.scalars().all()
    return executions


@router.get("/stats/overview", response_model=JobStatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get overall scheduler statistics"""
    # Total and active jobs
    total_jobs_result = await db.execute(select(func.count(ScheduledJob.id)))
    total_jobs = total_jobs_result.scalar()

    active_jobs_result = await db.execute(
        select(func.count(ScheduledJob.id)).where(ScheduledJob.is_active == True)
    )
    active_jobs = active_jobs_result.scalar()

    paused_jobs_result = await db.execute(
        select(func.count(ScheduledJob.id)).where(ScheduledJob.status == "paused")
    )
    paused_jobs = paused_jobs_result.scalar()

    # Execution stats
    total_executions_result = await db.execute(select(func.count(JobExecution.id)))
    total_executions = total_executions_result.scalar()

    successful_result = await db.execute(
        select(func.count(JobExecution.id)).where(JobExecution.status == "completed")
    )
    successful_executions = successful_result.scalar()

    failed_result = await db.execute(
        select(func.count(JobExecution.id)).where(JobExecution.status == "failed")
    )
    failed_executions = failed_result.scalar()

    running_result = await db.execute(
        select(func.count(JobExecution.id)).where(JobExecution.status == "running")
    )
    running_executions = running_result.scalar()

    # Average duration
    avg_duration_result = await db.execute(
        select(func.avg(JobExecution.duration_seconds))
        .where(JobExecution.status == "completed")
    )
    average_duration = avg_duration_result.scalar()

    # Last 24h executions
    yesterday = datetime.utcnow() - timedelta(days=1)
    last_24h_result = await db.execute(
        select(func.count(JobExecution.id))
        .where(JobExecution.created_at >= yesterday)
    )
    last_24h_executions = last_24h_result.scalar()

    return JobStatsResponse(
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        paused_jobs=paused_jobs,
        total_executions=total_executions,
        successful_executions=successful_executions,
        failed_executions=failed_executions,
        running_executions=running_executions,
        average_duration=average_duration,
        last_24h_executions=last_24h_executions
    )
