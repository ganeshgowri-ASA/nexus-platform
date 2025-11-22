"""Webhook model"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Webhook(Base):
    """Webhook endpoint model"""

    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    # Security
    secret = Column(String(255), nullable=False)  # For HMAC signature
    is_active = Column(Boolean, default=True, index=True)

    # Configuration
    headers = Column(JSON, default=dict)  # Custom headers
    timeout = Column(Integer, default=30)  # Request timeout in seconds

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=True)

    # Relationships
    events = relationship("WebhookEvent", back_populates="webhook", cascade="all, delete-orphan")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Webhook(id={self.id}, name='{self.name}', url='{self.url}')>"
