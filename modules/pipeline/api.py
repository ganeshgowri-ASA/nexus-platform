"""FastAPI endpoints for Pipeline module."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy.orm import Session

from config.database import get_db
from .services import PipelineService
from .models import PipelineStatus, ExecutionStatus, TriggerType

# Create router
router = APIRouter(prefix="/pipelines", tags=["pipeline"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class PipelineCreate(BaseModel):
    """Pipeline creation schema."""
    name: str = Field(..., description="Pipeline name")
    description: Optional[str] = Field(None, description="Pipeline description")
    config: dict = Field(default_factory=dict, description="Pipeline configuration")
    tags: List[str] = Field(default_factory=list, description="Pipeline tags")


class PipelineUpdate(BaseModel):
    """Pipeline update schema."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[PipelineStatus] = None
    config: Optional[dict] = None
    tags: Optional[List[str]] = None


class PipelineResponse(BaseModel):
    """Pipeline response schema."""
    id: int
    name: str
    description: Optional[str]
    status: PipelineStatus
    config: dict
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    airflow_dag_id: Optional[str]

    class Config:
        from_attributes = True


class StepCreate(BaseModel):
    """Pipeline step creation schema."""
    name: str
    step_type: str
    config: dict
    order: Optional[int] = None
    source_connector_id: Optional[int] = None
    destination_connector_id: Optional[int] = None
    depends_on: List[int] = Field(default_factory=list)


class StepUpdate(BaseModel):
    """Pipeline step update schema."""
    name: Optional[str] = None
    config: Optional[dict] = None
    order: Optional[int] = None


class ExecutionCreate(BaseModel):
    """Pipeline execution creation schema."""
    trigger_type: TriggerType = TriggerType.MANUAL
    config: dict = Field(default_factory=dict)


class ExecutionResponse(BaseModel):
    """Pipeline execution response schema."""
    id: int
    pipeline_id: int
    status: ExecutionStatus
    trigger_type: TriggerType
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration: Optional[float]
    records_processed: int
    records_failed: int
    error_message: Optional[str]

    class Config:
        from_attributes = True


class ConnectorCreate(BaseModel):
    """Connector creation schema."""
    name: str
    connector_type: str
    description: Optional[str] = None
    config: dict
    credentials: dict = Field(default_factory=dict)


class ConnectorResponse(BaseModel):
    """Connector response schema."""
    id: int
    name: str
    connector_type: str
    description: Optional[str]
    is_active: bool
    last_tested_at: Optional[datetime]
    last_test_status: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduleCreate(BaseModel):
    """Schedule creation schema."""
    cron_expression: str
    timezone: str = "UTC"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class BackfillRequest(BaseModel):
    """Backfill request schema."""
    start_date: datetime
    end_date: datetime


# ============================================================================
# Pipeline Endpoints
# ============================================================================

@router.post("/", response_model=PipelineResponse, status_code=201)
def create_pipeline(
    pipeline: PipelineCreate,
    db: Session = Depends(get_db)
):
    """Create a new pipeline."""
    service = PipelineService(db)
    result = service.create_pipeline(
        name=pipeline.name,
        description=pipeline.description,
        config=pipeline.config,
        tags=pipeline.tags
    )
    return result


