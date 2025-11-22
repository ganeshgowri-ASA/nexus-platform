"""Sync configuration schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class SyncConfigCreate(BaseModel):
    """Schema for creating sync configuration."""

    integration_id: str
    connection_id: str
    name: str
    sync_direction: str
    source_config: Dict[str, Any]
    destination_config: Dict[str, Any]
    field_mapping: Optional[Dict[str, str]] = None
    transformation_rules: Optional[Dict[str, Any]] = None
    schedule_type: str
    schedule_expression: str
    batch_size: int = 100


class SyncConfigResponse(BaseModel):
    """Schema for sync configuration response."""

    id: str
    integration_id: str
    connection_id: str
    name: str
    sync_direction: str
    schedule_type: str
    schedule_expression: str
    is_active: bool
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SyncExecutionResponse(BaseModel):
    """Schema for sync execution response."""

    id: str
    sync_config_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    records_read: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_deleted: int = 0
    records_failed: int = 0
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
