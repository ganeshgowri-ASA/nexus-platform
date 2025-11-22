"""
FastAPI endpoints for Integration Hub management.

Provides RESTful API for managing integrations, connections, sync jobs,
webhooks, and field mappings.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from . import schemas
from .models import (
    Integration, Connection, SyncJob, Webhook, FieldMapping,
    IntegrationStatus, SyncStatus, SyncDirection
)
from .registry import IntegrationRegistry, ConnectorFactory, ConfigManager
from .oauth import OAuthFlowManager
from .webhooks import WebhookManager
from .sync import DataSync
from .mapping import FieldMapper
from .monitoring import IntegrationMetrics, SyncStatusMonitor
from .rate_limiting import RateLimiter

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


# Dependency to get DB session (placeholder - replace with actual NEXUS DB session)
def get_db():
    """Get database session."""
    # This should be replaced with actual NEXUS database session
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine("sqlite:///integration_hub.db")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency to get current user (placeholder - replace with actual NEXUS auth)
def get_current_user():
    """Get current authenticated user."""
    # This should be replaced with actual NEXUS authentication
    return {"id": 1, "email": "user@example.com"}


# Integrations Endpoints
@router.get("/", response_model=List[schemas.IntegrationResponse])
def list_integrations(
    category: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all available integrations."""
    registry = IntegrationRegistry(db)
    integrations = registry.list_integrations(category=category, active_only=active_only)
    return integrations


@router.get("/{integration_id}", response_model=schemas.IntegrationResponse)
def get_integration(
    integration_id: int,
    db: Session = Depends(get_db)
):
    """Get integration by ID."""
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return integration


@router.post("/", response_model=schemas.IntegrationResponse, status_code=201)
def create_integration(
    integration: schemas.IntegrationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new integration."""
    registry = IntegrationRegistry(db)

    db_integration = registry.register_integration(
        name=integration.name,
        slug=integration.slug,
        provider=integration.provider,
        auth_type=integration.auth_type,
        config=integration.config,
        description=integration.description,
        icon_url=str(integration.icon_url) if integration.icon_url else None,
        category=integration.category,
        default_scopes=integration.default_scopes,
        api_base_url=str(integration.api_base_url) if integration.api_base_url else None,
        documentation_url=str(integration.documentation_url) if integration.documentation_url else None,
        rate_limit_requests=integration.rate_limit_requests,
        rate_limit_period=integration.rate_limit_period,
        supports_webhooks=integration.supports_webhooks,
        supports_bidirectional_sync=integration.supports_bidirectional_sync,
        supports_batch_operations=integration.supports_batch_operations,
        version=integration.version,
        is_premium=integration.is_premium,
        created_by=current_user["id"]
    )

    return db_integration


# Connections Endpoints
@router.get("/connections/", response_model=List[schemas.ConnectionResponse])
def list_connections(
    status: Optional[IntegrationStatus] = None,
    integration_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List user's connections."""
    query = db.query(Connection).filter(Connection.user_id == current_user["id"])

    if status:
        query = query.filter(Connection.status == status)

    if integration_id:
        query = query.filter(Connection.integration_id == integration_id)

    return query.all()


@router.get("/connections/{connection_id}", response_model=schemas.ConnectionResponse)
def get_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get connection by ID."""
    connection = db.query(Connection).filter(
        Connection.id == connection_id,
        Connection.user_id == current_user["id"]
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    return connection


@router.post("/connections/", response_model=schemas.ConnectionResponse, status_code=201)
def create_connection(
    connection: schemas.ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new connection."""
    db_connection = Connection(
        integration_id=connection.integration_id,
        user_id=current_user["id"],
        organization_id=connection.organization_id,
        name=connection.name,
        config=connection.config,
        scopes=connection.scopes,
        status=IntegrationStatus.PENDING
    )

    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)

    return db_connection


