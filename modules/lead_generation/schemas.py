"""
Pydantic schemas for lead generation module.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

from modules.lead_generation.models import FormType, LeadStatus, LeadSource


# Form Schemas
class FormFieldSchema(BaseModel):
    """Form field schema."""
    name: str
    label: str
    type: str
    required: bool = False
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None
    validation: Optional[Dict[str, Any]] = None


class FormCreate(BaseModel):
    """Schema for creating a form."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    form_type: FormType = FormType.INLINE
    fields: List[Dict[str, Any]] = Field(..., min_items=1)
    settings: Dict[str, Any] = {}
    design: Dict[str, Any] = {}
    progressive_profiling_enabled: bool = False
    progressive_fields: List[str] = []
    thank_you_message: Optional[str] = None
    redirect_url: Optional[str] = None
    email_notifications: List[str] = []


class FormUpdate(BaseModel):
    """Schema for updating a form."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    form_type: Optional[FormType] = None
    fields: Optional[List[Dict[str, Any]]] = None
    settings: Optional[Dict[str, Any]] = None
    design: Optional[Dict[str, Any]] = None
    progressive_profiling_enabled: Optional[bool] = None
    progressive_fields: Optional[List[str]] = None
    thank_you_message: Optional[str] = None
    redirect_url: Optional[str] = None
    email_notifications: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_published: Optional[bool] = None


class FormResponse(BaseModel):
    """Schema for form response."""
    id: UUID
    name: str
    description: Optional[str]
    form_type: FormType
    fields: List[Dict[str, Any]]
    settings: Dict[str, Any]
    design: Dict[str, Any]
    progressive_profiling_enabled: bool
    is_active: bool
    is_published: bool
    views: int
    submissions: int
    conversion_rate: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Landing Page Schemas
class LandingPageCreate(BaseModel):
    """Schema for creating a landing page."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    sections: List[Dict[str, Any]] = []
    form_id: Optional[UUID] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: List[str] = []
    template: Optional[str] = None
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None


class LandingPageUpdate(BaseModel):
    """Schema for updating a landing page."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    title: Optional[str] = None
    description: Optional[str] = None
    sections: Optional[List[Dict[str, Any]]] = None
    form_id: Optional[UUID] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[List[str]] = None
    template: Optional[str] = None
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None
    is_active: Optional[bool] = None
    is_published: Optional[bool] = None


class LandingPageResponse(BaseModel):
    """Schema for landing page response."""
    id: UUID
    name: str
    slug: str
    title: str
    description: Optional[str]
    sections: List[Dict[str, Any]]
    form_id: Optional[UUID]
    is_active: bool
    is_published: bool
    views: int
    unique_visitors: int
    bounce_rate: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Lead Schemas
class LeadCreate(BaseModel):
    """Schema for creating a lead."""
    email: EmailStr
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    custom_fields: Dict[str, Any] = {}
    source: LeadSource
    form_id: Optional[UUID] = None
    landing_page_url: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    referrer: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class LeadUpdate(BaseModel):
    """Schema for updating a lead."""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    status: Optional[LeadStatus] = None
    is_qualified: Optional[bool] = None
    assigned_to: Optional[str] = None
    score: Optional[int] = None
    grade: Optional[str] = None


class LeadResponse(BaseModel):
    """Schema for lead response."""
    id: UUID
    email: str
    phone: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    company: Optional[str]
    job_title: Optional[str]
    custom_fields: Dict[str, Any]
    source: LeadSource
    status: LeadStatus
    score: int
    grade: Optional[str]
    is_qualified: bool
    email_validated: bool
    phone_validated: bool
    enrichment_status: Optional[str]
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_activity_at: Optional[datetime]

    class Config:
        from_attributes = True


class LeadEnrichRequest(BaseModel):
    """Schema for lead enrichment request."""
    lead_id: UUID
    provider: Optional[str] = "clearbit"


class LeadScoreRequest(BaseModel):
    """Schema for lead scoring request."""
    lead_id: UUID


# Lead Activity Schemas
class LeadActivityCreate(BaseModel):
    """Schema for creating a lead activity."""
    lead_id: UUID
    activity_type: str
    title: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = {}


class LeadActivityResponse(BaseModel):
    """Schema for lead activity response."""
    id: UUID
    lead_id: UUID
    activity_type: str
    title: str
    description: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# Chatbot Schemas
class ChatbotMessageCreate(BaseModel):
    """Schema for creating a chatbot message."""
    conversation_id: Optional[UUID] = None
    message: str
    sender: str = "user"  # user or bot


class ChatbotConversationResponse(BaseModel):
    """Schema for chatbot conversation response."""
    id: UUID
    lead_id: Optional[UUID]
    messages: List[Dict[str, Any]]
    context: Dict[str, Any]
    is_active: bool
    is_completed: bool
    lead_captured: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Lead Magnet Schemas
class LeadMagnetCreate(BaseModel):
    """Schema for creating a lead magnet."""
    name: str = Field(..., min_length=1, max_length=255)
    type: str
    description: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    delivery_method: str = "email"
    email_template: Optional[str] = None


class LeadMagnetResponse(BaseModel):
    """Schema for lead magnet response."""
    id: UUID
    name: str
    type: str
    description: Optional[str]
    file_url: Optional[str]
    delivery_method: str
    downloads: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Lead Scoring Rule Schemas
class LeadScoringRuleCreate(BaseModel):
    """Schema for creating a lead scoring rule."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    conditions: Dict[str, Any]
    score_adjustment: int
    priority: int = 0


class LeadScoringRuleResponse(BaseModel):
    """Schema for lead scoring rule response."""
    id: UUID
    name: str
    description: Optional[str]
    conditions: Dict[str, Any]
    score_adjustment: int
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
