"""Celery tasks for Pipeline module."""

from celery import Celery, Task
from datetime import datetime
from typing import Dict, Any, List
import time

from config.settings import settings
from config.database import get_db_context
from core.utils import get_logger
from .models import (
    Pipeline, PipelineStep, PipelineExecution, StepExecution,
    ExecutionStatus, Connector
)
from .connectors import ConnectorFactory
from .transformations import TransformationFactory, TransformationPipeline

logger = get_logger(__name__)

# Create Celery app
celery_app = Celery(
    "nexus_pipeline",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=7200,  # 2 hours
    task_soft_time_limit=3600,  # 1 hour
)


class PipelineTask(Task):
    """Base task class for pipeline tasks."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Task {task_id} failed: {exc}")

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        logger.info(f"Task {task_id} completed successfully")


@celery_app.task(base=PipelineTask, bind=True)
def execute_pipeline_task(self, pipeline_id: int, execution_id: int, config: Dict[str, Any] = None):
    """
    Execute a pipeline asynchronously.

    Args:
        pipeline_id: Pipeline ID
        execution_id: Execution ID
        config: Execution configuration
    """
    logger.info(f"Starting pipeline execution: pipeline_id={pipeline_id}, execution_id={execution_id}")

    with get_db_context() as db:
        try:
            # Get pipeline execution
            execution = db.query(PipelineExecution).filter_by(id=execution_id).first()
            if not execution:
                raise ValueError(f"Execution {execution_id} not found")

            # Update execution status
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = datetime.utcnow()
            db.commit()

            # Get pipeline and steps
            pipeline = db.query(Pipeline).filter_by(id=pipeline_id).first()
            if not pipeline:
                raise ValueError(f"Pipeline {pipeline_id} not found")

            steps = db.query(PipelineStep).filter_by(pipeline_id=pipeline_id).order_by(PipelineStep.order).all()

            # Execute each step
            total_records = 0
            failed_records = 0

            for step in steps:
                logger.info(f"Executing step: {step.name}")

                # Create step execution record
                step_execution = StepExecution(
                    pipeline_execution_id=execution_id,
                    step_id=step.id,
                    status=ExecutionStatus.RUNNING,
                    started_at=datetime.utcnow()
                )
                db.add(step_execution)
                db.commit()

                try:
                    # Execute step
                    step_result = execute_step(db, step, config or {})

                    # Update step execution
                    step_execution.status = ExecutionStatus.SUCCESS
                    step_execution.completed_at = datetime.utcnow()
                    step_execution.duration = (step_execution.completed_at - step_execution.started_at).total_seconds()
                    step_execution.records_processed = step_result.get("records_processed", 0)
                    step_execution.records_failed = step_result.get("records_failed", 0)
                    step_execution.metrics = step_result.get("metrics", {})

                    total_records += step_result.get("records_processed", 0)
                    failed_records += step_result.get("records_failed", 0)

                except Exception as e:
                    logger.error(f"Step {step.name} failed: {e}")

                    # Update step execution
                    step_execution.status = ExecutionStatus.FAILED
                    step_execution.completed_at = datetime.utcnow()
                    step_execution.duration = (step_execution.completed_at - step_execution.started_at).total_seconds()
                    step_execution.error_message = str(e)

                    # Check if step has retry configuration
                    if step_execution.retry_count < step.max_retries:
                        logger.info(f"Retrying step {step.name} (attempt {step_execution.retry_count + 1}/{step.max_retries})")
                        step_execution.retry_count += 1
                        step_execution.status = ExecutionStatus.RETRYING
                        db.commit()

                        # Wait before retry
                        time.sleep(step.retry_delay)

                        # Retry step
                        continue
                    else:
                        # Mark execution as failed
                        execution.status = ExecutionStatus.FAILED
                        execution.error_message = f"Step {step.name} failed: {e}"
                        db.commit()
                        raise

                db.commit()

            # Update execution status
            execution.status = ExecutionStatus.SUCCESS
            execution.completed_at = datetime.utcnow()
            execution.duration = (execution.completed_at - execution.started_at).total_seconds()
            execution.records_processed = total_records
            execution.records_failed = failed_records
            db.commit()

            logger.info(f"Pipeline execution completed: {execution_id}")

            return {
                "execution_id": execution_id,
                "status": "success",
                "records_processed": total_records,
                "records_failed": failed_records
            }

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")

            # Update execution status
            execution.status = ExecutionStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.duration = (execution.completed_at - execution.started_at).total_seconds() if execution.started_at else 0
            execution.error_message = str(e)
            db.commit()

            raise


def execute_step(db, step: PipelineStep, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single pipeline step.

    Args:
        db: Database session
        step: Pipeline step
        config: Execution configuration

    Returns:
        Step execution results
    """
    start_time = time.time()
    records_processed = 0
    records_failed = 0
    data = []

    try:
        # Extract data from source
        if step.source_connector_id:
            source_connector = db.query(Connector).filter_by(id=step.source_connector_id).first()
            if source_connector:
                logger.info(f"Reading from source: {source_connector.name}")

                connector = ConnectorFactory.create(
                    source_connector.connector_type,
                    {**source_connector.config, **source_connector.credentials}
                )

                with connector:
                    # Get read parameters from step config
                    read_params = step.config.get("source_params", {})
                    data = list(connector.read(**read_params))
                    records_processed = len(data)

                logger.info(f"Read {records_processed} records from source")

        # Apply transformations
        transformations_config = step.config.get("transformations", [])
        if transformations_config:
            logger.info(f"Applying {len(transformations_config)} transformations")

            transformations = []
            for transform_config in transformations_config:
                transform_type = transform_config.get("type")
                transform_params = transform_config.get("params", {})

                transformation = TransformationFactory.create(transform_type, transform_params)
                transformations.append(transformation)

            pipeline = TransformationPipeline(transformations)
            data = pipeline.execute(data)

            logger.info(f"Transformed data: {len(data)} records")

        # Load data to destination
        if step.destination_connector_id and data:
            dest_connector = db.query(Connector).filter_by(id=step.destination_connector_id).first()
            if dest_connector:
                logger.info(f"Writing to destination: {dest_connector.name}")

                connector = ConnectorFactory.create(
                    dest_connector.connector_type,
                    {**dest_connector.config, **dest_connector.credentials}
                )

                with connector:
                    # Get write parameters from step config
                    write_params = step.config.get("destination_params", {})
                    result = connector.write(data, **write_params)
                    records_processed = result.get("records_written", len(data))

                logger.info(f"Wrote {records_processed} records to destination")

        # Calculate metrics
        duration = time.time() - start_time

        return {
            "records_processed": records_processed,
            "records_failed": records_failed,
            "metrics": {
                "duration": duration,
                "records_per_second": records_processed / duration if duration > 0 else 0
            }
        }

    except Exception as e:
        logger.error(f"Step execution failed: {e}")
        raise


