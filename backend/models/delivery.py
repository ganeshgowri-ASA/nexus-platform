"""
Delivery tracking and logging model
"""
from sqlalchemy import Column, String, DateTime, Text, JSON, Enum, Integer, Float
from sqlalchemy.sql import func
from backend.database import Base
import enum
import uuid


class DeliveryStatus(str, enum.Enum):
    """Delivery status tracking"""
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    REJECTED = "rejected"
    OPENED = "opened"
    CLICKED = "clicked"


class DeliveryLog(Base):
    """
    Delivery tracking log
    Tracks the entire delivery lifecycle of each notification
    """
    __tablename__ = "delivery_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Reference to notification
    notification_id = Column(String(36), nullable=False, index=True)

    # Delivery details
    channel = Column(String(20), nullable=False, index=True)
    recipient = Column(String(255), nullable=False)
    status = Column(Enum(DeliveryStatus), nullable=False, index=True)

    # Provider information
    provider = Column(String(50), nullable=True)  # e.g., "sendgrid", "twilio", "fcm"
    provider_message_id = Column(String(255), nullable=True, index=True)
    provider_response = Column(JSON, nullable=True)

    # Timing information
    queued_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)

    # Engagement tracking
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)

    # Error tracking
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Performance metrics
    processing_time_ms = Column(Float, nullable=True)

    # Additional metadata
    metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert delivery log to dictionary"""
        return {
            "id": self.id,
            "notification_id": self.notification_id,
            "channel": self.channel,
            "recipient": self.recipient,
            "status": self.status.value if self.status else None,
            "provider": self.provider,
            "provider_message_id": self.provider_message_id,
            "queued_at": self.queued_at.isoformat() if self.queued_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "clicked_at": self.clicked_at.isoformat() if self.clicked_at else None,
            "open_count": self.open_count,
            "click_count": self.click_count,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
