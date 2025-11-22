"""Voice command registry model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class VoiceCommand(Base):
    """Model for registered voice commands."""

    __tablename__ = 'voice_commands'

    id = Column(Integer, primary_key=True, index=True)
    command_name = Column(String(200), unique=True, nullable=False, index=True)

    # Command patterns
    patterns = Column(JSON)  # List of text patterns that trigger this command
    keywords = Column(JSON)  # Key phrases to match

    # Intent mapping
    intent = Column(String(200), index=True)
    category = Column(String(100))  # e.g., 'productivity', 'navigation', 'system'

    # Execution details
    handler_function = Column(String(200))  # Function to call
    module_name = Column(String(200))  # Which NEXUS module handles this
    required_params = Column(JSON)  # Parameters needed

    # Configuration
    is_active = Column(Boolean, default=True)
    requires_confirmation = Column(Boolean, default=False)
    priority = Column(Integer, default=0)  # Higher priority commands matched first

    # Documentation
    description = Column(Text)
    example_phrases = Column(JSON)
    help_text = Column(Text)

    # Usage stats
    usage_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    last_used = Column(DateTime)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))

    def __repr__(self):
        return f"<VoiceCommand(name={self.command_name}, intent={self.intent})>"