@celery_app.task(base=PipelineTask)
def test_connector_task(connector_id: int):
    """
    Test a connector connection asynchronously.

    Args:
        connector_id: Connector ID

    Returns:
        Test results
    """
    logger.info(f"Testing connector: {connector_id}")

    with get_db_context() as db:
        connector_model = db.query(Connector).filter_by(id=connector_id).first()
        if not connector_model:
            raise ValueError(f"Connector {connector_id} not found")

        try:
            connector = ConnectorFactory.create(
                connector_model.connector_type,
                {**connector_model.config, **connector_model.credentials}
            )

            result = connector.test_connection()

            # Update connector test status
            connector_model.last_tested_at = datetime.utcnow()
            connector_model.last_test_status = result.get("status")
            db.commit()

            return result

        except Exception as e:
            logger.error(f"Connector test failed: {e}")

            # Update connector test status
            connector_model.last_tested_at = datetime.utcnow()
            connector_model.last_test_status = "failed"
            db.commit()

            return {
                "status": "failed",
                "message": str(e)
            }


@celery_app.task(base=PipelineTask)
def cleanup_old_executions_task(days: int = 30):
    """
    Cleanup old pipeline executions.

    Args:
        days: Number of days to keep executions

    Returns:
        Cleanup results
    """
    logger.info(f"Cleaning up executions older than {days} days")

    with get_db_context() as db:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Delete old executions
        deleted_count = db.query(PipelineExecution).filter(
            PipelineExecution.created_at < cutoff_date
        ).delete()

        db.commit()

        logger.info(f"Deleted {deleted_count} old executions")

        return {
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }


@celery_app.task(base=PipelineTask)
def backfill_pipeline_task(pipeline_id: int, start_date: str, end_date: str):
    """
    Backfill a pipeline for a date range.

    Args:
        pipeline_id: Pipeline ID
        start_date: Start date (ISO format)
        end_date: End date (ISO format)

    Returns:
        Backfill results
    """
    from datetime import datetime, timedelta

    logger.info(f"Starting backfill: pipeline_id={pipeline_id}, start={start_date}, end={end_date}")

    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)

    executions = []

    with get_db_context() as db:
        pipeline = db.query(Pipeline).filter_by(id=pipeline_id).first()
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        # Create execution for each day
        current_date = start
        while current_date <= end:
            execution = PipelineExecution(
                pipeline_id=pipeline_id,
                status=ExecutionStatus.PENDING,
                trigger_type="manual",
                is_backfill=True,
                backfill_start_date=current_date,
                backfill_end_date=current_date + timedelta(days=1),
                execution_config={"backfill_date": current_date.isoformat()}
            )
            db.add(execution)
            db.commit()

            # Execute pipeline
            execute_pipeline_task.delay(pipeline_id, execution.id)

            executions.append(execution.id)
            current_date += timedelta(days=1)

        return {
            "executions_created": len(executions),
            "execution_ids": executions
        }
