"""API Key model."""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from shared.database.base import Base
import uuid


class APIKey(Base):
    """API Key storage for integrations."""

    __tablename__ = "api_keys"
    __table_args__ = {"schema": "integration_hub"}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    integration_id = Column(String(36), ForeignKey("integration_hub.integrations.id"), nullable=False)

    # Key details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    encrypted_key = Column(Text, nullable=False)  # Encrypted API key

    # Additional credentials
    additional_fields = Column(Text, nullable=True)  # Encrypted JSON for extra fields

    # Status
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Rate limiting
    rate_limit_per_minute = Column(String(50), nullable=True)
    rate_limit_per_hour = Column(String(50), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<APIKey(name='{self.name}', integration_id='{self.integration_id}')>"
