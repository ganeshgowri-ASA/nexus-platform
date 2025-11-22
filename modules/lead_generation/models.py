"""
Database models for lead generation module.
<<<<<<< HEAD

This module contains SQLAlchemy ORM models for leads, sources, activities,
and related entities.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship

from config.database import Base
from shared.utils import generate_uuid


class Lead(Base):
    """Lead database model."""

    __tablename__ = "leads"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), nullable=False, index=True, unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))
    company = Column(String(255), index=True)
    job_title = Column(String(255))
    website = Column(String(255))
    industry = Column(String(100))
    company_size = Column(String(50))
    country = Column(String(100))
    state = Column(String(100))
    city = Column(String(100))
    status = Column(String(50), default="new", index=True)
    score = Column(Integer, default=0, index=True)
    source_id = Column(String(36), ForeignKey("lead_sources.id"))
    assigned_to = Column(String(36))
    last_activity_at = Column(DateTime)
    converted_at = Column(DateTime)
    enriched_at = Column(DateTime)
    is_duplicate = Column(Boolean, default=False)
    tags = Column(JSON)
    custom_fields = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source = relationship("LeadSource", back_populates="leads")
    activities = relationship("LeadActivity", back_populates="lead", cascade="all, delete-orphan")
    scores = relationship("LeadScoreRecord", back_populates="lead", cascade="all, delete-orphan")
    touchpoints = relationship("TouchpointRecord", back_populates="lead", cascade="all, delete-orphan")
    conversions = relationship("ConversionRecord", back_populates="lead", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_lead_email_status", "email", "status"),
        Index("idx_lead_score_status", "score", "status"),
        Index("idx_lead_created_at", "created_at"),
    )


class LeadSource(Base):
    """Lead source database model."""

    __tablename__ = "lead_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(50), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    leads_count = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    leads = relationship("Lead", back_populates="source")


class LeadActivity(Base):
    """Lead activity database model."""

    __tablename__ = "lead_activities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
=======
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from database import Base


class FormType(str, enum.Enum):
    """Form types."""
    INLINE = "inline"
    POPUP = "popup"
    SLIDE_IN = "slide_in"
    EMBEDDED = "embedded"
    STANDALONE = "standalone"


class LeadStatus(str, enum.Enum):
    """Lead status."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    CONVERTED = "converted"
    LOST = "lost"


class LeadSource(str, enum.Enum):
    """Lead source."""
    FORM = "form"
    LANDING_PAGE = "landing_page"
    CHATBOT = "chatbot"
    POPUP = "popup"
    MANUAL = "manual"
    IMPORT = "import"
    API = "api"


class Form(Base):
    """Lead capture form model."""

    __tablename__ = "forms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    form_type = Column(SQLEnum(FormType), nullable=False, default=FormType.INLINE)

    # Configuration
    fields = Column(JSON, nullable=False)  # Field definitions
    settings = Column(JSON, default={})  # Form settings (validation, behavior)
    design = Column(JSON, default={})  # Design/styling configuration

    # Progressive profiling
    progressive_profiling_enabled = Column(Boolean, default=False)
    progressive_fields = Column(JSON, default=[])

    # Behavior
    thank_you_message = Column(Text)
    redirect_url = Column(String(500))
    email_notifications = Column(JSON, default=[])

    # Status
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)

    # Tracking
    views = Column(Integer, default=0)
    submissions = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)

    # Relationships
    leads = relationship("Lead", back_populates="form", cascade="all, delete-orphan")


class LandingPage(Base):
    """Landing page model."""

    __tablename__ = "landing_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)

    # Content
    sections = Column(JSON, default=[])  # Page sections
    form_id = Column(UUID(as_uuid=True), ForeignKey("forms.id"))

    # SEO
    meta_title = Column(String(500))
    meta_description = Column(Text)
    meta_keywords = Column(JSON, default=[])

    # Design
    template = Column(String(100))
    custom_css = Column(Text)
    custom_js = Column(Text)

    # A/B Testing
    variant_of = Column(UUID(as_uuid=True), ForeignKey("landing_pages.id"))
    variant_name = Column(String(100))
    traffic_percentage = Column(Integer, default=100)

    # Status
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)

    # Tracking
    views = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    bounce_rate = Column(Float, default=0.0)
    avg_time_on_page = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)

    # Relationships
    form = relationship("Form")
    variants = relationship("LandingPage", remote_side=[variant_of])


