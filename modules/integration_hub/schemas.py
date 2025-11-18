"""
Pydantic schemas for API request/response validation.

This module defines the data validation schemas used by the FastAPI
endpoints for creating, updating, and retrieving integration data.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator, HttpUrl, EmailStr
from enum import Enum


# Enums
class AuthTypeSchema(str, Enum):
    """Authentication type enumeration."""
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    JWT = "jwt"
    BASIC = "basic"
    CUSTOM = "custom"


class IntegrationStatusSchema(str, Enum):
    """Integration status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"
    EXPIRED = "expired"


class SyncStatusSchema(str, Enum):
    """Sync status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class SyncDirectionSchema(str, Enum):
    """Sync direction enumeration."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class WebhookStatusSchema(str, Enum):
    """Webhook status enumeration."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


# Integration Schemas
class IntegrationBase(BaseModel):
    """Base schema for integration."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    provider: str = Field(..., min_length=1, max_length=100)
    auth_type: AuthTypeSchema
    icon_url: Optional[HttpUrl] = None
    category: Optional[str] = Field(None, max_length=100)


class IntegrationCreate(IntegrationBase):
    """Schema for creating an integration."""
    config: Dict[str, Any] = Field(default_factory=dict)
    default_scopes: List[str] = Field(default_factory=list)
    api_base_url: Optional[HttpUrl] = None
    documentation_url: Optional[HttpUrl] = None
    rate_limit_requests: Optional[int] = Field(None, gt=0)
    rate_limit_period: Optional[int] = Field(None, gt=0)
    supports_webhooks: bool = False
    supports_bidirectional_sync: bool = False
    supports_batch_operations: bool = False
    version: Optional[str] = Field(None, max_length=50)
    is_premium: bool = False


class IntegrationUpdate(BaseModel):
    """Schema for updating an integration."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    default_scopes: Optional[List[str]] = None
    api_base_url: Optional[HttpUrl] = None
    rate_limit_requests: Optional[int] = Field(None, gt=0)
    rate_limit_period: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class IntegrationResponse(IntegrationBase):
    """Schema for integration response."""
    id: int
    config: Dict[str, Any]
    default_scopes: List[str]
    api_base_url: Optional[str] = None
    documentation_url: Optional[str] = None
    rate_limit_requests: Optional[int] = None
    rate_limit_period: Optional[int] = None
    supports_webhooks: bool
    supports_bidirectional_sync: bool
    supports_batch_operations: bool
    version: Optional[str] = None
    is_active: bool
    is_premium: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Connection Schemas
class ConnectionBase(BaseModel):
    """Base schema for connection."""
    integration_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=255)
    config: Dict[str, Any] = Field(default_factory=dict)
    scopes: List[str] = Field(default_factory=list)


class ConnectionCreate(ConnectionBase):
    """Schema for creating a connection."""
    organization_id: Optional[int] = None


class ConnectionUpdate(BaseModel):
    """Schema for updating a connection."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    config: Optional[Dict[str, Any]] = None
    scopes: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ConnectionResponse(ConnectionBase):
    """Schema for connection response."""
    id: int
    user_id: int
    organization_id: Optional[int] = None
    status: IntegrationStatusSchema
    connected_account_id: Optional[str] = None
    connected_account_name: Optional[str] = None
    connected_account_email: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    consecutive_failures: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConnectionHealth(BaseModel):
    """Schema for connection health status."""
    connection_id: int
    is_healthy: bool
    status: IntegrationStatusSchema
    last_check: datetime
    consecutive_failures: int
    last_error: Optional[str] = None
    uptime_percentage: float = Field(..., ge=0, le=100)


# Credential Schemas
class CredentialCreate(BaseModel):
    """Schema for creating credentials."""
    auth_type: AuthTypeSchema
    data: Dict[str, Any] = Field(..., description="Credential data (will be encrypted)")


class CredentialResponse(BaseModel):
    """Schema for credential response (no sensitive data)."""
    id: int
    auth_type: AuthTypeSchema
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    has_access_token: bool = False
    has_refresh_token: bool = False
    token_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# OAuth Schemas
class OAuthInitiate(BaseModel):
    """Schema for initiating OAuth flow."""
    integration_id: int
    redirect_uri: HttpUrl
    state: Optional[str] = None
    scopes: Optional[List[str]] = None


class OAuthCallback(BaseModel):
    """Schema for OAuth callback."""
    code: str
    state: Optional[str] = None
    error: Optional[str] = None
    error_description: Optional[str] = None


