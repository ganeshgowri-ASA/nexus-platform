"""Pydantic schemas for webhooks"""

from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class DeliveryStatusEnum(str, Enum):
    """Delivery status enumeration"""
    PENDING = "pending"
    SENDING = "sending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


# Webhook Schemas
class WebhookBase(BaseModel):
    """Base webhook schema"""
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., description="Webhook endpoint URL")
    description: Optional[str] = None
    headers: Optional[Dict[str, str]] = Field(default_factory=dict)
    timeout: int = Field(default=30, ge=1, le=300)
    is_active: bool = True


class WebhookCreate(WebhookBase):
    """Schema for creating a webhook"""
    event_types: List[str] = Field(..., min_items=1, description="List of event types to subscribe to")
    created_by: Optional[str] = None


class WebhookUpdate(BaseModel):
    """Schema for updating a webhook"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = None
    description: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    timeout: Optional[int] = Field(None, ge=1, le=300)
    is_active: Optional[bool] = None


class WebhookEventSchema(BaseModel):
    """Webhook event schema"""
    id: int
    webhook_id: int
    event_type: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookResponse(WebhookBase):
    """Schema for webhook response"""
    id: int
    secret: str
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    events: List[WebhookEventSchema] = []

    class Config:
        from_attributes = True


# Webhook Event Schemas
class EventSubscriptionCreate(BaseModel):
    """Schema for creating event subscription"""
    event_type: str = Field(..., min_length=1)


class EventSubscriptionUpdate(BaseModel):
    """Schema for updating event subscription"""
    is_active: bool


# Webhook Delivery Schemas
class WebhookDeliveryBase(BaseModel):
    """Base delivery schema"""
    event_type: str
    event_id: Optional[str] = None
    payload: Dict[str, Any]


class WebhookDeliveryCreate(WebhookDeliveryBase):
    """Schema for creating a delivery"""
    webhook_id: int


class WebhookDeliveryResponse(BaseModel):
    """Schema for delivery response"""
    id: int
    webhook_id: int
    event_type: str
    event_id: Optional[str]
    status: DeliveryStatusEnum
    attempt_count: int
    max_attempts: int
    status_code: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]
    next_retry_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class WebhookDeliveryDetailResponse(WebhookDeliveryResponse):
    """Detailed delivery response with payload and responses"""
    payload: Dict[str, Any]
    response_body: Optional[str]
    response_headers: Optional[Dict[str, Any]]
    request_headers: Optional[Dict[str, Any]]
    request_url: Optional[str]

    class Config:
        from_attributes = True


# Event Trigger Schema
class EventTrigger(BaseModel):
    """Schema for triggering an event"""
    event_type: str = Field(..., description="Type of event (e.g., 'user.created', 'order.completed')")
    event_id: Optional[str] = Field(None, description="Optional unique event identifier")
    payload: Dict[str, Any] = Field(..., description="Event payload data")


# Statistics Schema
class WebhookStats(BaseModel):
    """Webhook statistics schema"""
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    pending_deliveries: int
    success_rate: float
    average_response_time: Optional[float]
