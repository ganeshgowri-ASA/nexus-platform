"""
Contact and segment models for marketing automation.

This module contains models for contacts, lists, segments, and tags.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, JSON, Table, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from src.core.database import Base
from config.constants import ContactStatus


# Association tables for many-to-many relationships
contact_tags = Table(
    'contact_tags',
    Base.metadata,
    Column('contact_id', UUID(as_uuid=True), ForeignKey('contacts.id'), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id'), primary_key=True),
)

contact_lists = Table(
    'contact_lists',
    Base.metadata,
    Column('contact_id', UUID(as_uuid=True), ForeignKey('contacts.id'), primary_key=True),
    Column('list_id', UUID(as_uuid=True), ForeignKey('contact_lists_table.id'), primary_key=True),
)


class Contact(Base):
    """
    Contact/Lead model.

    Attributes:
        id: Contact ID
        workspace_id: Associated workspace ID
        email: Contact email (unique per workspace)
        first_name: First name
        last_name: Last name
        phone: Phone number
        company: Company name
        job_title: Job title
        status: Subscription status
        lead_score: Lead score (0-1000)
        custom_attributes: Custom attributes (JSON)
        subscribed_at: Subscription timestamp
        unsubscribed_at: Unsubscription timestamp
        last_activity_at: Last activity timestamp
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))
    company = Column(String(255))
    job_title = Column(String(255))
    status = Column(SQLEnum(ContactStatus), nullable=False, default=ContactStatus.SUBSCRIBED)
    lead_score = Column(Integer, default=0)
    custom_attributes = Column(JSON, default={})

    subscribed_at = Column(DateTime, default=datetime.utcnow)
    unsubscribed_at = Column(DateTime)
    last_activity_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="contacts")
    messages = relationship("CampaignMessage", back_populates="contact")
    events = relationship("ContactEvent", back_populates="contact", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=contact_tags, back_populates="contacts")
    lists = relationship("ContactList", secondary=contact_lists, back_populates="contacts")

    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, email={self.email})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "workspace_id": str(self.workspace_id),
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "company": self.company,
            "job_title": self.job_title,
            "status": self.status.value if self.status else None,
            "lead_score": self.lead_score,
            "custom_attributes": self.custom_attributes,
            "subscribed_at": self.subscribed_at.isoformat() if self.subscribed_at else None,
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ContactList(Base):
    """
    Contact list/audience model.

    Attributes:
        id: List ID
        workspace_id: Associated workspace ID
        name: List name
        description: List description
        is_dynamic: Dynamic list flag (auto-updated based on criteria)
        criteria: List criteria for dynamic lists (JSON)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "contact_lists_table"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_dynamic = Column(Boolean, default=False)
    criteria = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contacts = relationship("Contact", secondary=contact_lists, back_populates="lists")

    def __repr__(self) -> str:
        return f"<ContactList(id={self.id}, name={self.name})>"


class Tag(Base):
    """
    Tag model for organizing contacts.

    Attributes:
        id: Tag ID
        workspace_id: Associated workspace ID
        name: Tag name
        color: Tag color (hex code)
        created_at: Creation timestamp
    """

    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    color = Column(String(7))  # Hex color code
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    contacts = relationship("Contact", secondary=contact_tags, back_populates="tags")

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name})>"


class Segment(Base):
    """
    Segment model for advanced contact segmentation.

    Attributes:
        id: Segment ID
        workspace_id: Associated workspace ID
        name: Segment name
        description: Segment description
        conditions: Segment conditions (JSON)
        is_dynamic: Dynamic segment flag
        contact_count: Cached contact count
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    conditions = Column(JSON, nullable=False)
    is_dynamic = Column(Boolean, default=True)
    contact_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaigns = relationship("Campaign", back_populates="segment")

    def __repr__(self) -> str:
        return f"<Segment(id={self.id}, name={self.name})>"


class ContactEvent(Base):
    """
    Contact event/activity tracking.

    Attributes:
        id: Event ID
        contact_id: Associated contact ID
        event_type: Event type
        event_data: Event data (JSON)
        occurred_at: Event occurrence timestamp
        created_at: Creation timestamp
    """

    __tablename__ = "contact_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSON, default={})
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    contact = relationship("Contact", back_populates="events")

    def __repr__(self) -> str:
        return f"<ContactEvent(id={self.id}, type={self.event_type})>"