class OAuthTokenResponse(BaseModel):
    """Schema for OAuth token response."""
    access_token: str
    token_type: str
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


# Sync Job Schemas
class SyncJobBase(BaseModel):
    """Base schema for sync job."""
    connection_id: int = Field(..., gt=0)
    name: Optional[str] = Field(None, max_length=255)
    direction: SyncDirectionSchema
    entity_type: Optional[str] = Field(None, max_length=100)


class SyncJobCreate(SyncJobBase):
    """Schema for creating a sync job."""
    sync_config: Dict[str, Any] = Field(default_factory=dict)
    filters: Dict[str, Any] = Field(default_factory=dict)
    field_mapping_id: Optional[int] = None
    max_retries: int = Field(default=3, ge=0, le=10)
    is_scheduled: bool = False
    schedule_cron: Optional[str] = None

    @validator('schedule_cron')
    def validate_cron(cls, v, values):
        """Validate cron expression if scheduled."""
        if values.get('is_scheduled') and not v:
            raise ValueError('schedule_cron is required when is_scheduled is True')
        return v


class SyncJobUpdate(BaseModel):
    """Schema for updating a sync job."""
    name: Optional[str] = Field(None, max_length=255)
    sync_config: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    is_scheduled: Optional[bool] = None
    schedule_cron: Optional[str] = None


class SyncJobResponse(SyncJobBase):
    """Schema for sync job response."""
    id: int
    status: SyncStatusSchema
    sync_config: Dict[str, Any]
    filters: Dict[str, Any]
    field_mapping_id: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    retry_count: int
    max_retries: int
    total_records: int
    processed_records: int
    successful_records: int
    failed_records: int
    skipped_records: int
    duration_seconds: Optional[float] = None
    records_per_second: Optional[float] = None
    api_calls_made: int
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    is_scheduled: bool
    schedule_cron: Optional[str] = None
    last_run_at: Optional[datetime] = None
    celery_task_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SyncJobProgress(BaseModel):
    """Schema for sync job progress."""
    job_id: int
    status: SyncStatusSchema
    progress_percentage: float = Field(..., ge=0, le=100)
    processed_records: int
    total_records: int
    current_operation: Optional[str] = None
    estimated_completion: Optional[datetime] = None


# Webhook Schemas
class WebhookBase(BaseModel):
    """Base schema for webhook."""
    connection_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=255)
    url: HttpUrl
    events: List[str] = Field(default_factory=list)


class WebhookCreate(WebhookBase):
    """Schema for creating a webhook."""
    method: str = Field(default="POST", pattern="^(GET|POST|PUT|PATCH|DELETE)$")
    is_incoming: bool = False
    secret: Optional[str] = None
    signature_header: Optional[str] = Field(None, max_length=100)
    signature_algorithm: Optional[str] = Field(None, max_length=50)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=60, ge=0)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    custom_headers: Dict[str, str] = Field(default_factory=dict)


