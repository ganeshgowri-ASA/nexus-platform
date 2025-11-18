"""
Database models for lead generation module.

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

    # Relationships
    lead = relationship("Lead", back_populates="activities")

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
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
