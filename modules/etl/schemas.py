"""
Pydantic schemas for ETL module.

This module defines request/response schemas for API validation
and data serialization.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator, ConfigDict

from modules.etl.models import (
    SourceType, DatabaseType, JobStatus, LoadStrategy
)


# Data Source Schemas
class DataSourceBase(BaseModel):
    """Base schema for data sources."""
    name: str = Field(..., min_length=1, max_length=255, description="Unique name for the data source")
    source_type: SourceType = Field(..., description="Type of data source")
    database_type: Optional[DatabaseType] = Field(None, description="Database type if applicable")
    description: Optional[str] = Field(None, description="Description of the data source")

    # Connection details
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

    # Additional configuration
    config: Dict[str, Any] = Field(default_factory=dict)

    # File/Cloud storage
    file_path: Optional[str] = None
    bucket_name: Optional[str] = None
    region: Optional[str] = None

    # API specific
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)

    is_active: bool = True


class DataSourceCreate(DataSourceBase):
    """Schema for creating a data source."""
    pass


class DataSourceUpdate(BaseModel):
    """Schema for updating a data source."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    source_type: Optional[SourceType] = None
    database_type: Optional[DatabaseType] = None
    description: Optional[str] = None
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    bucket_name: Optional[str] = None
    region: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class DataSourceResponse(DataSourceBase):
    """Schema for data source responses."""
    id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Data Target Schemas
class DataTargetBase(BaseModel):
    """Base schema for data targets."""
    name: str = Field(..., min_length=1, max_length=255)
    target_type: SourceType
    database_type: Optional[DatabaseType] = None
    description: Optional[str] = None

    # Connection details
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

    config: Dict[str, Any] = Field(default_factory=dict)

    # File/Cloud storage
    file_path: Optional[str] = None
    bucket_name: Optional[str] = None
    region: Optional[str] = None

    # API specific
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)

    load_strategy: LoadStrategy = LoadStrategy.APPEND
    is_active: bool = True


class DataTargetCreate(DataTargetBase):
    """Schema for creating a data target."""
    pass


class DataTargetUpdate(BaseModel):
    """Schema for updating a data target."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    target_type: Optional[SourceType] = None
    database_type: Optional[DatabaseType] = None
    description: Optional[str] = None
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    bucket_name: Optional[str] = None
    region: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    load_strategy: Optional[LoadStrategy] = None
    is_active: Optional[bool] = None


class DataTargetResponse(DataTargetBase):
    """Schema for data target responses."""
    id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Mapping Schemas
class MappingBase(BaseModel):
    """Base schema for field mappings."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_schema: Dict[str, Any] = Field(default_factory=dict)
    target_schema: Dict[str, Any] = Field(default_factory=dict)
    field_mappings: Dict[str, str] = Field(default_factory=dict)
    type_conversions: Dict[str, str] = Field(default_factory=dict)
    transformation_rules: Dict[str, Any] = Field(default_factory=dict)
    default_values: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class MappingCreate(MappingBase):
    """Schema for creating a mapping."""
    pass


class MappingUpdate(BaseModel):
    """Schema for updating a mapping."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    source_schema: Optional[Dict[str, Any]] = None
    target_schema: Optional[Dict[str, Any]] = None
    field_mappings: Optional[Dict[str, str]] = None
    type_conversions: Optional[Dict[str, str]] = None
    transformation_rules: Optional[Dict[str, Any]] = None
    default_values: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class MappingResponse(MappingBase):
    """Schema for mapping responses."""
    id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ETL Job Schemas
class ETLJobBase(BaseModel):
    """Base schema for ETL jobs."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_id: int = Field(..., gt=0)
    target_id: int = Field(..., gt=0)
    mapping_id: Optional[int] = Field(None, gt=0)

    # Extraction configuration
    extraction_query: Optional[str] = None
    extraction_config: Dict[str, Any] = Field(default_factory=dict)

    # Transformation configuration
    transformation_steps: List[Dict[str, Any]] = Field(default_factory=list)

    # Loading configuration
    load_strategy: LoadStrategy = LoadStrategy.APPEND
    batch_size: int = Field(1000, gt=0, le=100000)

    # Incremental load
    is_incremental: bool = False
    watermark_column: Optional[str] = None

    # Scheduling
    schedule_cron: Optional[str] = None
    is_scheduled: bool = False

    # Retry configuration
    max_retries: int = Field(3, ge=0, le=10)
    retry_delay_seconds: int = Field(300, ge=0)

    # Notifications
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notification_emails: List[str] = Field(default_factory=list)
    notification_slack_webhook: Optional[str] = None

    # Performance
    parallel_workers: int = Field(1, ge=1, le=100)
    timeout_seconds: int = Field(3600, gt=0)

    is_active: bool = True


class ETLJobCreate(ETLJobBase):
    """Schema for creating an ETL job."""
    pass


