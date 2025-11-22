"""
Pydantic schemas for campaign-related API operations.

This module defines request and response schemas for campaign endpoints.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from config.constants import CampaignType, CampaignStatus


class CampaignBase(BaseModel):
    """Base campaign schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Campaign name")
    description: Optional[str] = Field(None, description="Campaign description")
    type: CampaignType = Field(default=CampaignType.EMAIL, description="Campaign type")


class CampaignCreate(CampaignBase):
    """Schema for creating a campaign."""
    subject: Optional[str] = Field(None, max_length=500, description="Email subject line")
    content: str = Field(..., description="Campaign content/body")
    from_name: Optional[str] = Field(None, max_length=255, description="Sender name")
    from_email: Optional[EmailStr] = Field(None, description="Sender email")
    reply_to: Optional[EmailStr] = Field(None, description="Reply-to email")
    segment_id: Optional[UUID] = Field(None, description="Target segment ID")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled send time")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate content is not empty."""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    subject: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    from_name: Optional[str] = Field(None, max_length=255)
    from_email: Optional[EmailStr] = None
    reply_to: Optional[EmailStr] = None
    segment_id: Optional[UUID] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[CampaignStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class CampaignMetrics(BaseModel):
    """Campaign metrics schema."""
    total_recipients: int = 0
    total_sent: int = 0
    total_delivered: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_bounced: int = 0
    total_unsubscribed: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    bounce_rate: float = 0.0
    unsubscribe_rate: float = 0.0


class CampaignResponse(CampaignBase):
    """Schema for campaign response."""
    id: UUID
    workspace_id: UUID
    status: CampaignStatus
    subject: Optional[str] = None
    from_name: Optional[str] = None
    from_email: Optional[str] = None
    segment_id: Optional[UUID] = None
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: UUID
    metrics: CampaignMetrics
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    """Schema for campaign list response."""
    campaigns: List[CampaignResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CampaignSendRequest(BaseModel):
    """Schema for sending a campaign."""
    send_immediately: bool = Field(default=True, description="Send immediately or schedule")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule for later")
    test_emails: Optional[List[EmailStr]] = Field(None, description="Test email addresses")


class EmailTemplateCreate(BaseModel):
    """Schema for creating email template."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    subject: Optional[str] = Field(None, max_length=500)
    html_content: str = Field(..., description="HTML content")
    text_content: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    is_public: bool = False


class EmailTemplateResponse(BaseModel):
    """Schema for email template response."""
    id: UUID
    workspace_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    subject: Optional[str] = None
    html_content: str
    text_content: Optional[str] = None
    category: Optional[str] = None
    is_public: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ABTestCreate(BaseModel):
    """Schema for creating A/B test."""
    campaign_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    variant_a: Dict[str, Any] = Field(..., description="Variant A configuration")
    variant_b: Dict[str, Any] = Field(..., description="Variant B configuration")
    split_percentage: float = Field(default=50.0, ge=0, le=100, description="Split percentage")


class ABTestResponse(BaseModel):
    """Schema for A/B test response."""
    id: UUID
    campaign_id: UUID
    name: str
    variant_a: Dict[str, Any]
    variant_b: Dict[str, Any]
    split_percentage: float
    winner: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignAnalyticsResponse(BaseModel):
    """Schema for campaign analytics response."""
    campaign_id: UUID
    date: datetime
    sent_count: int
    delivered_count: int
    opened_count: int
    clicked_count: int
    bounced_count: int
    open_rate: float
    click_rate: float
    bounce_rate: float
    conversion_count: int
    conversion_rate: float
    revenue: float

    class Config:
        from_attributes = True
