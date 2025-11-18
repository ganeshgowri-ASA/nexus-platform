"""
User model for authentication and user management.

This module defines the User model with authentication fields,
profile information, and relationships.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, String, Text, BigInteger
from sqlalchemy.orm import relationship

from backend.models.base import BaseModel


class User(BaseModel):
    """
    User model for authentication and profile management.

    Attributes:
        email: User email address (unique)
        username: Username (unique)
        full_name: User's full name
        hashed_password: Hashed password
        is_active: Whether user account is active
        is_admin: Whether user has admin privileges
        is_superuser: Whether user has superuser privileges
        is_verified: Whether user email is verified
        avatar_url: URL to user's avatar image
        bio: User biography
        phone: Phone number
        last_login: Last login timestamp
        password_changed_at: Password last changed timestamp
        storage_quota: Storage quota in bytes
        storage_used: Storage used in bytes
        preferences: User preferences (JSON)
        api_key_hash: Hashed API key for API access
    """

    __tablename__ = "users"

    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Profile fields
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)

    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Activity tracking
    last_login = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Storage quota (in bytes)
    storage_quota = Column(BigInteger, default=10737418240, nullable=False)  # 10GB default
    storage_used = Column(BigInteger, default=0, nullable=False)

    # User preferences (stored as JSON)
    preferences = Column(Text, nullable=True)

    # API key for programmatic access
    api_key_hash = Column(String(255), nullable=True)

    # Relationships (will be defined when creating related models)
    # documents = relationship("Document", back_populates="owner")
    # folders = relationship("Folder", back_populates="owner")

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    @property
    def storage_quota_mb(self) -> float:
        """Get storage quota in MB."""
        return self.storage_quota / (1024 * 1024)

    @property
    def storage_used_mb(self) -> float:
        """Get storage used in MB."""
        return self.storage_used / (1024 * 1024)

    @property
    def storage_available(self) -> int:
        """Get available storage in bytes."""
        return max(0, self.storage_quota - self.storage_used)

    @property
    def storage_percentage_used(self) -> float:
        """Get percentage of storage used."""
        if self.storage_quota == 0:
            return 0.0
        return (self.storage_used / self.storage_quota) * 100

    def has_storage_available(self, size: int) -> bool:
        """
        Check if user has enough storage available.

        Args:
            size: Required size in bytes

        Returns:
            bool: True if storage is available
        """
        return self.storage_available >= size

    def update_storage_used(self, delta: int) -> None:
        """
        Update storage used by delta.

        Args:
            delta: Change in storage (positive or negative)
        """
        self.storage_used = max(0, self.storage_used + delta)
