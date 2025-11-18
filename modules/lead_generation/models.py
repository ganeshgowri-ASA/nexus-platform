"""
Database models for lead generation module.
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

    # Relationships
    lead = relationship("Lead", back_populates="activities")


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
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
