from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Route(Base):
    """Database model for API routes"""

    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    path = Column(String, nullable=False)
    method = Column(String, nullable=False)  # GET, POST, PUT, DELETE, etc.
    target_url = Column(String, nullable=False)

    # Route configuration
    enabled = Column(Boolean, default=True)
    require_auth = Column(Boolean, default=True)

    # Rate limiting
    rate_limit = Column(Integer, default=100)  # requests per minute
    rate_limit_window = Column(Integer, default=60)  # seconds

    # Load balancing
    load_balance_strategy = Column(String, default="round_robin")  # round_robin, least_connections, ip_hash
    target_urls = Column(JSON, default=list)  # Multiple backend URLs

    # Caching
    cache_enabled = Column(Boolean, default=False)
    cache_ttl = Column(Integer, default=300)  # seconds

    # Request/Response transformation
    request_transform = Column(JSON, nullable=True)  # Transformation rules
    response_transform = Column(JSON, nullable=True)

    # Headers
    headers_to_add = Column(JSON, default=dict)
    headers_to_remove = Column(JSON, default=list)

    # Timeouts
    timeout = Column(Float, default=30.0)  # seconds

    # Metadata
    description = Column(String, nullable=True)
    tags = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Route {self.name} {self.method} {self.path}>"
