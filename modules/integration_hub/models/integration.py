"""Integration model."""
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer
from sqlalchemy.sql import func
from shared.database.base import Base
import uuid


class Integration(Base):
    """Available integrations (marketplace)."""

    __tablename__ = "integrations"
    __table_args__ = {"schema": "integration_hub"}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    provider = Column(String(100), nullable=False)  # github, slack, google, etc.
    category = Column(String(50), nullable=False)  # productivity, communication, storage, etc.
    logo_url = Column(String(500), nullable=True)

    # Auth configuration
    auth_type = Column(
        String(50), nullable=False
    )  # oauth2, api_key, basic_auth, bearer_token
    auth_config = Column(JSON, nullable=False)  # OAuth endpoints, scopes, etc.

    # Features
    supports_webhooks = Column(Boolean, default=False)
    supports_sync = Column(Boolean, default=False)
    supported_actions = Column(JSON, nullable=True)  # List of available actions

    # Marketplace info
    is_public = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    install_count = Column(Integer, default=0)
    rating = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Integration(name='{self.name}', provider='{self.provider}')>"
