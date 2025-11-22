"""Webhook model."""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, JSON, Integer
from sqlalchemy.sql import func
from shared.database.base import Base
import uuid


class Webhook(Base):
    """Webhook configuration and logs."""

    __tablename__ = "webhooks"
    __table_args__ = {"schema": "integration_hub"}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    integration_id = Column(String(36), ForeignKey("integration_hub.integrations.id"), nullable=False)

    # Webhook details
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)  # Webhook URL endpoint
    secret = Column(String(255), nullable=True)  # Webhook secret for verification
    events = Column(JSON, nullable=False)  # List of events to listen for

    # Payload configuration
    payload_template = Column(JSON, nullable=True)  # Custom payload template
    headers = Column(JSON, nullable=True)  # Custom headers

    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)

    # Status
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    trigger_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<Webhook(name='{self.name}', integration_id='{self.integration_id}')>"
