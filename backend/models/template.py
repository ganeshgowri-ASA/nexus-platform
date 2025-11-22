"""
Notification template model
"""
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean
from sqlalchemy.sql import func
from backend.database import Base
import uuid


class NotificationTemplate(Base):
    """
    Notification templates for consistent messaging
    Supports variables and multiple channels
    """
    __tablename__ = "notification_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Template identification
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)

    # Template content (supports Jinja2 syntax)
    subject = Column(String(255), nullable=True)  # For email/push
    body = Column(Text, nullable=False)
    html_body = Column(Text, nullable=True)  # For email HTML version

    # Channel-specific templates
    email_template = Column(JSON, nullable=True)  # Email-specific settings
    sms_template = Column(JSON, nullable=True)    # SMS-specific settings
    push_template = Column(JSON, nullable=True)   # Push-specific settings
    in_app_template = Column(JSON, nullable=True) # In-app-specific settings

    # Template variables schema (for validation)
    variables = Column(JSON, nullable=True)  # e.g., ["user_name", "order_id", "amount"]

    # Template status
    active = Column(Boolean, default=True)
    version = Column(String(20), default="1.0")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert template to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "subject": self.subject,
            "body": self.body,
            "html_body": self.html_body,
            "email_template": self.email_template,
            "sms_template": self.sms_template,
            "push_template": self.push_template,
            "in_app_template": self.in_app_template,
            "variables": self.variables,
            "active": self.active,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
