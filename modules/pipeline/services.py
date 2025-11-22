"""Service layer for Pipeline module."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.utils import get_logger
from .models import (
    Pipeline, PipelineStep, PipelineExecution, StepExecution,
    Connector, Schedule, PipelineStatus, ExecutionStatus, TriggerType
)
from .config import pipeline_config
from .tasks import execute_pipeline_task, test_connector_task, backfill_pipeline_task
from .airflow_integration import AirflowService

logger = get_logger(__name__)


class PipelineService:
    """Service for pipeline operations."""

    def __init__(self, db: Session):
        """
        Initialize pipeline service.

        Args:
            db: Database session
        """
        self.db = db
        self.airflow_service = AirflowService()

    # ========================================================================
    # Pipeline CRUD Operations
    # ========================================================================

    def create_pipeline(
        self,
        name: str,
        description: Optional[str] = None,
        config: Dict[str, Any] = None,
        tags: List[str] = None
    ) -> Pipeline:
        """
        Create a new pipeline.

        Args:
            name: Pipeline name
            description: Pipeline description
            config: Pipeline configuration
            tags: Pipeline tags

        Returns:
            Created pipeline
        """
        pipeline = Pipeline(
            name=name,
            description=description,
            status=PipelineStatus.DRAFT,
            config=config or {},
            tags=tags or []
        )

        self.db.add(pipeline)
        self.db.commit()
        self.db.refresh(pipeline)

        logger.info(f"Created pipeline: {pipeline.id} - {name}")

        return pipeline

    def get_pipeline(self, pipeline_id: int) -> Optional[Pipeline]:
        """
        Get pipeline by ID.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            Pipeline or None
        """
        return self.db.query(Pipeline).filter_by(id=pipeline_id).first()

    def list_pipelines(
        self,
        status: Optional[PipelineStatus] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Pipeline]:
        """
        List pipelines with optional filters.

        Args:
            status: Filter by status
            tags: Filter by tags
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of pipelines
        """
        query = self.db.query(Pipeline)

        if status:
            query = query.filter(Pipeline.status == status)

        if tags:
            # Filter by tags (any match)
            query = query.filter(Pipeline.tags.contains(tags))

        query = query.order_by(desc(Pipeline.created_at))
        query = query.limit(limit).offset(offset)

        return query.all()

    def update_pipeline(
        self,
        pipeline_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[PipelineStatus] = None,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Pipeline:
        """
        Update pipeline.

        Args:
            pipeline_id: Pipeline ID
            name: New name
            description: New description
            status: New status
            config: New configuration
            tags: New tags

        Returns:
            Updated pipeline
        """
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        if name is not None:
            pipeline.name = name
        if description is not None:
            pipeline.description = description
        if status is not None:
            pipeline.status = status
        if config is not None:
            pipeline.config = config
        if tags is not None:
            pipeline.tags = tags

        pipeline.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(pipeline)

        logger.info(f"Updated pipeline: {pipeline_id}")

        return pipeline

    def delete_pipeline(self, pipeline_id: int) -> bool:
        """
        Delete pipeline.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            True if deleted
        """
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        # Delete from Airflow if exists
        if pipeline.airflow_dag_id:
            self.airflow_service.delete_dag(pipeline.airflow_dag_id)

        self.db.delete(pipeline)
        self.db.commit()

        logger.info(f"Deleted pipeline: {pipeline_id}")

        return True

    # ========================================================================
    # Pipeline Step Operations
    # ========================================================================

    def add_step(
        self,
        pipeline_id: int,
        name: str,
        step_type: str,
        config: Dict[str, Any],
        order: Optional[int] = None,
        source_connector_id: Optional[int] = None,
        destination_connector_id: Optional[int] = None,
        depends_on: List[int] = None
    ) -> PipelineStep:
        """
        Add a step to pipeline.

        Args:
            pipeline_id: Pipeline ID
            name: Step name
            step_type: Step type (extract, transform, load)
            config: Step configuration
            order: Step order
            source_connector_id: Source connector ID
            destination_connector_id: Destination connector ID
            depends_on: List of step IDs this step depends on

        Returns:
            Created step
        """
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        # Auto-assign order if not provided
        if order is None:
            max_order = self.db.query(PipelineStep).filter_by(pipeline_id=pipeline_id).count()
            order = max_order + 1

        step = PipelineStep(
            pipeline_id=pipeline_id,
            name=name,
            step_type=step_type,
            order=order,
            config=config,
            source_connector_id=source_connector_id,
            destination_connector_id=destination_connector_id,
            depends_on=depends_on or []
        )

        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)

        logger.info(f"Added step to pipeline {pipeline_id}: {step.id} - {name}")

        return step

    def update_step(
        self,
        step_id: int,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        order: Optional[int] = None
    ) -> PipelineStep:
        """
        Update pipeline step.

        Args:
            step_id: Step ID
            name: New name
            config: New configuration
            order: New order

        Returns:
            Updated step
        """
        step = self.db.query(PipelineStep).filter_by(id=step_id).first()
        if not step:
            raise ValueError(f"Step {step_id} not found")

        if name is not None:
            step.name = name
        if config is not None:
            step.config = config
        if order is not None:
            step.order = order

        step.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(step)

        return step

    def delete_step(self, step_id: int) -> bool:
        """
        Delete pipeline step.

        Args:
            step_id: Step ID

        Returns:
            True if deleted
        """
        step = self.db.query(PipelineStep).filter_by(id=step_id).first()
        if not step:
            raise ValueError(f"Step {step_id} not found")

        self.db.delete(step)
        self.db.commit()

        logger.info(f"Deleted step: {step_id}")

        return True

    # ========================================================================
    # Pipeline Execution
    # ========================================================================

    def execute_pipeline(
        self,
        pipeline_id: int,
        trigger_type: TriggerType = TriggerType.MANUAL,
        config: Dict[str, Any] = None
    ) -> PipelineExecution:
        """
        Execute a pipeline.

        Args:
            pipeline_id: Pipeline ID
            trigger_type: Trigger type
            config: Execution configuration

        Returns:
            Pipeline execution
        """
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        if pipeline.status != PipelineStatus.ACTIVE:
            raise ValueError(f"Pipeline {pipeline_id} is not active")

        # Create execution record
        execution = PipelineExecution(
            pipeline_id=pipeline_id,
            status=ExecutionStatus.PENDING,
            trigger_type=trigger_type,
            execution_config=config or {}
        )

        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        # Execute asynchronously with Celery
        execute_pipeline_task.delay(pipeline_id, execution.id, config)

        logger.info(f"Started pipeline execution: {execution.id}")

        return execution

    def get_execution(self, execution_id: int) -> Optional[PipelineExecution]:
        """
        Get execution by ID.

        Args:
            execution_id: Execution ID

        Returns:
            Execution or None
        """
        return self.db.query(PipelineExecution).filter_by(id=execution_id).first()

    def list_executions(
        self,
        pipeline_id: Optional[int] = None,
        status: Optional[ExecutionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PipelineExecution]:
        """
        List pipeline executions.

        Args:
            pipeline_id: Filter by pipeline ID
            status: Filter by status
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of executions
        """
        query = self.db.query(PipelineExecution)

        if pipeline_id:
            query = query.filter(PipelineExecution.pipeline_id == pipeline_id)

        if status:
            query = query.filter(PipelineExecution.status == status)

        query = query.order_by(desc(PipelineExecution.created_at))
        query = query.limit(limit).offset(offset)

        return query.all()

    def cancel_execution(self, execution_id: int) -> PipelineExecution:
        """
        Cancel a running execution.

        Args:
            execution_id: Execution ID

        Returns:
            Updated execution
        """
        execution = self.get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if execution.status != ExecutionStatus.RUNNING:
            raise ValueError(f"Execution {execution_id} is not running")

        execution.status = ExecutionStatus.CANCELLED
        execution.completed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(execution)

        logger.info(f"Cancelled execution: {execution_id}")

        return execution

    # ========================================================================
    # Connector Operations
    # ========================================================================

    def create_connector(
        self,
        name: str,
        connector_type: str,
        config: Dict[str, Any],
        credentials: Dict[str, Any] = None,
        description: Optional[str] = None
    ) -> Connector:
        """
        Create a new connector.

        Args:
            name: Connector name
            connector_type: Connector type
            config: Connector configuration
            credentials: Connector credentials
            description: Connector description

        Returns:
            Created connector
        """
        connector = Connector(
            name=name,
            connector_type=connector_type,
            config=config,
            credentials=credentials or {},
            description=description
        )

        self.db.add(connector)
        self.db.commit()
        self.db.refresh(connector)

        logger.info(f"Created connector: {connector.id} - {name}")

        return connector

    def test_connector(self, connector_id: int) -> Dict[str, Any]:
        """
        Test a connector connection.

        Args:
            connector_id: Connector ID

        Returns:
            Test results
        """
        # Execute test asynchronously
        result = test_connector_task.delay(connector_id)

        return {
            "task_id": result.id,
            "status": "testing"
        }

    def list_connectors(
        self,
        connector_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Connector]:
        """
        List connectors.

        Args:
            connector_type: Filter by connector type
            is_active: Filter by active status

        Returns:
            List of connectors
        """
        query = self.db.query(Connector)

        if connector_type:
            query = query.filter(Connector.connector_type == connector_type)

        if is_active is not None:
            query = query.filter(Connector.is_active == is_active)

        return query.all()

    # ========================================================================
    # Scheduling Operations
    # ========================================================================

    def create_schedule(
        self,
        pipeline_id: int,
        cron_expression: str,
        timezone: str = "UTC",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Schedule:
        """
        Create a schedule for pipeline.

        Args:
            pipeline_id: Pipeline ID
            cron_expression: Cron expression
            timezone: Timezone
            start_date: Start date
            end_date: End date

        Returns:
            Created schedule
        """
        schedule = Schedule(
            pipeline_id=pipeline_id,
            cron_expression=cron_expression,
            timezone=timezone,
            start_date=start_date,
            end_date=end_date
        )

        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)

        # Sync to Airflow
        pipeline = self.get_pipeline(pipeline_id)
        if pipeline:
            self.airflow_service.sync_pipeline_to_dag(pipeline, schedule)

        logger.info(f"Created schedule for pipeline {pipeline_id}")

        return schedule

    def activate_schedule(self, schedule_id: int) -> Schedule:
        """
        Activate a schedule.

        Args:
            schedule_id: Schedule ID

        Returns:
            Updated schedule
        """
        schedule = self.db.query(Schedule).filter_by(id=schedule_id).first()
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")

        schedule.is_active = True
        self.db.commit()
        self.db.refresh(schedule)

        return schedule

    # ========================================================================
    # Airflow Integration
    # ========================================================================

    def sync_to_airflow(self, pipeline_id: int) -> Dict[str, Any]:
        """
        Sync pipeline to Airflow DAG.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            Sync results
        """
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        schedule = self.db.query(Schedule).filter_by(
            pipeline_id=pipeline_id,
            is_active=True
        ).first()

        result = self.airflow_service.sync_pipeline_to_dag(pipeline, schedule)

        if result.get("success"):
            pipeline.airflow_dag_id = result.get("dag_id")
            self.db.commit()

        return result

    # ========================================================================
    # Backfill Operations
    # ========================================================================

    def backfill_pipeline(
        self,
        pipeline_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Backfill pipeline for date range.

        Args:
            pipeline_id: Pipeline ID
            start_date: Start date
            end_date: End date

        Returns:
            Backfill task info
        """
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        # Execute backfill asynchronously
        result = backfill_pipeline_task.delay(
            pipeline_id,
            start_date.isoformat(),
            end_date.isoformat()
        )

        return {
            "task_id": result.id,
            "status": "running",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }

    # ========================================================================
    # Metrics and Monitoring
    # ========================================================================

    def get_pipeline_metrics(self, pipeline_id: int) -> Dict[str, Any]:
        """
        Get pipeline metrics.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            Pipeline metrics
        """
        executions = self.db.query(PipelineExecution).filter_by(
            pipeline_id=pipeline_id
        ).all()

        total_executions = len(executions)
        successful_executions = len([e for e in executions if e.status == ExecutionStatus.SUCCESS])
        failed_executions = len([e for e in executions if e.status == ExecutionStatus.FAILED])

        total_duration = sum([e.duration or 0 for e in executions])
        avg_duration = total_duration / total_executions if total_executions > 0 else 0

        total_records = sum([e.records_processed or 0 for e in executions])

        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "avg_duration": avg_duration,
            "total_records_processed": total_records
        }
