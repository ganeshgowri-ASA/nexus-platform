"""
User Models

Data models for user behavior analytics.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, EmailStr

from shared.utils import generate_uuid, get_utc_now


class UserBase(BaseModel):
    """Base user model."""

    email: Optional[EmailStr] = Field(None, description="User email")
    name: Optional[str] = Field(None, max_length=255, description="User name")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="User properties"
    )


class UserCreate(UserBase):
    """Model for creating a new user."""

    external_id: Optional[str] = Field(None, description="External user ID")


class UserUpdate(BaseModel):
    """Model for updating a user."""

    email: Optional[EmailStr] = None
    name: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class User(UserBase):
    """Complete user model with database fields."""

    id: str = Field(default_factory=generate_uuid, description="User ID")
    external_id: Optional[str] = Field(None, description="External user ID")
    first_seen_at: datetime = Field(
        default_factory=get_utc_now, description="First seen time"
    )
    last_seen_at: datetime = Field(
        default_factory=get_utc_now, description="Last seen time"
    )
    total_sessions: int = Field(default=0, description="Total sessions")
    total_events: int = Field(default=0, description="Total events")
    total_conversions: int = Field(default=0, description="Total conversions")
    lifetime_value: float = Field(default=0.0, description="Lifetime value")
    created_at: datetime = Field(
        default_factory=get_utc_now, description="Creation time"
    )
    updated_at: datetime = Field(
        default_factory=get_utc_now, description="Update time"
    )

    model_config = {"from_attributes": True}


class UserBehavior(BaseModel):
    """User behavior analytics."""

    user_id: str
    total_sessions: int
    avg_session_duration: float
    total_page_views: int
    total_events: int
    bounce_rate: float
    conversion_rate: float
    favorite_modules: list[str]
    last_active: datetime
    engagement_score: float


class UserQuery(BaseModel):
    """Model for querying users."""

    email: Optional[str] = None
    external_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=1000)
