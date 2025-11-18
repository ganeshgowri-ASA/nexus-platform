from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import secrets

Base = declarative_base()


class APIKey(Base):
    """Database model for API keys"""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)

    # Owner information
    user_id = Column(String, nullable=True)
    email = Column(String, nullable=True)

    # Status
    active = Column(Boolean, default=True)

    # Permissions
    scopes = Column(JSON, default=list)  # List of allowed scopes/permissions
    allowed_routes = Column(JSON, default=list)  # Specific routes this key can access

    # Rate limiting (per API key)
    rate_limit = Column(Integer, default=1000)  # requests per hour
    rate_limit_window = Column(Integer, default=3600)  # seconds

    # Usage tracking
    total_requests = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)

    # Expiration
    expires_at = Column(DateTime, nullable=True)

    # Metadata
    description = Column(String, nullable=True)
    metadata = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def generate_key() -> str:
        """Generate a secure API key"""
        return f"nxs_{secrets.token_urlsafe(32)}"

    def __repr__(self):
        return f"<APIKey {self.name} ({self.key[:16]}...)>"
