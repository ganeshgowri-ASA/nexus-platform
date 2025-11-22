"""Celery tasks for ETL module."""
from celery import Task
from .celery_app import celery_app
from modules.etl.services.pipeline_service import PipelineService
from modules.etl.models import ETLExecution, Pipeline, ETLJob, DataSource
from shared.database.session import SessionLocal
from shared.utils.logger import get_logger
from datetime import datetime, timedelta
from sqlalchemy import and_
import traceback

logger = get_logger(__name__)


class DatabaseTask(Task):
    """Base task with database session management."""

    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True, max_retries=3)
def execute_pipeline_task(self, pipeline_id: str, job_id: str = None) -> dict:
    """
    Execute an ETL pipeline asynchronously.

    Args:
        pipeline_id: ID of the pipeline to execute
        job_id: Optional job ID for scheduled executions

    Returns:
        Execution report
    """
    execution_id = None

    try:
        logger.info(f"Starting pipeline execution: {pipeline_id}")

        # Get pipeline configuration
        pipeline = self.db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
        if not pipeline:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        if not pipeline.is_active:
            raise ValueError(f"Pipeline is not active: {pipeline_id}")

        # Get data source configuration
        source = self.db.query(DataSource).filter(DataSource.id == pipeline.source_id).first()
        if not source:
            raise ValueError(f"Data source not found: {pipeline.source_id}")

        # Create execution record
        execution = ETLExecution(
            pipeline_id=pipeline_id,
            job_id=job_id,
            status="running",
            started_at=datetime.utcnow(),
            celery_task_id=self.request.id,
        )
        self.db.add(execution)
        self.db.commit()
        execution_id = execution.id

        # Prepare pipeline configuration
        pipeline_config = {
            "extract_config": pipeline.extract_config,
            "transform_config": pipeline.transform_config,
            "load_config": pipeline.load_config,
            "validation_rules": pipeline.validation_rules,
            "deduplication_config": pipeline.deduplication_config,
        }

        source_config = {"source_type": source.source_type, "connection_config": source.connection_config}

        # Execute pipeline
        pipeline_service = PipelineService()
        execution_report = pipeline_service.execute_pipeline(pipeline_config, source_config)

        # Update execution record
        execution.status = execution_report["status"]
        execution.completed_at = datetime.utcnow()
        execution.duration_seconds = execution_report["duration_seconds"]
        execution.records_extracted = execution_report["records_extracted"]
        execution.records_transformed = execution_report["records_transformed"]
        execution.records_loaded = execution_report["records_loaded"]
        execution.records_duplicates = execution_report["records_duplicates"]
        execution.execution_logs = execution_report["steps"]

        # Update pipeline last_run
        pipeline.last_run = datetime.utcnow()

        self.db.commit()

        logger.info(f"Pipeline execution completed: {pipeline_id}")
        return execution_report

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        error_traceback = traceback.format_exc()

        # Update execution record with error
        if execution_id:
            execution = self.db.query(ETLExecution).filter(ETLExecution.id == execution_id).first()
            if execution:
                execution.status = "failed"
                execution.completed_at = datetime.utcnow()
                execution.error_message = str(e)
                execution.error_traceback = error_traceback
                self.db.commit()

        # Retry on failure
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        raise


@celery_app.task
def check_scheduled_pipelines():
    """Check and trigger scheduled pipeline executions."""
    db = SessionLocal()

    try:
        logger.info("Checking for scheduled pipeline executions...")

        # Get active jobs that are due for execution
        now = datetime.utcnow()
        jobs = (
            db.query(ETLJob)
            .filter(
                and_(
                    ETLJob.is_active == True,
                    ETLJob.next_run <= now,
                )
            )
            .all()
        )

        logger.info(f"Found {len(jobs)} jobs to execute")

        for job in jobs:
            try:
                # Trigger pipeline execution
                execute_pipeline_task.delay(job.pipeline_id, job.id)
                logger.info(f"Triggered execution for job: {job.id}")

                # Update next run time
                job.last_run = now
                job.next_run = calculate_next_run(job.schedule_expression, job.schedule_type)
                db.commit()

            except Exception as e:
                logger.error(f"Error triggering job {job.id}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error checking scheduled pipelines: {e}")
    finally:
        db.close()


def calculate_next_run(schedule_expression: str, schedule_type: str) -> datetime:
    """Calculate next run time based on schedule."""
    from croniter import croniter

    now = datetime.utcnow()

    if schedule_type == "cron":
        # Parse cron expression
        iter = croniter(schedule_expression, now)
        return iter.get_next(datetime)

    elif schedule_type == "interval":
        # Parse interval (e.g., "5m", "1h", "1d")
        import re

        match = re.match(r"(\d+)([smhd])", schedule_expression)
        if not match:
            raise ValueError(f"Invalid interval expression: {schedule_expression}")

        value, unit = int(match.group(1)), match.group(2)

        if unit == "s":
            return now + timedelta(seconds=value)
        elif unit == "m":
            return now + timedelta(minutes=value)
        elif unit == "h":
            return now + timedelta(hours=value)
        elif unit == "d":
            return now + timedelta(days=value)

    elif schedule_type == "once":
        # For one-time jobs, set next run far in the future
        return now + timedelta(days=365 * 10)

    else:
        raise ValueError(f"Unknown schedule type: {schedule_type}")


@celery_app.task(base=DatabaseTask, bind=True)
def cleanup_old_executions(self, days: int = 30):
    """Clean up old execution records."""
    try:
        logger.info(f"Cleaning up executions older than {days} days...")

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted = (
            self.db.query(ETLExecution)
            .filter(ETLExecution.started_at < cutoff_date)
            .delete(synchronize_session=False)
        )

        self.db.commit()
        logger.info(f"Deleted {deleted} old execution records")

    except Exception as e:
        logger.error(f"Error cleaning up executions: {e}")
        raise


@celery_app.task
def test_connection_task(source_id: str) -> dict:
    """Test data source connection."""
    db = SessionLocal()

    try:
        from modules.etl.connectors.factory import ConnectorFactory

        source = db.query(DataSource).filter(DataSource.id == source_id).first()
        if not source:
            return {"success": False, "error": "Data source not found"}

        connector = ConnectorFactory.create_connector(source.source_type, source.connection_config)

        if connector.connect():
            is_valid = connector.test_connection()
            connector.disconnect()
            return {"success": is_valid, "message": "Connection successful" if is_valid else "Connection failed"}
        else:
            return {"success": False, "error": "Failed to connect"}

    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()
