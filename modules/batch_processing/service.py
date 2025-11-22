"""Service layer for batch processing operations."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from database.models.batch_job import BatchJob, BatchTask, JobStatus, TaskStatus
from .schemas import (
    BatchJobCreate, BatchJobUpdate, BatchJobStats,
    BatchTaskCreate, BatchTaskUpdate
)


class BatchJobService:
    """Service for managing batch jobs."""

    @staticmethod
    def create_job(db: Session, job_data: BatchJobCreate) -> BatchJob:
        """Create a new batch job."""
        job = BatchJob(
            name=job_data.name,
            description=job_data.description,
            job_type=job_data.job_type,
            config=job_data.config,
            created_by=job_data.created_by,
            metadata=job_data.metadata,
            status=JobStatus.PENDING
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_job(db: Session, job_id: int) -> Optional[BatchJob]:
        """Get a batch job by ID."""
        return db.query(BatchJob).filter(BatchJob.id == job_id).first()

    @staticmethod
    def get_jobs(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[JobStatus] = None,
        job_type: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> tuple[List[BatchJob], int]:
        """Get list of batch jobs with filters."""
        query = db.query(BatchJob)

        # Apply filters
        if status:
            query = query.filter(BatchJob.status == status)
        if job_type:
            query = query.filter(BatchJob.job_type == job_type)
        if created_by:
            query = query.filter(BatchJob.created_by == created_by)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        jobs = query.order_by(BatchJob.created_at.desc()).offset(skip).limit(limit).all()

        return jobs, total

    @staticmethod
    def update_job(db: Session, job_id: int, job_data: BatchJobUpdate) -> Optional[BatchJob]:
        """Update a batch job."""
        job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
        if not job:
            return None

        update_data = job_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)

        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def delete_job(db: Session, job_id: int) -> bool:
        """Delete a batch job."""
        job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
        if not job:
            return False

        db.delete(job)
        db.commit()
        return True

    @staticmethod
    def start_job(db: Session, job_id: int, celery_task_id: Optional[str] = None) -> Optional[BatchJob]:
        """Mark a batch job as started."""
        job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
        if not job:
            return None

        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        if celery_task_id:
            job.celery_task_id = celery_task_id

        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def complete_job(
        db: Session,
        job_id: int,
        result_summary: Optional[Dict[str, Any]] = None
    ) -> Optional[BatchJob]:
        """Mark a batch job as completed."""
        job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
        if not job:
            return None

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.progress_percentage = 100.0
        if result_summary:
            job.result_summary = result_summary

        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def fail_job(db: Session, job_id: int, error_message: str) -> Optional[BatchJob]:
        """Mark a batch job as failed."""
        job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
        if not job:
            return None

        job.status = JobStatus.FAILED
        job.completed_at = datetime.utcnow()
        job.error_message = error_message

        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def cancel_job(db: Session, job_id: int) -> Optional[BatchJob]:
        """Cancel a batch job."""
        job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
        if not job or job.is_terminal_state:
            return None

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.utcnow()

        # Cancel all pending/running tasks
        db.query(BatchTask).filter(
            and_(
                BatchTask.batch_job_id == job_id,
                BatchTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING])
            )
        ).update({BatchTask.status: TaskStatus.SKIPPED})

        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def update_progress(
        db: Session,
        job_id: int,
        processed_items: int,
        successful_items: int,
        failed_items: int
    ) -> Optional[BatchJob]:
        """Update job progress."""
        job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
        if not job:
            return None

        job.processed_items = processed_items
        job.successful_items = successful_items
        job.failed_items = failed_items

        if job.total_items > 0:
            job.progress_percentage = (processed_items / job.total_items) * 100

        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_stats(db: Session) -> BatchJobStats:
        """Get batch job statistics."""
        total_jobs = db.query(func.count(BatchJob.id)).scalar()

        status_counts = {}
        for status in JobStatus:
            count = db.query(func.count(BatchJob.id)).filter(
                BatchJob.status == status
            ).scalar()
            status_counts[status.value] = count

        total_items_processed = db.query(
            func.sum(BatchJob.processed_items)
        ).scalar() or 0

        # Calculate average success rate
        completed_jobs = db.query(BatchJob).filter(
            BatchJob.status == JobStatus.COMPLETED
        ).all()

        if completed_jobs:
            success_rates = [
                (job.successful_items / job.total_items * 100)
                if job.total_items > 0 else 0
                for job in completed_jobs
            ]
            average_success_rate = sum(success_rates) / len(success_rates)
        else:
            average_success_rate = 0.0

        return BatchJobStats(
            total_jobs=total_jobs,
            pending_jobs=status_counts.get("pending", 0),
            running_jobs=status_counts.get("running", 0),
            completed_jobs=status_counts.get("completed", 0),
            failed_jobs=status_counts.get("failed", 0),
            cancelled_jobs=status_counts.get("cancelled", 0),
            total_items_processed=total_items_processed,
            average_success_rate=average_success_rate
        )


class BatchTaskService:
    """Service for managing batch tasks."""

    @staticmethod
    def create_task(db: Session, task_data: BatchTaskCreate) -> BatchTask:
        """Create a new batch task."""
        task = BatchTask(
            batch_job_id=task_data.batch_job_id,
            task_number=task_data.task_number,
            task_name=task_data.task_name,
            input_data=task_data.input_data,
            max_retries=task_data.max_retries,
            status=TaskStatus.PENDING
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def create_tasks_bulk(db: Session, tasks_data: List[BatchTaskCreate]) -> List[BatchTask]:
        """Create multiple batch tasks at once."""
        tasks = [
            BatchTask(
                batch_job_id=task_data.batch_job_id,
                task_number=task_data.task_number,
                task_name=task_data.task_name,
                input_data=task_data.input_data,
                max_retries=task_data.max_retries,
                status=TaskStatus.PENDING
            )
            for task_data in tasks_data
        ]
        db.bulk_save_objects(tasks)
        db.commit()
        return tasks

    @staticmethod
    def get_task(db: Session, task_id: int) -> Optional[BatchTask]:
        """Get a batch task by ID."""
        return db.query(BatchTask).filter(BatchTask.id == task_id).first()

    @staticmethod
    def get_tasks_by_job(
        db: Session,
        job_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None
    ) -> tuple[List[BatchTask], int]:
        """Get tasks for a specific job."""
        query = db.query(BatchTask).filter(BatchTask.batch_job_id == job_id)

        if status:
            query = query.filter(BatchTask.status == status)

        total = query.count()
        tasks = query.order_by(BatchTask.task_number).offset(skip).limit(limit).all()

        return tasks, total

    @staticmethod
    def update_task(db: Session, task_id: int, task_data: BatchTaskUpdate) -> Optional[BatchTask]:
        """Update a batch task."""
        task = db.query(BatchTask).filter(BatchTask.id == task_id).first()
        if not task:
            return None

        update_data = task_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def start_task(db: Session, task_id: int, celery_task_id: Optional[str] = None) -> Optional[BatchTask]:
        """Mark a task as started."""
        task = db.query(BatchTask).filter(BatchTask.id == task_id).first()
        if not task:
            return None

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        if celery_task_id:
            task.celery_task_id = celery_task_id

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def complete_task(
        db: Session,
        task_id: int,
        output_data: Optional[Dict[str, Any]] = None
    ) -> Optional[BatchTask]:
        """Mark a task as completed."""
        task = db.query(BatchTask).filter(BatchTask.id == task_id).first()
        if not task:
            return None

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        if task.started_at:
            task.duration_seconds = (task.completed_at - task.started_at).total_seconds()
        if output_data:
            task.output_data = output_data

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def fail_task(
        db: Session,
        task_id: int,
        error_message: str,
        error_traceback: Optional[str] = None
    ) -> Optional[BatchTask]:
        """Mark a task as failed."""
        task = db.query(BatchTask).filter(BatchTask.id == task_id).first()
        if not task:
            return None

        task.status = TaskStatus.FAILED
        task.completed_at = datetime.utcnow()
        if task.started_at:
            task.duration_seconds = (task.completed_at - task.started_at).total_seconds()
        task.error_message = error_message
        task.error_traceback = error_traceback

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def retry_task(db: Session, task_id: int) -> Optional[BatchTask]:
        """Retry a failed task."""
        task = db.query(BatchTask).filter(BatchTask.id == task_id).first()
        if not task or not task.can_retry:
            return None

        task.status = TaskStatus.RETRYING
        task.retry_count += 1
        task.error_message = None
        task.error_traceback = None

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_failed_tasks(db: Session, job_id: int) -> List[BatchTask]:
        """Get all failed tasks for a job."""
        return db.query(BatchTask).filter(
            and_(
                BatchTask.batch_job_id == job_id,
                BatchTask.status == TaskStatus.FAILED
            )
        ).all()
