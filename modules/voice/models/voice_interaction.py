"""Voice interaction database model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class VoiceInteraction(Base):
    """Model for storing voice interactions."""

    __tablename__ = 'voice_interactions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    session_id = Column(String(100), index=True)

    # Audio data
    audio_file_path = Column(String(500))
    audio_format = Column(String(50))
    audio_duration = Column(Float)

    # Transcription
    transcript = Column(Text)
    transcription_confidence = Column(Float)
    language_code = Column(String(10), default='en-US')

    # Intent recognition
    detected_intent = Column(String(200))
    intent_confidence = Column(Float)
    entities = Column(JSON)  # Extracted entities from NLP

    # Response
    response_text = Column(Text)
    response_audio_path = Column(String(500))

    # Action taken
    action_type = Column(String(100))
    action_result = Column(JSON)
    action_success = Column(Boolean, default=True)

    # Metadata
    processing_time_ms = Column(Float)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<VoiceInteraction(id={self.id}, user={self.user_id}, intent={self.detected_intent})>"
