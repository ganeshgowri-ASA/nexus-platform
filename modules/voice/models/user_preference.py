"""User voice preferences model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserVoicePreference(Base):
    """Model for user voice preferences."""

    __tablename__ = 'user_voice_preferences'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, nullable=False, index=True)

    # Speech-to-text preferences
    preferred_language = Column(String(10), default='en-US')
    enable_profanity_filter = Column(Boolean, default=False)
    enable_automatic_punctuation = Column(Boolean, default=True)

    # Text-to-speech preferences
    tts_voice_name = Column(String(100), default='en-US-Neural2-A')
    tts_speaking_rate = Column(Float, default=1.0)  # 0.25 to 4.0
    tts_pitch = Column(Float, default=0.0)  # -20.0 to 20.0
    tts_volume_gain_db = Column(Float, default=0.0)

    # Voice activation
    wake_word = Column(String(100), default='nexus')
    enable_wake_word = Column(Boolean, default=True)
    voice_activation_sensitivity = Column(Float, default=0.7)

    # NLP preferences
    preferred_ai_model = Column(String(100), default='claude-3-sonnet')
    enable_context_memory = Column(Boolean, default=True)
    context_window_size = Column(Integer, default=5)  # Number of previous interactions to remember

    # UI preferences
    show_transcript = Column(Boolean, default=True)
    show_confidence_scores = Column(Boolean, default=False)
    enable_visual_feedback = Column(Boolean, default=True)

    # Privacy settings
    store_audio_recordings = Column(Boolean, default=False)
    share_analytics = Column(Boolean, default=True)

    # Custom commands
    custom_commands = Column(JSON)  # User-defined voice commands

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserVoicePreference(user_id={self.user_id}, lang={self.preferred_language})>"
