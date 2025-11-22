"""
Base database models for NEXUS Platform.

This module contains the base model class and common models used across modules.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import Base


class User(Base):
    """
    User model for authentication and authorization.

    Attributes:
        id: User ID
        email: User email (unique)
        password_hash: Hashed password
        first_name: First name
        last_name: Last name
        is_active: Account active status
        is_superuser: Superuser flag
        workspace_id: Associated workspace ID
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="users")
    campaigns = relationship("Campaign", back_populates="created_by_user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_active": self.is_active,
            "workspace_id": str(self.workspace_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Workspace(Base):
    """
    Workspace/Tenant model for multi-tenancy.

    Attributes:
        id: Workspace ID
        name: Workspace name
        slug: URL-friendly slug
        is_active: Active status
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "workspaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="workspace")
    campaigns = relationship("Campaign", back_populates="workspace")
    contacts = relationship("Contact", back_populates="workspace")
    automations = relationship("Automation", back_populates="workspace")

    def __repr__(self) -> str:
        return f"<Workspace(id={self.id}, name={self.name})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