class Lead(Base):
    """Lead model."""

    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Basic Information
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50))
    first_name = Column(String(100))
    last_name = Column(String(100))
    company = Column(String(255))
    job_title = Column(String(255))

    # Additional Data
    custom_fields = Column(JSON, default={})

    # Enrichment Data
    enrichment_data = Column(JSON, default={})
    enrichment_status = Column(String(50))
    enrichment_provider = Column(String(50))
    enriched_at = Column(DateTime)

    # Validation
    email_validated = Column(Boolean, default=False)
    email_validation_score = Column(Float)
    phone_validated = Column(Boolean, default=False)

    # Source
    source = Column(SQLEnum(LeadSource), nullable=False)
    form_id = Column(UUID(as_uuid=True), ForeignKey("forms.id"))
    landing_page_url = Column(String(500))
    utm_source = Column(String(255))
    utm_medium = Column(String(255))
    utm_campaign = Column(String(255))
    utm_term = Column(String(255))
    utm_content = Column(String(255))
    referrer = Column(String(500))

    # Scoring
    score = Column(Integer, default=0)
    score_breakdown = Column(JSON, default={})
    grade = Column(String(10))

    # Status
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW, index=True)
    is_qualified = Column(Boolean, default=False)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of = Column(UUID(as_uuid=True), ForeignKey("leads.id"))

    # Assignment
    assigned_to = Column(String(255))
    assigned_at = Column(DateTime)

    # CRM Sync
    crm_id = Column(String(255))
    crm_synced_at = Column(DateTime)

    # Tracking
    ip_address = Column(String(45))
    user_agent = Column(Text)
    geo_data = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime)
    converted_at = Column(DateTime)

    # Relationships
    form = relationship("Form", back_populates="leads")
    activities = relationship("LeadActivity", back_populates="lead", cascade="all, delete-orphan")
    chatbot_conversations = relationship("ChatbotConversation", back_populates="lead")


class LeadActivity(Base):
    """Lead activity tracking model."""

    __tablename__ = "lead_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False, index=True)

    # Activity Details
    activity_type = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi

    # Relationships
    lead = relationship("Lead", back_populates="activities")

<<<<<<< HEAD
    # Indexes
    __table_args__ = (
        Index("idx_activity_lead_type", "lead_id", "type"),
        Index("idx_activity_created_at", "created_at"),
    )


class LeadScoreRecord(Base):
    """Lead score record database model."""

    __tablename__ = "lead_scores"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    value = Column(Integer, nullable=False)
    reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lead = relationship("Lead", back_populates="scores")


class TouchpointRecord(Base):
    """Touchpoint record database model."""

    __tablename__ = "touchpoints"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=False, index=True)
    channel = Column(String(100), nullable=False)
    campaign_id = Column(String(36))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lead = relationship("Lead", back_populates="touchpoints")


class ConversionRecord(Base):
    """Conversion record database model."""

    __tablename__ = "conversions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=False, index=True)
    type = Column(String(100), nullable=False)
    value = Column(Float)
    currency = Column(String(10), default="USD")
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lead = relationship("Lead", back_populates="conversions")


class Form(Base):
    """Form database model."""

    __tablename__ = "forms"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    fields = Column(JSON, nullable=False)
    submit_button_text = Column(String(100), default="Submit")
    success_message = Column(Text, default="Thank you for your submission!")
    is_active = Column(Boolean, default=True)
    submissions_count = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    embed_code = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    landing_pages = relationship("LandingPage", back_populates="form")
    popups = relationship("Popup", back_populates="form")


class LandingPage(Base):
    """Landing page database model."""

    __tablename__ = "landing_pages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    template = Column(String(100), nullable=False)
    content = Column(JSON, nullable=False)
    form_id = Column(String(36), ForeignKey("forms.id"))
    is_active = Column(Boolean, default=True)
    views = Column(Integer, default=0)
    submissions = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    form = relationship("Form", back_populates="landing_pages")


class Popup(Base):
    """Popup database model."""

    __tablename__ = "popups"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    form_id = Column(String(36), ForeignKey("forms.id"))
    trigger_type = Column(String(50), nullable=False)
    trigger_value = Column(String(100))
    is_active = Column(Boolean, default=True)
    views = Column(Integer, default=0)
    submissions = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    form = relationship("Form", back_populates="popups")


class NurtureCampaign(Base):
    """Nurture campaign database model."""

    __tablename__ = "nurture_campaigns"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    trigger_type = Column(String(50), nullable=False)
    trigger_conditions = Column(JSON)
    emails = Column(JSON, nullable=False)  # List of email configurations
    is_active = Column(Boolean, default=True)
    enrolled_count = Column(Integer, default=0)
    completed_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LeadEnrichment(Base):
    """Lead enrichment record database model."""

    __tablename__ = "lead_enrichments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=False, index=True)
    provider = Column(String(100), nullable=False)
    data = Column(JSON, nullable=False)
    status = Column(String(50), default="completed")
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
=======

class LeadMagnet(Base):
    """Lead magnet model."""

    __tablename__ = "lead_magnets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)  # ebook, whitepaper, template, etc.
    description = Column(Text)

    # Content
    file_url = Column(String(500))
    file_type = Column(String(50))
    file_size = Column(Integer)

    # Delivery
    delivery_method = Column(String(100))  # email, download, etc.
    email_template = Column(Text)

    # Tracking
    downloads = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatbotConversation(Base):
    """Chatbot conversation model."""

    __tablename__ = "chatbot_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), index=True)

    # Conversation Details
    messages = Column(JSON, default=[])
    context = Column(JSON, default={})

    # Status
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    lead_captured = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    lead = relationship("Lead", back_populates="chatbot_conversations")


class LeadScoringRule(Base):
    """Lead scoring rule model."""

    __tablename__ = "lead_scoring_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Rule Configuration
    conditions = Column(JSON, nullable=False)
    score_adjustment = Column(Integer, nullable=False)

    # Status
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
