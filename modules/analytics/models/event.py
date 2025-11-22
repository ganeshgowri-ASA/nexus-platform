"""
Event Models

Data models for analytics event tracking.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from shared.constants import EventType
from shared.utils import generate_uuid, get_utc_now


class EventBase(BaseModel):
    """Base event model with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Event name")
    event_type: EventType = Field(..., description="Event type category")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Event properties"
    )
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    module: Optional[str] = Field(None, max_length=100, description="Module name")
    page_url: Optional[str] = Field(None, max_length=2048, description="Page URL")
    page_title: Optional[str] = Field(None, max_length=255, description="Page title")
    referrer: Optional[str] = Field(None, max_length=2048, description="Referrer URL")
    user_agent: Optional[str] = Field(None, max_length=512, description="User agent")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")
    country: Optional[str] = Field(None, max_length=2, description="Country code")
    city: Optional[str] = Field(None, max_length=100, description="City name")
    device_type: Optional[str] = Field(None, max_length=50, description="Device type")
    browser: Optional[str] = Field(None, max_length=50, description="Browser name")
    os: Optional[str] = Field(None, max_length=50, description="Operating system")

    @field_validator("properties")
    @classmethod
    def validate_properties(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate event properties don't exceed limits."""
        if len(v) > 100:
            raise ValueError("Event properties cannot exceed 100 keys")
        return v


class EventCreate(EventBase):
    """Model for creating a new event."""

    pass


class EventUpdate(BaseModel):
    """Model for updating an event."""

    properties: Optional[Dict[str, Any]] = None


class Event(EventBase):
    """Complete event model with database fields."""

    id: str = Field(default_factory=generate_uuid, description="Event ID")
    timestamp: datetime = Field(
        default_factory=get_utc_now, description="Event timestamp"
    )
    created_at: datetime = Field(
        default_factory=get_utc_now, description="Record creation time"
    )
    processed: bool = Field(default=False, description="Processing status")
    processed_at: Optional[datetime] = Field(None, description="Processing time")

    model_config = {"from_attributes": True}


class EventBatch(BaseModel):
    """Model for batch event processing."""

    events: list[EventCreate] = Field(..., min_length=1, max_length=1000)
    batch_id: str = Field(default_factory=generate_uuid)
    timestamp: datetime = Field(default_factory=get_utc_now)


class EventQuery(BaseModel):
    """Model for querying events."""

    event_types: Optional[list[EventType]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    module: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=1000)


class EventAggregation(BaseModel):
    """Model for event aggregation results."""

    event_type: EventType
    count: int
    unique_users: int
    unique_sessions: int
    start_date: datetime
    end_date: datetime
    properties: Dict[str, Any] = Field(default_factory=dict)
