"""
Type definitions for lead generation module.

This module contains Pydantic models for leads, sources, activities,
and related entities in the lead generation system.
"""

from typing import Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict

from shared.types import TimestampMixin


class LeadStatus(str, Enum):
    """Lead status enumeration."""

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    NURTURING = "nurturing"
    CONVERTED = "converted"
    LOST = "lost"


class LeadSourceType(str, Enum):
    """Lead source type enumeration."""

    ORGANIC = "organic"
    PAID = "paid"
    REFERRAL = "referral"
    SOCIAL = "social"
    EMAIL = "email"
    DIRECT = "direct"
    OTHER = "other"


class LeadActivityType(str, Enum):
    """Lead activity type enumeration."""

    FORM_SUBMISSION = "form_submission"
    PAGE_VIEW = "page_view"
    EMAIL_OPENED = "email_opened"
    EMAIL_CLICKED = "email_clicked"
    DOWNLOAD = "download"
    CALL = "call"
    MEETING = "meeting"
    NOTE = "note"
    STATUS_CHANGE = "status_change"


class LeadScoreType(str, Enum):
    """Lead scoring type enumeration."""

    BEHAVIOR = "behavior"
    DEMOGRAPHIC = "demographic"
    FIRMOGRAPHIC = "firmographic"
    PREDICTIVE = "predictive"
    CUSTOM = "custom"


class QualificationCriteria(str, Enum):
    """Lead qualification criteria enumeration."""

    BANT = "bant"  # Budget, Authority, Need, Timeline
    CHAMP = "champ"  # Challenges, Authority, Money, Prioritization
    MEDDIC = "meddic"  # Metrics, Economic Buyer, Decision Criteria, Decision Process, Identify Pain, Champion
    CUSTOM = "custom"


# Base Models


class LeadBase(BaseModel):
    """Base model for lead data."""

    email: EmailStr = Field(description="Lead email address")
    first_name: Optional[str] = Field(default=None, description="First name")
    last_name: Optional[str] = Field(default=None, description="Last name")
    phone: Optional[str] = Field(default=None, description="Phone number")
    company: Optional[str] = Field(default=None, description="Company name")
    job_title: Optional[str] = Field(default=None, description="Job title")
    website: Optional[str] = Field(default=None, description="Company website")
    industry: Optional[str] = Field(default=None, description="Industry")
    company_size: Optional[str] = Field(default=None, description="Company size")
    country: Optional[str] = Field(default=None, description="Country")
    state: Optional[str] = Field(default=None, description="State/Province")
    city: Optional[str] = Field(default=None, description="City")
    status: LeadStatus = Field(default=LeadStatus.NEW, description="Lead status")
    custom_fields: Optional[dict[str, Any]] = Field(
        default=None,
        description="Custom field values",
    )

    model_config = ConfigDict(from_attributes=True)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v:
            from shared.utils import validate_phone
            if not validate_phone(v):
                raise ValueError("Invalid phone number format")
        return v


class LeadCreate(LeadBase):
    """Model for creating a new lead."""

    source_id: Optional[str] = Field(default=None, description="Lead source ID")
    campaign_id: Optional[str] = Field(default=None, description="Campaign ID")
    utm_source: Optional[str] = Field(default=None, description="UTM source")
    utm_medium: Optional[str] = Field(default=None, description="UTM medium")
    utm_campaign: Optional[str] = Field(default=None, description="UTM campaign")
    utm_content: Optional[str] = Field(default=None, description="UTM content")