class ETLJobUpdate(BaseModel):
    """Schema for updating an ETL job."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    source_id: Optional[int] = Field(None, gt=0)
    target_id: Optional[int] = Field(None, gt=0)
    mapping_id: Optional[int] = Field(None, gt=0)
    extraction_query: Optional[str] = None
    extraction_config: Optional[Dict[str, Any]] = None
    transformation_steps: Optional[List[Dict[str, Any]]] = None
    load_strategy: Optional[LoadStrategy] = None
    batch_size: Optional[int] = Field(None, gt=0, le=100000)
    is_incremental: Optional[bool] = None
    watermark_column: Optional[str] = None
    schedule_cron: Optional[str] = None
    is_scheduled: Optional[bool] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=0)
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    notification_emails: Optional[List[str]] = None
    notification_slack_webhook: Optional[str] = None
    parallel_workers: Optional[int] = Field(None, ge=1, le=100)
    timeout_seconds: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class ETLJobResponse(ETLJobBase):
    """Schema for ETL job responses."""
    id: int
    last_watermark_value: Optional[str]
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    last_run_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Job Run Schemas
class JobRunBase(BaseModel):
    """Base schema for job runs."""
    job_id: int = Field(..., gt=0)
    status: JobStatus = JobStatus.PENDING
    triggered_by: Optional[str] = None
    triggered_by_user: Optional[int] = None


class JobRunCreate(JobRunBase):
    """Schema for creating a job run."""
    pass


class JobRunResponse(JobRunBase):
    """Schema for job run responses."""
    id: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    records_extracted: int = 0
    records_transformed: int = 0
    records_loaded: int = 0
    records_failed: int = 0
    error_message: Optional[str]
    error_traceback: Optional[str]
    error_count: int = 0
    retry_count: int = 0
    parent_run_id: Optional[int]
    data_quality_score: Optional[float]
    validation_errors: List[Dict[str, Any]] = Field(default_factory=list)
    watermark_value: Optional[str]
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    extraction_time_seconds: Optional[float]
    transformation_time_seconds: Optional[float]
    loading_time_seconds: Optional[float]
    log_file_path: Optional[str]
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Template Schemas
class ETLTemplateBase(BaseModel):
    """Base schema for ETL templates."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    template_config: Dict[str, Any] = Field(default_factory=dict)
    source_type: Optional[SourceType] = None
    target_type: Optional[SourceType] = None
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True


class ETLTemplateCreate(ETLTemplateBase):
    """Schema for creating an ETL template."""
    pass


class ETLTemplateUpdate(BaseModel):
    """Schema for updating an ETL template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    template_config: Optional[Dict[str, Any]] = None
    source_type: Optional[SourceType] = None
    target_type: Optional[SourceType] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ETLTemplateResponse(ETLTemplateBase):
    """Schema for ETL template responses."""
    id: int
    is_builtin: bool
    usage_count: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Data Quality Rule Schemas
class DataQualityRuleBase(BaseModel):
    """Base schema for data quality rules."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    rule_type: str = Field(..., min_length=1)
    field_name: Optional[str] = None
    rule_config: Dict[str, Any] = Field(default_factory=dict)
    severity: str = Field("warning", regex="^(info|warning|error|critical)$")
    fail_job_on_error: bool = False
    is_active: bool = True


class DataQualityRuleCreate(DataQualityRuleBase):
    """Schema for creating a data quality rule."""
    pass


class DataQualityRuleUpdate(BaseModel):
    """Schema for updating a data quality rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rule_type: Optional[str] = Field(None, min_length=1)
    field_name: Optional[str] = None
    rule_config: Optional[Dict[str, Any]] = None
    severity: Optional[str] = Field(None, regex="^(info|warning|error|critical)$")
    fail_job_on_error: Optional[bool] = None
    is_active: Optional[bool] = None


class DataQualityRuleResponse(DataQualityRuleBase):
    """Schema for data quality rule responses."""
    id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Audit Log Schemas
class AuditLogResponse(BaseModel):
    """Schema for audit log responses."""
    id: int
    job_run_id: int
    event_type: str
    event_timestamp: datetime
    event_data: Dict[str, Any] = Field(default_factory=dict)
    message: Optional[str]
    source_records: List[Dict[str, Any]] = Field(default_factory=list)
    target_records: List[Dict[str, Any]] = Field(default_factory=list)
    severity: str
    user_id: Optional[int]
    user_action: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Additional Schemas for API operations

class JobExecutionRequest(BaseModel):
    """Schema for manual job execution request."""
    job_id: int = Field(..., gt=0)
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    force_full_load: bool = False


class JobExecutionResponse(BaseModel):
    """Schema for job execution response."""
    job_run_id: int
    status: JobStatus
    message: str


class BulkOperationRequest(BaseModel):
    """Schema for bulk operations."""
    ids: List[int] = Field(..., min_items=1)
    action: str = Field(..., regex="^(activate|deactivate|delete)$")


class BulkOperationResponse(BaseModel):
    """Schema for bulk operation response."""
    success_count: int
    failed_count: int
    failed_ids: List[int] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class DataPreviewRequest(BaseModel):
    """Schema for data preview request."""
    source_id: int = Field(..., gt=0)
    query: Optional[str] = None
    limit: int = Field(10, ge=1, le=1000)


class DataPreviewResponse(BaseModel):
    """Schema for data preview response."""
    columns: List[str]
    data: List[Dict[str, Any]]
    total_count: Optional[int]


class ValidationResultResponse(BaseModel):
    """Schema for validation result response."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class MetricsResponse(BaseModel):
    """Schema for metrics response."""
    total_jobs: int
    active_jobs: int
    total_runs: int
    successful_runs: int
    failed_runs: int
    running_jobs: int
    avg_execution_time: Optional[float]
    total_records_processed: int
    data_quality_avg_score: Optional[float]


class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Schema for paginated responses."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class ExportRequest(BaseModel):
    """Schema for export request."""
    format: str = Field(..., regex="^(json|yaml|csv|excel)$")
    include_credentials: bool = False


class ImportRequest(BaseModel):
    """Schema for import request."""
    format: str = Field(..., regex="^(json|yaml)$")
    data: str  # JSON/YAML string
    overwrite_existing: bool = False
