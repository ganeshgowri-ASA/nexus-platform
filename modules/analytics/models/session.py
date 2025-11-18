"""
Session Models

Data models for user session tracking.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from shared.utils import generate_uuid, get_utc_now


class SessionBase(BaseModel):
    """Base session model."""

    user_id: str = Field(..., description="User identifier")
    started_at: datetime = Field(
        default_factory=get_utc_now, description="Session start time"
    )
    last_activity_at: datetime = Field(
        default_factory=get_utc_now, description="Last activity time"
    )
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")
    user_agent: Optional[str] = Field(None, max_length=512, description="User agent")
    country: Optional[str] = Field(None, max_length=2, description="Country code")
    city: Optional[str] = Field(None, max_length=100, description="City")
    device_type: Optional[str] = Field(None, max_length=50, description="Device type")
    browser: Optional[str] = Field(None, max_length=50, description="Browser")
    os: Optional[str] = Field(None, max_length=50, description="Operating system")
    referrer: Optional[str] = Field(None, max_length=2048, description="Referrer URL")
    landing_page: Optional[str] = Field(None, max_length=2048, description="Landing page")
    utm_source: Optional[str] = Field(None, max_length=255, description="UTM source")
    utm_medium: Optional[str] = Field(None, max_length=255, description="UTM medium")
    utm_campaign: Optional[str] = Field(None, max_length=255, description="UTM campaign")


class SessionCreate(SessionBase):
    """Model for creating a new session."""

    pass


class SessionUpdate(BaseModel):
    """Model for updating a session."""

    last_activity_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class Session(SessionBase):
    """Complete session model with database fields."""

    id: str = Field(default_factory=generate_uuid, description="Session ID")
    ended_at: Optional[datetime] = Field(None, description="Session end time")
    duration_seconds: Optional[int] = Field(None, description="Session duration")
    page_views: int = Field(default=0, description="Number of page views")
    events_count: int = Field(default=0, description="Number of events")
    is_bounce: bool = Field(default=False, description="Bounce flag")
    converted: bool = Field(default=False, description="Conversion flag")
    conversion_value: Optional[float] = Field(None, description="Conversion value")
    created_at: datetime = Field(
        default_factory=get_utc_now, description="Creation time"
    )

    model_config = {"from_attributes": True}


class SessionAnalytics(BaseModel):
    """Session analytics aggregation."""

    total_sessions: int
    unique_users: int
    avg_duration_seconds: float
    avg_page_views: float
    bounce_rate: float
    conversion_rate: float
    total_conversions: int
    total_conversion_value: float


class SessionQuery(BaseModel):
    """Model for querying sessions."""

    user_id: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    country: Optional[str] = None
    converted: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=1000)
