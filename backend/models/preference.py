"""
Notification preference and unsubscribe models
"""
from sqlalchemy import Column, String, DateTime, Boolean, JSON, UniqueConstraint
from sqlalchemy.sql import func
from backend.database import Base
import uuid


class NotificationPreference(Base):
    """
    User notification preferences
    Controls which channels and categories users receive notifications on
    """
    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint('user_id', 'category', 'channel', name='unique_user_category_channel'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)

    # Preference settings
    category = Column(String(50), nullable=False)  # e.g., "marketing", "transactional", "alerts"
    channel = Column(String(20), nullable=False)   # email, sms, push, in_app
    enabled = Column(Boolean, default=True)

    # Channel-specific settings
    settings = Column(JSON, nullable=True)  # Additional settings like frequency, quiet hours, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert preference to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category": self.category,
            "channel": self.channel,
            "enabled": self.enabled,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UnsubscribeToken(Base):
    """
    Unsubscribe tokens for one-click unsubscribe functionality
    """
    __tablename__ = "unsubscribe_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token = Column(String(64), unique=True, nullable=False, index=True)

    # Token details
    user_id = Column(String(36), nullable=False, index=True)
    category = Column(String(50), nullable=True)  # Specific category or None for all
    channel = Column(String(20), nullable=True)   # Specific channel or None for all

    # Token status
    used = Column(Boolean, default=False)
    used_at = Column(DateTime(timezone=True), nullable=True)

    # Token expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        """Convert token to dictionary"""
        return {
            "id": self.id,
            "token": self.token,
            "user_id": self.user_id,
            "category": self.category,
            "channel": self.channel,
            "used": self.used,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
