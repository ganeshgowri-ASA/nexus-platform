"""Data models for email service."""

from datetime import datetime
from typing import Optional, List
from enum import Enum

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr, Field

from src.core.database import Base


class EmailStatus(str, Enum):
    """Email status enum."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    RECEIVED = "received"


class EmailPriority(str, Enum):
    """Email priority enum."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# SQLAlchemy ORM Models

class EmailAccount(Base):
    """Email account model."""
    __tablename__ = "email_accounts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))

    # SMTP settings
    smtp_host = Column(String(255))
    smtp_port = Column(Integer)
    smtp_username = Column(String(255))
    smtp_password = Column(String(255))  # Should be encrypted
    smtp_use_tls = Column(Boolean, default=True)

    # IMAP settings
    imap_host = Column(String(255))
    imap_port = Column(Integer)
    imap_username = Column(String(255))
    imap_password = Column(String(255))  # Should be encrypted
    imap_use_ssl = Column(Boolean, default=True)

    # Metadata
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    last_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    emails = relationship("Email", back_populates="account")


class Email(Base):
    """Email model."""
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("email_accounts.id"))

    # Email headers
    message_id = Column(String(255), unique=True, index=True)
    in_reply_to = Column(String(255))
    references = Column(Text)

    # From/To/Cc/Bcc
    from_address = Column(String(255), nullable=False)
    from_name = Column(String(255))
    to_addresses = Column(JSON)  # List of email addresses
    cc_addresses = Column(JSON)  # List of email addresses
    bcc_addresses = Column(JSON)  # List of email addresses
    reply_to = Column(String(255))

    # Content
    subject = Column(String(500))
    body_text = Column(Text)
    body_html = Column(Text)

    # Metadata
    status = Column(String(50), default=EmailStatus.DRAFT.value)
    priority = Column(String(50), default=EmailPriority.NORMAL.value)
    is_read = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)
    is_spam = Column(Boolean, default=False)
    spam_score = Column(Float, default=0.0)

    # Folder/Labels
    folder = Column(String(255), default="inbox")
    labels = Column(JSON)  # List of labels

    # Scheduling
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    received_at = Column(DateTime)

    # Tracking
    opened_count = Column(Integer, default=0)
    last_opened_at = Column(DateTime)
    clicked_count = Column(Integer, default=0)
    last_clicked_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    account = relationship("EmailAccount", back_populates="emails")
    attachments = relationship("EmailAttachment", back_populates="email", cascade="all, delete-orphan")
    tracking_events = relationship("EmailTrackingEvent", back_populates="email", cascade="all, delete-orphan")


class EmailAttachment(Base):
    """Email attachment model."""
    __tablename__ = "email_attachments"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"))

    filename = Column(String(255), nullable=False)
    content_type = Column(String(255))
    content_id = Column(String(255))  # For inline images
    size = Column(Integer)  # Size in bytes
    file_path = Column(String(500))  # Path to saved file
    is_inline = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    email = relationship("Email", back_populates="attachments")


class EmailTemplate(Base):
    """Email template model."""
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)

    subject = Column(String(500))
    body_html = Column(Text)
    body_text = Column(Text)

    # Template variables (JSON schema)
    variables = Column(JSON)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmailTrackingEvent(Base):
    """Email tracking event model."""
    __tablename__ = "email_tracking_events"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"))

    event_type = Column(String(50))  # opened, clicked, bounced, etc.
    ip_address = Column(String(50))
    user_agent = Column(Text)
    location = Column(String(255))

    # For click tracking
    url = Column(Text)

    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    email = relationship("Email", back_populates="tracking_events")


# Pydantic models for API/validation

class EmailAddress(BaseModel):
    """Email address model."""
    email: EmailStr
    name: Optional[str] = None


class EmailCreate(BaseModel):
    """Email creation model."""
    to: List[EmailStr]
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    subject: str
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    reply_to: Optional[EmailStr] = None
    priority: EmailPriority = EmailPriority.NORMAL
    scheduled_at: Optional[datetime] = None


class EmailResponse(BaseModel):
    """Email response model."""
    id: int
    from_address: str
    to_addresses: List[str]
    subject: str
    status: EmailStatus
    created_at: datetime
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemplateCreate(BaseModel):
    """Template creation model."""
    name: str
    description: Optional[str] = None
    subject: str
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    variables: Optional[dict] = None


class AttachmentInfo(BaseModel):
    """Attachment information model."""
    filename: str
    content_type: str
    size: int
    is_inline: bool = False
