"""
Pydantic schemas for contact-related API operations.

This module defines request and response schemas for contact endpoints.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from config.constants import ContactStatus


class ContactBase(BaseModel):
    """Base contact schema."""
    email: EmailStr = Field(..., description="Contact email address")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    company: Optional[str] = Field(None, max_length=255, description="Company name")
    job_title: Optional[str] = Field(None, max_length=255, description="Job title")


class ContactCreate(ContactBase):
    """Schema for creating a contact."""
    custom_attributes: Optional[Dict[str, Any]] = Field(default={}, description="Custom attributes")
    tags: Optional[List[str]] = Field(default=[], description="Tag names")
    list_ids: Optional[List[UUID]] = Field(default=[], description="List IDs to add contact to")


class ContactUpdate(BaseModel):
    """Schema for updating a contact."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    company: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    status: Optional[ContactStatus] = None
    custom_attributes: Optional[Dict[str, Any]] = None
    lead_score: Optional[int] = Field(None, ge=0, le=1000)


class ContactResponse(ContactBase):
    """Schema for contact response."""
    id: UUID
    workspace_id: UUID
    status: ContactStatus
    lead_score: int
    custom_attributes: Dict[str, Any]
    subscribed_at: Optional[datetime] = None
    unsubscribed_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    tags: Optional[List[str]] = []

    class Config:
        from_attributes = True


class ContactListResponse(BaseModel):
    """Schema for contact list response."""
    contacts: List[ContactResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ContactBulkImport(BaseModel):
    """Schema for bulk contact import."""
    contacts: List[ContactCreate] = Field(..., description="List of contacts to import")
    list_id: Optional[UUID] = Field(None, description="List to add contacts to")
    skip_duplicates: bool = Field(default=True, description="Skip duplicate emails")
    update_existing: bool = Field(default=False, description="Update existing contacts")


class ContactBulkImportResponse(BaseModel):
    """Schema for bulk import response."""
    total_imported: int
    total_updated: int
    total_skipped: int
    errors: List[Dict[str, str]] = []


class ContactListCreate(BaseModel):
    """Schema for creating contact list."""
    name: str = Field(..., min_length=1, max_length=255, description="List name")
    description: Optional[str] = Field(None, description="List description")
    is_dynamic: bool = Field(default=False, description="Dynamic list flag")
    criteria: Optional[Dict[str, Any]] = Field(None, description="Dynamic list criteria")


class ContactListUpdateSchema(BaseModel):
    """Schema for updating contact list."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = None


class ContactListResponseSchema(BaseModel):
    """Schema for contact list response."""
    id: UUID
    workspace_id: UUID
    name: str
    description: Optional[str] = None
    is_dynamic: bool
    criteria: Optional[Dict[str, Any]] = None
    contact_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TagCreate(BaseModel):
    """Schema for creating tag."""
    name: str = Field(..., min_length=1, max_length=100, description="Tag name")
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code")


class TagResponse(BaseModel):
    """Schema for tag response."""
    id: UUID
    workspace_id: UUID
    name: str
    color: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SegmentCreate(BaseModel):
    """Schema for creating segment."""
    name: str = Field(..., min_length=1, max_length=255, description="Segment name")
    description: Optional[str] = Field(None, description="Segment description")
    conditions: Dict[str, Any] = Field(..., description="Segment conditions")
    is_dynamic: bool = Field(default=True, description="Dynamic segment flag")


class SegmentUpdate(BaseModel):
    """Schema for updating segment."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None


class SegmentResponse(BaseModel):
    """Schema for segment response."""
    id: UUID
    workspace_id: UUID
    name: str
    description: Optional[str] = None
    conditions: Dict[str, Any]
    is_dynamic: bool
    contact_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContactEventCreate(BaseModel):
    """Schema for creating contact event."""
    event_type: str = Field(..., min_length=1, max_length=100, description="Event type")
    event_data: Optional[Dict[str, Any]] = Field(default={}, description="Event data")
    occurred_at: Optional[datetime] = Field(None, description="Event occurrence time")


class ContactEventResponse(BaseModel):
    """Schema for contact event response."""
    id: UUID
    contact_id: UUID
    event_type: str
    event_data: Dict[str, Any]
    occurred_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ContactScoreUpdate(BaseModel):
    """Schema for updating contact lead score."""
    score_delta: int = Field(..., description="Score change (positive or negative)")
    reason: str = Field(..., description="Reason for score change")