class LeadUpdate(BaseModel):
    """Model for updating a lead."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    status: Optional[LeadStatus] = None
    custom_fields: Optional[dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class Lead(LeadBase, TimestampMixin):
    """Complete lead model."""

    id: str = Field(description="Lead ID")
    score: int = Field(default=0, description="Lead score")
    source_id: Optional[str] = Field(default=None, description="Lead source ID")
    assigned_to: Optional[str] = Field(default=None, description="Assigned user ID")
    last_activity_at: Optional[datetime] = Field(
        default=None,
        description="Last activity timestamp",
    )
    converted_at: Optional[datetime] = Field(
        default=None,
        description="Conversion timestamp",
    )
    enriched_at: Optional[datetime] = Field(
        default=None,
        description="Enrichment timestamp",
    )
    is_duplicate: bool = Field(default=False, description="Duplicate flag")
    tags: list[str] = Field(default_factory=list, description="Lead tags")

    model_config = ConfigDict(from_attributes=True)


# Lead Source Models


class LeadSourceBase(BaseModel):
    """Base model for lead source."""

    name: str = Field(description="Source name")
    type: LeadSourceType = Field(description="Source type")
    description: Optional[str] = Field(default=None, description="Source description")
    is_active: bool = Field(default=True, description="Active status")

    model_config = ConfigDict(from_attributes=True)


class LeadSourceCreate(LeadSourceBase):
    """Model for creating a lead source."""

    pass


class LeadSource(LeadSourceBase, TimestampMixin):
    """Complete lead source model."""

    id: str = Field(description="Source ID")
    leads_count: int = Field(default=0, description="Total leads from this source")
    conversion_rate: float = Field(
        default=0.0,
        description="Conversion rate",
    )

    model_config = ConfigDict(from_attributes=True)


# Lead Activity Models


class LeadActivityBase(BaseModel):
    """Base model for lead activity."""

    lead_id: str = Field(description="Lead ID")
    type: LeadActivityType = Field(description="Activity type")
    description: Optional[str] = Field(default=None, description="Activity description")
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Activity metadata",
    )

    model_config = ConfigDict(from_attributes=True)


class LeadActivityCreate(LeadActivityBase):
    """Model for creating a lead activity."""

    pass


class LeadActivity(LeadActivityBase, TimestampMixin):
    """Complete lead activity model."""

    id: str = Field(description="Activity ID")

    model_config = ConfigDict(from_attributes=True)


# Lead Score Models


class LeadScoreBase(BaseModel):
    """Base model for lead score."""

    lead_id: str = Field(description="Lead ID")
    type: LeadScoreType = Field(description="Score type")
    value: int = Field(description="Score value")
    reason: Optional[str] = Field(default=None, description="Scoring reason")

    model_config = ConfigDict(from_attributes=True)


class LeadScoreCreate(LeadScoreBase):
    """Model for creating a lead score."""

    pass


class LeadScore(LeadScoreBase, TimestampMixin):
    """Complete lead score model."""

    id: str = Field(description="Score ID")

    model_config = ConfigDict(from_attributes=True)


# Touchpoint Models


class TouchpointBase(BaseModel):
    """Base model for touchpoint."""

    lead_id: str = Field(description="Lead ID")
    channel: str = Field(description="Touchpoint channel")
    campaign_id: Optional[str] = Field(default=None, description="Campaign ID")
    content: Optional[str] = Field(default=None, description="Touchpoint content")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Touchpoint timestamp",
    )

    model_config = ConfigDict(from_attributes=True)


class TouchpointCreate(TouchpointBase):
    """Model for creating a touchpoint."""

    pass


class Touchpoint(TouchpointBase, TimestampMixin):
    """Complete touchpoint model."""

    id: str = Field(description="Touchpoint ID")

    model_config = ConfigDict(from_attributes=True)


# Conversion Models


class ConversionBase(BaseModel):
    """Base model for conversion."""

    lead_id: str = Field(description="Lead ID")
    type: str = Field(description="Conversion type")
    value: Optional[float] = Field(default=None, description="Conversion value")
    currency: str = Field(default="USD", description="Currency code")
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Conversion metadata",
    )

    model_config = ConfigDict(from_attributes=True)


class ConversionCreate(ConversionBase):
    """Model for creating a conversion."""

    pass


class Conversion(ConversionBase, TimestampMixin):
    """Complete conversion model."""

    id: str = Field(description="Conversion ID")

    model_config = ConfigDict(from_attributes=True)


# Form Models


class FormField(BaseModel):
    """Form field definition."""

    name: str = Field(description="Field name")
    type: str = Field(description="Field type (text, email, phone, etc.)")
    label: str = Field(description="Field label")
    placeholder: Optional[str] = Field(default=None, description="Placeholder text")
    required: bool = Field(default=False, description="Required flag")
    validation: Optional[dict[str, Any]] = Field(
        default=None,
        description="Validation rules",
    )
    options: Optional[list[str]] = Field(
        default=None,
        description="Options for select fields",
    )

    model_config = ConfigDict(from_attributes=True)


class FormBase(BaseModel):
    """Base model for form."""

    name: str = Field(description="Form name")
    title: str = Field(description="Form title")
    description: Optional[str] = Field(default=None, description="Form description")
    fields: list[FormField] = Field(description="Form fields")
    submit_button_text: str = Field(default="Submit", description="Submit button text")
    success_message: str = Field(
        default="Thank you for your submission!",
        description="Success message",
    )
    is_active: bool = Field(default=True, description="Active status")

    model_config = ConfigDict(from_attributes=True)


class FormCreate(FormBase):
    """Model for creating a form."""

    pass


class Form(FormBase, TimestampMixin):
    """Complete form model."""

    id: str = Field(description="Form ID")
    submissions_count: int = Field(default=0, description="Total submissions")
    conversion_rate: float = Field(default=0.0, description="Conversion rate")
    embed_code: Optional[str] = Field(default=None, description="Embed code")

    model_config = ConfigDict(from_attributes=True)


# Landing Page Models


class LandingPageBase(BaseModel):
    """Base model for landing page."""

    name: str = Field(description="Page name")
    title: str = Field(description="Page title")
    slug: str = Field(description="URL slug")
    template: str = Field(description="Template name")
    content: dict[str, Any] = Field(description="Page content")
    form_id: Optional[str] = Field(default=None, description="Associated form ID")
    is_active: bool = Field(default=True, description="Active status")

    model_config = ConfigDict(from_attributes=True)


class LandingPageCreate(LandingPageBase):
    """Model for creating a landing page."""

    pass


class LandingPage(LandingPageBase, TimestampMixin):
    """Complete landing page model."""

    id: str = Field(description="Page ID")
    views: int = Field(default=0, description="Total views")
    submissions: int = Field(default=0, description="Total submissions")
    conversion_rate: float = Field(default=0.0, description="Conversion rate")
    url: Optional[str] = Field(default=None, description="Full URL")

    model_config = ConfigDict(from_attributes=True)


# Popup Models


class PopupBase(BaseModel):
    """Base model for popup."""

    name: str = Field(description="Popup name")
    title: str = Field(description="Popup title")
    content: str = Field(description="Popup content")
    form_id: Optional[str] = Field(default=None, description="Associated form ID")
    trigger_type: str = Field(
        description="Trigger type (exit_intent, scroll, time, click)"
    )
    trigger_value: Optional[str] = Field(
        default=None,
        description="Trigger value (e.g., 50% for scroll, 10s for time)",
    )
    is_active: bool = Field(default=True, description="Active status")

    model_config = ConfigDict(from_attributes=True)


class PopupCreate(PopupBase):
    """Model for creating a popup."""

    pass


class Popup(PopupBase, TimestampMixin):
    """Complete popup model."""

    id: str = Field(description="Popup ID")
    views: int = Field(default=0, description="Total views")
    submissions: int = Field(default=0, description="Total submissions")
    conversion_rate: float = Field(default=0.0, description="Conversion rate")

    model_config = ConfigDict(from_attributes=True)
