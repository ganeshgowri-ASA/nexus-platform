from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class RateLimit(Base):
    """Database model for rate limit tracking (fallback when Redis is unavailable)"""

    __tablename__ = "rate_limits"

    id = Column(Integer, primary_key=True, index=True)

    # Identifier (could be IP, API key, user ID, etc.)
    identifier = Column(String, index=True, nullable=False)
    identifier_type = Column(String, index=True)  # ip, api_key, user

    # Route information
    route_name = Column(String, index=True, nullable=True)

    # Rate limit tracking
    request_count = Column(Integer, default=0)
    window_start = Column(DateTime, default=datetime.utcnow)
    window_end = Column(DateTime)

    # Limit configuration
    max_requests = Column(Integer, nullable=False)
    window_seconds = Column(Integer, nullable=False)

    # Status
    blocked = Column(Boolean, default=False)
    blocked_until = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<RateLimit {self.identifier} {self.request_count}/{self.max_requests}>"
