"""Webhook schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class WebhookCreate(BaseModel):
    """Schema for creating a webhook."""

    integration_id: str
    name: str
    url: str
    secret: Optional[str] = None
    events: List[str]
    payload_template: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    max_retries: int = 3
    retry_delay_seconds: int = 60


class WebhookResponse(BaseModel):
    """Schema for webhook response."""

    id: str
    integration_id: str
    name: str
    url: str
    events: List[str]
    is_active: bool
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    failure_count: int = 0
    created_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True
