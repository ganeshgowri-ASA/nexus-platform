from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Metric(Base):
    """Database model for API metrics and monitoring"""

    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)

    # Request information
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    method = Column(String, index=True)
    path = Column(String, index=True)
    route_name = Column(String, index=True, nullable=True)

    # Response information
    status_code = Column(Integer, index=True)
    response_time = Column(Float)  # milliseconds

    # Client information
    client_ip = Column(String, index=True)
    user_agent = Column(String, nullable=True)
    api_key_id = Column(Integer, nullable=True, index=True)

    # Request/Response sizes
    request_size = Column(Integer, default=0)  # bytes
    response_size = Column(Integer, default=0)  # bytes

    # Error tracking
    error = Column(Boolean, default=False, index=True)
    error_message = Column(String, nullable=True)
    error_type = Column(String, nullable=True)

    # Backend information
    backend_url = Column(String, nullable=True)
    backend_response_time = Column(Float, nullable=True)

    # Cache
    cache_hit = Column(Boolean, default=False, index=True)

    # Additional metadata
    metadata = Column(JSON, default=dict)

    __table_args__ = (
        Index('idx_timestamp_route', 'timestamp', 'route_name'),
        Index('idx_timestamp_status', 'timestamp', 'status_code'),
    )

    def __repr__(self):
        return f"<Metric {self.method} {self.path} {self.status_code} {self.response_time}ms>"