@router.patch("/connections/{connection_id}", response_model=schemas.ConnectionResponse)
def update_connection(
    connection_id: int,
    updates: schemas.ConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a connection."""
    connection = db.query(Connection).filter(
        Connection.id == connection_id,
        Connection.user_id == current_user["id"]
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(connection, field, value)

    db.commit()
    db.refresh(connection)

    return connection


@router.delete("/connections/{connection_id}", status_code=204)
def delete_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a connection."""
    connection = db.query(Connection).filter(
        Connection.id == connection_id,
        Connection.user_id == current_user["id"]
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    db.delete(connection)
    db.commit()

    return None


@router.post("/connections/{connection_id}/test", response_model=schemas.TestConnectionResponse)
async def test_connection(
    connection_id: int,
    request: schemas.TestConnectionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Test a connection."""
    connection = db.query(Connection).filter(
        Connection.id == connection_id,
        Connection.user_id == current_user["id"]
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        # Create connector and test
        factory = ConnectorFactory(db, encryption_key=b"dummy_key_replace_with_actual")
        connector = factory.create_connector(connection_id)

        start_time = datetime.now()
        result = await connector.test_connection()
        end_time = datetime.now()

        response_time = int((end_time - start_time).total_seconds() * 1000)

        return schemas.TestConnectionResponse(
            success=result.get('success', False),
            message=result.get('message', ''),
            details=result,
            response_time_ms=response_time
        )

    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return schemas.TestConnectionResponse(
            success=False,
            message=f"Test failed: {str(e)}",
            details={'error': str(e)}
        )


# OAuth Endpoints
@router.get("/oauth/{integration_id}/authorize")
def initiate_oauth(
    integration_id: int,
    redirect_uri: str,
    scopes: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """Initiate OAuth authorization flow."""
    oauth_manager = OAuthFlowManager(db, encryption_key=b"dummy_key_replace_with_actual")

    auth_data = oauth_manager.get_authorization_url(
        integration_id=integration_id,
        redirect_uri=redirect_uri,
        scopes=scopes
    )

    return auth_data


@router.post("/oauth/callback", response_model=schemas.ConnectionResponse)
async def oauth_callback(
    callback: schemas.OAuthCallback,
    state: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Handle OAuth callback."""
    if callback.error:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth error: {callback.error} - {callback.error_description}"
        )

    oauth_manager = OAuthFlowManager(db, encryption_key=b"dummy_key_replace_with_actual")

    connection = await oauth_manager.handle_callback(
        code=callback.code,
        state=state,
        user_id=current_user["id"]
    )

    return connection


# Sync Jobs Endpoints
@router.get("/sync-jobs/", response_model=List[schemas.SyncJobResponse])
def list_sync_jobs(
    connection_id: Optional[int] = None,
    status: Optional[SyncStatus] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List sync jobs."""
    query = db.query(SyncJob).join(Connection).filter(
        Connection.user_id == current_user["id"]
    )

    if connection_id:
        query = query.filter(SyncJob.connection_id == connection_id)

    if status:
        query = query.filter(SyncJob.status == status)

    return query.order_by(SyncJob.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/sync-jobs/{job_id}", response_model=schemas.SyncJobResponse)
def get_sync_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get sync job by ID."""
    job = db.query(SyncJob).join(Connection).filter(
        SyncJob.id == job_id,
        Connection.user_id == current_user["id"]
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Sync job not found")

    return job


@router.post("/sync-jobs/", response_model=schemas.SyncJobResponse, status_code=201)
async def create_sync_job(
    job: schemas.SyncJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create and start a sync job."""
    # Verify connection belongs to user
    connection = db.query(Connection).filter(
        Connection.id == job.connection_id,
        Connection.user_id == current_user["id"]
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    db_job = SyncJob(
        connection_id=job.connection_id,
        name=job.name,
        direction=job.direction,
        entity_type=job.entity_type,
        sync_config=job.sync_config,
        filters=job.filters,
        field_mapping_id=job.field_mapping_id,
        max_retries=job.max_retries,
        is_scheduled=job.is_scheduled,
        schedule_cron=job.schedule_cron,
        created_by=current_user["id"]
    )

    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    # TODO: Trigger async job via Celery
    # background_tasks.add_task(run_sync_job, db_job.id)

    return db_job


@router.get("/sync-jobs/{job_id}/progress", response_model=schemas.SyncJobProgress)
def get_sync_progress(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get sync job progress."""
    monitor = SyncStatusMonitor(db)
    status = monitor.get_sync_status(job_id)

    if 'error' in status:
        raise HTTPException(status_code=404, detail=status['error'])

    return status


# Webhooks Endpoints
@router.get("/webhooks/", response_model=List[schemas.WebhookResponse])
def list_webhooks(
    connection_id: Optional[int] = None,
    is_incoming: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List webhooks."""
    query = db.query(Webhook).join(Connection).filter(
        Connection.user_id == current_user["id"]
    )

    if connection_id:
        query = query.filter(Webhook.connection_id == connection_id)

    if is_incoming is not None:
        query = query.filter(Webhook.is_incoming == is_incoming)

    return query.all()


@router.post("/webhooks/", response_model=schemas.WebhookResponse, status_code=201)
def create_webhook(
    webhook: schemas.WebhookCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a webhook."""
    # Verify connection
    connection = db.query(Connection).filter(
        Connection.id == webhook.connection_id,
        Connection.user_id == current_user["id"]
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    manager = WebhookManager(db)
    db_webhook = manager.create_webhook(
        connection_id=webhook.connection_id,
        name=webhook.name,
        url=str(webhook.url),
        events=webhook.events,
        method=webhook.method,
        is_incoming=webhook.is_incoming,
        secret=webhook.secret,
        signature_header=webhook.signature_header,
        signature_algorithm=webhook.signature_algorithm,
        max_retries=webhook.max_retries,
        retry_delay_seconds=webhook.retry_delay_seconds,
        timeout_seconds=webhook.timeout_seconds,
        custom_headers=webhook.custom_headers
    )

    return db_webhook


# Field Mappings Endpoints
@router.get("/field-mappings/", response_model=List[schemas.FieldMappingResponse])
def list_field_mappings(
    connection_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List field mappings."""
    query = db.query(FieldMapping).join(Connection).filter(
        Connection.user_id == current_user["id"]
    )

    if connection_id:
        query = query.filter(FieldMapping.connection_id == connection_id)

    return query.all()


@router.post("/field-mappings/", response_model=schemas.FieldMappingResponse, status_code=201)
def create_field_mapping(
    mapping: schemas.FieldMappingCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a field mapping."""
    # Verify connection
    connection = db.query(Connection).filter(
        Connection.id == mapping.connection_id,
        Connection.user_id == current_user["id"]
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    mapper = FieldMapper(db)
    db_mapping = mapper.create_mapping(
        connection_id=mapping.connection_id,
        name=mapping.name,
        entity_type=mapping.entity_type,
        direction=mapping.direction,
        mappings=mapping.mappings,
        description=mapping.description,
        transformations=mapping.transformations,
        default_values=mapping.default_values,
        required_fields=mapping.required_fields,
        validation_rules=mapping.validation_rules,
        is_template=mapping.is_template,
        created_by=current_user["id"]
    )

    return db_mapping


# Monitoring Endpoints
@router.get("/metrics/dashboard", response_model=schemas.DashboardMetrics)
def get_dashboard_metrics(
    db: Session = Depends(get_db)
):
    """Get dashboard metrics."""
    metrics = IntegrationMetrics(db)
    return metrics.get_dashboard_metrics()


@router.get("/metrics/connections/{connection_id}", response_model=schemas.ConnectionMetrics)
def get_connection_metrics(
    connection_id: int,
    period_days: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get metrics for a specific connection."""
    # Verify connection
    connection = db.query(Connection).filter(
        Connection.id == connection_id,
        Connection.user_id == current_user["id"]
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    metrics = IntegrationMetrics(db)
    return metrics.get_connection_metrics(connection_id, period_days)


@router.get("/health/{connection_id}", response_model=schemas.ConnectionHealth)
def check_connection_health(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Check connection health."""
    monitor = SyncStatusMonitor(db)
    health = monitor.check_connection_health(connection_id)

    if 'error' in health:
        raise HTTPException(status_code=404, detail=health['error'])

    return health
