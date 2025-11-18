"""
Campaign models for marketing automation.

This module contains models related to campaigns, messages, and templates.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import Base
from config.constants import CampaignType, CampaignStatus, MessageStatus


class Campaign(Base):
    """
    Campaign model for email, SMS, and multi-channel campaigns.

    Attributes:
        id: Campaign ID
        workspace_id: Associated workspace ID
        name: Campaign name
        description: Campaign description
        type: Campaign type (email, sms, multi_channel)
        status: Campaign status
        subject: Email subject line (for email campaigns)
        content: Campaign content/body
        from_name: Sender name
        from_email: Sender email
        reply_to: Reply-to email
        segment_id: Target segment ID (optional)
        scheduled_at: Scheduled send time
        sent_at: Actual send time
        completed_at: Completion time
        created_by: User ID who created the campaign
        total_recipients: Total number of recipients
        total_sent: Total messages sent
        total_delivered: Total messages delivered
        total_opened: Total messages opened
        total_clicked: Total messages clicked
        total_bounced: Total messages bounced
        total_unsubscribed: Total unsubscribes
        metadata: Additional metadata (JSON)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(SQLEnum(CampaignType), nullable=False, default=CampaignType.EMAIL)
    status = Column(SQLEnum(CampaignStatus), nullable=False, default=CampaignStatus.DRAFT)

    # Email-specific fields
    subject = Column(String(500))
    content = Column(Text, nullable=False)
    from_name = Column(String(255))
    from_email = Column(String(255))
    reply_to = Column(String(255))

    # Targeting
    segment_id = Column(UUID(as_uuid=True), ForeignKey("segments.id"))

    # Scheduling
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Metrics
    total_recipients = Column(Integer, default=0)
    total_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)
    total_bounced = Column(Integer, default=0)
    total_unsubscribed = Column(Integer, default=0)

    metadata = Column(JSON, default={})

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="campaigns")
    created_by_user = relationship("User", back_populates="campaigns")
    segment = relationship("Segment", back_populates="campaigns")
    messages = relationship("CampaignMessage", back_populates="campaign", cascade="all, delete-orphan")
    ab_tests = relationship("ABTest", back_populates="campaign", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name={self.name}, status={self.status})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "workspace_id": str(self.workspace_id),
            "name": self.name,
            "description": self.description,
            "type": self.type.value if self.type else None,
            "status": self.status.value if self.status else None,
            "subject": self.subject,
            "from_name": self.from_name,
            "from_email": self.from_email,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "metrics": {
                "total_recipients": self.total_recipients,
                "total_sent": self.total_sent,
                "total_delivered": self.total_delivered,
                "total_opened": self.total_opened,
                "total_clicked": self.total_clicked,
                "total_bounced": self.total_bounced,
                "total_unsubscribed": self.total_unsubscribed,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CampaignMessage(Base):
    """
    Individual campaign message tracking.

    Attributes:
        id: Message ID
        campaign_id: Associated campaign ID
        contact_id: Recipient contact ID
        status: Message status
        sent_at: Send timestamp
        delivered_at: Delivery timestamp
        opened_at: Open timestamp
        clicked_at: Click timestamp
        bounced_at: Bounce timestamp
        error_message: Error message if failed
        metadata: Additional metadata (JSON)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "campaign_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False, index=True)
    status = Column(SQLEnum(MessageStatus), nullable=False, default=MessageStatus.PENDING)

    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    bounced_at = Column(DateTime)

    error_message = Column(Text)
    metadata = Column(JSON, default={})

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="messages")
    contact = relationship("Contact", back_populates="messages")

    def __repr__(self) -> str:
        return f"<CampaignMessage(id={self.id}, status={self.status})>"


class EmailTemplate(Base):
    """
    Email template model.

    Attributes:
        id: Template ID
        workspace_id: Associated workspace ID
        name: Template name
        description: Template description
        subject: Email subject template
        html_content: HTML content
        text_content: Plain text content
        thumbnail_url: Template thumbnail URL
        is_public: Public template flag
        category: Template category
        created_by: Creator user ID
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "email_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    subject = Column(String(500))
    html_content = Column(Text, nullable=False)
    text_content = Column(Text)
    thumbnail_url = Column(String(500))
    is_public = Column(Boolean, default=False)
    category = Column(String(100))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<EmailTemplate(id={self.id}, name={self.name})>"


class ABTest(Base):
    """
    A/B test model for campaign testing.

    Attributes:
        id: Test ID
        campaign_id: Associated campaign ID
        name: Test name
        variant_a: Variant A configuration (JSON)
        variant_b: Variant B configuration (JSON)
        split_percentage: Split percentage for variant B
        winner: Winning variant (a or b)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "ab_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    variant_a = Column(JSON, nullable=False)
    variant_b = Column(JSON, nullable=False)
    split_percentage = Column(Float, default=50.0)
    winner = Column(String(1))  # 'a' or 'b'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="ab_tests")

    def __repr__(self) -> str:
        return f"<ABTest(id={self.id}, name={self.name})>"
