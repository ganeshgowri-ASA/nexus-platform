"""Pipeline schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class PipelineBase(BaseModel):
    """Base pipeline schema."""

    name: str = Field(..., description="Pipeline name")
    description: Optional[str] = Field(None, description="Pipeline description")
    source_id: str = Field(..., description="Data source ID")
    extract_config: Dict[str, Any] = Field(..., description="Extract configuration")
    transform_config: Dict[str, Any] = Field(..., description="Transform configuration")
    load_config: Dict[str, Any] = Field(..., description="Load configuration")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")
    deduplication_config: Optional[Dict[str, Any]] = Field(None, description="Deduplication config")
    is_active: bool = Field(True, description="Whether the pipeline is active")
    schedule: Optional[str] = Field(None, description="Cron expression for scheduling")
    parallel_processing: bool = Field(False, description="Enable parallel processing")
    batch_size: int = Field(1000, description="Batch size for processing")


class PipelineCreate(PipelineBase):
    """Schema for creating a pipeline."""

    pass


class PipelineUpdate(BaseModel):
    """Schema for updating a pipeline."""

    name: Optional[str] = None
    description: Optional[str] = None
    extract_config: Optional[Dict[str, Any]] = None
    transform_config: Optional[Dict[str, Any]] = None
    load_config: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    deduplication_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    schedule: Optional[str] = None
    parallel_processing: Optional[bool] = None
    batch_size: Optional[int] = None


class PipelineResponse(PipelineBase):
    """Schema for pipeline response."""

    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    last_run: Optional[datetime] = None

    class Config:
        from_attributes = True
