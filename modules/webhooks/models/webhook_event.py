"""Webhook event subscription model"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class WebhookEvent(Base):
    """Webhook event subscription model"""

    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(255), nullable=False, index=True)  # e.g., "user.created", "order.completed"
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    webhook = relationship("Webhook", back_populates="events")

    def __repr__(self):
        return f"<WebhookEvent(id={self.id}, webhook_id={self.webhook_id}, event_type='{self.event_type}')>"
