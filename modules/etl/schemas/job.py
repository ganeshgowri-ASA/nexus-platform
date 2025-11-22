"""ETL Job schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ETLJobBase(BaseModel):
    """Base ETL job schema."""

    pipeline_id: str = Field(..., description="Pipeline ID")
    schedule_type: str = Field(..., description="Schedule type (cron, interval, once)")
    schedule_expression: str = Field(..., description="Schedule expression")
    timezone: str = Field("UTC", description="Timezone for scheduling")
    is_active: bool = Field(True, description="Whether the job is active")


class ETLJobCreate(ETLJobBase):
    """Schema for creating an ETL job."""

    pass


class ETLJobUpdate(BaseModel):
    """Schema for updating an ETL job."""

    schedule_type: Optional[str] = None
    schedule_expression: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None


class ETLJobResponse(ETLJobBase):
    """Schema for ETL job response."""

    id: str
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True
