"""
Notification model for storing notification records
"""
from sqlalchemy import Column, String, DateTime, Text, JSON, Enum, Boolean, Integer
from sqlalchemy.sql import func
from backend.database import Base
import enum
import uuid


class NotificationStatus(str, enum.Enum):
    """Notification status enumeration"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationPriority(str, enum.Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannel(str, enum.Enum):
    """Available notification channels"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class Notification(Base):
    """
    Main notification model
    Stores all notifications across all channels
    """
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # User identification
    user_id = Column(String(36), nullable=False, index=True)

    # Notification content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Additional structured data

    # Channel and delivery
    channel = Column(Enum(NotificationChannel), nullable=False, index=True)
    recipient = Column(String(255), nullable=False)  # email/phone/device_token/user_id

    # Status and priority
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING, index=True)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL)

    # Template reference
    template_id = Column(String(36), nullable=True)
    template_vars = Column(JSON, nullable=True)

    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    # Tracking
    read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Retry mechanism
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_error = Column(Text, nullable=True)

    # Metadata
    category = Column(String(50), nullable=True, index=True)  # e.g., "order", "alert", "marketing"
    action_url = Column(String(500), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "channel": self.channel.value if self.channel else None,
            "recipient": self.recipient,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "template_id": self.template_id,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "read": self.read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "category": self.category,
            "action_url": self.action_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
