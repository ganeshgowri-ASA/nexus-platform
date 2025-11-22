"""API Key schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""

    integration_id: str
    name: str
    description: Optional[str] = None
    api_key: str  # Will be encrypted before storage
    additional_fields: Optional[dict] = None
    rate_limit_per_minute: Optional[str] = None
    rate_limit_per_hour: Optional[str] = None


class APIKeyResponse(BaseModel):
    """Schema for API key response."""

    id: str
    integration_id: str
    name: str
    description: Optional[str] = None
    is_active: bool
    last_used: Optional[datetime] = None
    rate_limit_per_minute: Optional[str] = None
    rate_limit_per_hour: Optional[str] = None
    created_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True