@router.get("/", response_model=List[PipelineResponse])
def list_pipelines(
    status: Optional[PipelineStatus] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List all pipelines."""
    service = PipelineService(db)
    return service.list_pipelines(status=status, limit=limit, offset=offset)


@router.get("/{pipeline_id}", response_model=PipelineResponse)
def get_pipeline(
    pipeline_id: int,
    db: Session = Depends(get_db)
):
    """Get pipeline by ID."""
    service = PipelineService(db)
    pipeline = service.get_pipeline(pipeline_id)

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return pipeline


@router.put("/{pipeline_id}", response_model=PipelineResponse)
def update_pipeline(
    pipeline_id: int,
    pipeline: PipelineUpdate,
    db: Session = Depends(get_db)
):
    """Update pipeline."""
    service = PipelineService(db)

    try:
        result = service.update_pipeline(
            pipeline_id=pipeline_id,
            name=pipeline.name,
            description=pipeline.description,
            status=pipeline.status,
            config=pipeline.config,
            tags=pipeline.tags
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{pipeline_id}", status_code=204)
def delete_pipeline(
    pipeline_id: int,
    db: Session = Depends(get_db)
):
    """Delete pipeline."""
    service = PipelineService(db)

    try:
        service.delete_pipeline(pipeline_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Pipeline Step Endpoints
# ============================================================================

@router.post("/{pipeline_id}/steps", status_code=201)
def add_step(
    pipeline_id: int,
    step: StepCreate,
    db: Session = Depends(get_db)
):
    """Add a step to pipeline."""
    service = PipelineService(db)

    try:
        result = service.add_step(
            pipeline_id=pipeline_id,
            name=step.name,
            step_type=step.step_type,
            config=step.config,
            order=step.order,
            source_connector_id=step.source_connector_id,
            destination_connector_id=step.destination_connector_id,
            depends_on=step.depends_on
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/steps/{step_id}")
def update_step(
    step_id: int,
    step: StepUpdate,
    db: Session = Depends(get_db)
):
    """Update pipeline step."""
    service = PipelineService(db)

    try:
        result = service.update_step(
            step_id=step_id,
            name=step.name,
            config=step.config,
            order=step.order
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/steps/{step_id}", status_code=204)
def delete_step(
    step_id: int,
    db: Session = Depends(get_db)
):
    """Delete pipeline step."""
    service = PipelineService(db)

    try:
        service.delete_step(step_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Pipeline Execution Endpoints
# ============================================================================

@router.post("/{pipeline_id}/execute", response_model=ExecutionResponse)
def execute_pipeline(
    pipeline_id: int,
    execution: ExecutionCreate,
    db: Session = Depends(get_db)
):
    """Execute a pipeline."""
    service = PipelineService(db)

    try:
        result = service.execute_pipeline(
            pipeline_id=pipeline_id,
            trigger_type=execution.trigger_type,
            config=execution.config
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{pipeline_id}/executions", response_model=List[ExecutionResponse])
def list_executions(
    pipeline_id: int,
    status: Optional[ExecutionStatus] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List pipeline executions."""
    service = PipelineService(db)
    return service.list_executions(
        pipeline_id=pipeline_id,
        status=status,
        limit=limit,
        offset=offset
    )


@router.get("/executions/{execution_id}", response_model=ExecutionResponse)
def get_execution(
    execution_id: int,
    db: Session = Depends(get_db)
):
    """Get execution by ID."""
    service = PipelineService(db)
    execution = service.get_execution(execution_id)

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return execution


@router.post("/executions/{execution_id}/cancel", response_model=ExecutionResponse)
def cancel_execution(
    execution_id: int,
    db: Session = Depends(get_db)
):
    """Cancel a running execution."""
    service = PipelineService(db)

    try:
        result = service.cancel_execution(execution_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Connector Endpoints
# ============================================================================

@router.post("/connectors", response_model=ConnectorResponse, status_code=201)
def create_connector(
    connector: ConnectorCreate,
    db: Session = Depends(get_db)
):
    """Create a new connector."""
    service = PipelineService(db)
    result = service.create_connector(
        name=connector.name,
        connector_type=connector.connector_type,
        config=connector.config,
        credentials=connector.credentials,
        description=connector.description
    )
    return result


@router.get("/connectors", response_model=List[ConnectorResponse])
def list_connectors(
    connector_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List all connectors."""
    service = PipelineService(db)
    return service.list_connectors(
        connector_type=connector_type,
        is_active=is_active
    )


@router.post("/connectors/{connector_id}/test")
def test_connector(
    connector_id: int,
    db: Session = Depends(get_db)
):
    """Test connector connection."""
    service = PipelineService(db)
    return service.test_connector(connector_id)


# ============================================================================
# Schedule Endpoints
# ============================================================================

@router.post("/{pipeline_id}/schedules", status_code=201)
def create_schedule(
    pipeline_id: int,
    schedule: ScheduleCreate,
    db: Session = Depends(get_db)
):
    """Create a schedule for pipeline."""
    service = PipelineService(db)

    try:
        result = service.create_schedule(
            pipeline_id=pipeline_id,
            cron_expression=schedule.cron_expression,
            timezone=schedule.timezone,
            start_date=schedule.start_date,
            end_date=schedule.end_date
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/schedules/{schedule_id}/activate")
def activate_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """Activate a schedule."""
    service = PipelineService(db)

    try:
        result = service.activate_schedule(schedule_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Airflow Integration Endpoints
# ============================================================================

@router.post("/{pipeline_id}/sync-to-airflow")
def sync_to_airflow(
    pipeline_id: int,
    db: Session = Depends(get_db)
):
    """Sync pipeline to Airflow DAG."""
    service = PipelineService(db)

    try:
        result = service.sync_to_airflow(pipeline_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Backfill Endpoints
# ============================================================================

@router.post("/{pipeline_id}/backfill")
def backfill_pipeline(
    pipeline_id: int,
    backfill: BackfillRequest,
    db: Session = Depends(get_db)
):
    """Backfill pipeline for date range."""
    service = PipelineService(db)

    try:
        result = service.backfill_pipeline(
            pipeline_id=pipeline_id,
            start_date=backfill.start_date,
            end_date=backfill.end_date
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Metrics Endpoints
# ============================================================================

@router.get("/{pipeline_id}/metrics")
def get_pipeline_metrics(
    pipeline_id: int,
    db: Session = Depends(get_db)
):
    """Get pipeline metrics."""
    service = PipelineService(db)
    return service.get_pipeline_metrics(pipeline_id)
