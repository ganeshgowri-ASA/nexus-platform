"""Data source schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class DataSourceBase(BaseModel):
    """Base data source schema."""

    name: str = Field(..., description="Data source name")
    description: Optional[str] = Field(None, description="Description of the data source")
    source_type: str = Field(..., description="Type of data source (csv, json, sql, api, etc.)")
    connection_config: Dict[str, Any] = Field(..., description="Connection configuration")
    is_active: bool = Field(True, description="Whether the data source is active")


class DataSourceCreate(DataSourceBase):
    """Schema for creating a data source."""

    pass


class DataSourceUpdate(BaseModel):
    """Schema for updating a data source."""

    name: Optional[str] = None
    description: Optional[str] = None
    connection_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class DataSourceResponse(DataSourceBase):
    """Schema for data source response."""

    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True
