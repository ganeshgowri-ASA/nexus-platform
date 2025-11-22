"""OAuth Connection model."""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from shared.database.base import Base
import uuid


class OAuthConnection(Base):
    """OAuth 2.0 connection storage."""

    __tablename__ = "oauth_connections"
    __table_args__ = {"schema": "integration_hub"}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    integration_id = Column(String(36), ForeignKey("integration_hub.integrations.id"), nullable=False)

    # Connection details
    name = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=True)  # User who authorized

    # OAuth tokens (encrypted)
    encrypted_access_token = Column(Text, nullable=False)
    encrypted_refresh_token = Column(Text, nullable=True)
    token_type = Column(String(50), default="Bearer")
    scopes = Column(JSON, nullable=True)  # List of granted scopes

    # Token expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Connection metadata
    provider_user_id = Column(String(255), nullable=True)  # ID in the provider system
    provider_user_info = Column(JSON, nullable=True)  # Email, name, etc.

    # Status
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<OAuthConnection(name='{self.name}', integration_id='{self.integration_id}')>"
