"""Webhook delivery log model"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import Base


class DeliveryStatus(str, enum.Enum):
    """Delivery status enumeration"""
    PENDING = "pending"
    SENDING = "sending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookDelivery(Base):
    """Webhook delivery log model"""

    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False, index=True)

    # Event details
    event_type = Column(String(255), nullable=False, index=True)
    event_id = Column(String(255), nullable=True, index=True)  # External event ID
    payload = Column(JSON, nullable=False)

    # Delivery details
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING, index=True)
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=5)

    # Response details
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    response_headers = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Request details
    request_headers = Column(JSON, nullable=True)
    request_url = Column(Text, nullable=True)

    # Relationships
    webhook = relationship("Webhook", back_populates="deliveries")

    def __repr__(self):
        return f"<WebhookDelivery(id={self.id}, webhook_id={self.webhook_id}, status='{self.status}')>"