class WebhookUpdate(BaseModel):
    """Schema for updating a webhook."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None
    custom_headers: Optional[Dict[str, str]] = None


class WebhookResponse(WebhookBase):
    """Schema for webhook response."""
    id: int
    method: str
    is_incoming: bool
    is_active: bool
    signature_header: Optional[str] = None
    signature_algorithm: Optional[str] = None
    max_retries: int
    retry_delay_seconds: int
    timeout_seconds: int
    custom_headers: Dict[str, str]
    last_triggered_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    consecutive_failures: int
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WebhookDeliveryResponse(BaseModel):
    """Schema for webhook delivery response."""
    id: int
    webhook_id: int
    status: WebhookStatusSchema
    event_type: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    response_status_code: Optional[int] = None
    response_body: Optional[str] = None
    attempted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    retry_count: int
    next_retry_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookPayload(BaseModel):
    """Schema for incoming webhook payload."""
    event: str
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None
    signature: Optional[str] = None


# Field Mapping Schemas
class FieldMappingBase(BaseModel):
    """Base schema for field mapping."""
    connection_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=255)
    entity_type: str = Field(..., max_length=100)
    direction: SyncDirectionSchema


class FieldMappingCreate(FieldMappingBase):
    """Schema for creating a field mapping."""
    description: Optional[str] = None
    mappings: Dict[str, str] = Field(default_factory=dict)
    transformations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    default_values: Dict[str, Any] = Field(default_factory=dict)
    required_fields: List[str] = Field(default_factory=list)
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    is_template: bool = False


class FieldMappingUpdate(BaseModel):
    """Schema for updating a field mapping."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    mappings: Optional[Dict[str, str]] = None
    transformations: Optional[Dict[str, Dict[str, Any]]] = None
    default_values: Optional[Dict[str, Any]] = None
    required_fields: Optional[List[str]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class FieldMappingResponse(FieldMappingBase):
    """Schema for field mapping response."""
    id: int
    description: Optional[str] = None
    mappings: Dict[str, str]
    transformations: Dict[str, Dict[str, Any]]
    default_values: Dict[str, Any]
    required_fields: List[str]
    validation_rules: Dict[str, Any]
    ai_suggested: bool
    ai_confidence: Optional[float] = None
    is_active: bool
    is_template: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FieldMappingSuggestion(BaseModel):
    """Schema for AI-suggested field mapping."""
    source_field: str
    target_field: str
    confidence: float = Field(..., ge=0, le=1)
    reasoning: Optional[str] = None
    transformation_suggested: Optional[Dict[str, Any]] = None


# Monitoring Schemas
class IntegrationMetricCreate(BaseModel):
    """Schema for creating an integration metric."""
    connection_id: int
    metric_type: str = Field(..., max_length=100)
    metric_name: str = Field(..., max_length=255)
    value: float
    dimensions: Dict[str, Any] = Field(default_factory=dict)


class IntegrationMetricResponse(BaseModel):
    """Schema for integration metric response."""
    id: int
    connection_id: int
    metric_type: str
    metric_name: str
    value: float
    dimensions: Dict[str, Any]
    timestamp: datetime

    class Config:
        from_attributes = True


class DashboardMetrics(BaseModel):
    """Schema for dashboard metrics."""
    total_connections: int
    active_connections: int
    failed_connections: int
    total_syncs_today: int
    successful_syncs_today: int
    failed_syncs_today: int
    total_records_synced_today: int
    average_sync_duration: float
    total_api_calls_today: int
    total_webhooks_delivered_today: int
    uptime_percentage: float = Field(..., ge=0, le=100)


class ConnectionMetrics(BaseModel):
    """Schema for connection-specific metrics."""
    connection_id: int
    total_syncs: int
    successful_syncs: int
    failed_syncs: int
    total_records_synced: int
    average_records_per_sync: float
    average_sync_duration: float
    total_api_calls: int
    last_sync_duration: Optional[float] = None
    success_rate: float = Field(..., ge=0, le=100)
    uptime_percentage: float = Field(..., ge=0, le=100)


# Error Response Schema
class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Batch Operation Schemas
class BatchSyncCreate(BaseModel):
    """Schema for creating batch sync jobs."""
    connection_ids: List[int] = Field(..., min_items=1)
    direction: SyncDirectionSchema
    entity_type: str
    sync_config: Dict[str, Any] = Field(default_factory=dict)
    filters: Dict[str, Any] = Field(default_factory=dict)


class BatchSyncResponse(BaseModel):
    """Schema for batch sync response."""
    job_ids: List[int]
    total_jobs: int
    created_at: datetime


# Export/Import Schemas
class IntegrationExport(BaseModel):
    """Schema for exporting integration configuration."""
    integration: IntegrationResponse
    connections: List[ConnectionResponse]
    field_mappings: List[FieldMappingResponse]
    webhooks: List[WebhookResponse]
    exported_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"


class IntegrationImport(BaseModel):
    """Schema for importing integration configuration."""
    integration: IntegrationCreate
    connections: List[ConnectionCreate] = Field(default_factory=list)
    field_mappings: List[FieldMappingCreate] = Field(default_factory=list)
    webhooks: List[WebhookCreate] = Field(default_factory=list)


# Pagination Schemas
class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Generic schema for paginated responses."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

    @validator('total_pages', always=True)
    def calculate_total_pages(cls, v, values):
        """Calculate total pages."""
        total = values.get('total', 0)
        page_size = values.get('page_size', 50)
        return (total + page_size - 1) // page_size if page_size > 0 else 0


# Test Connection Schema
class TestConnectionRequest(BaseModel):
    """Schema for testing a connection."""
    connection_id: int
    test_type: str = Field(default="ping", pattern="^(ping|auth|api_call)$")


class TestConnectionResponse(BaseModel):
    """Schema for test connection response."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[int] = None
    tested_at: datetime = Field(default_factory=datetime.utcnow)
