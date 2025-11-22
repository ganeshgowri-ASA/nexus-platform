"""ETL Pipeline model."""
from sqlalchemy import Column, String, Integer, JSON, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.database.base import Base
import uuid


class Pipeline(Base):
    """ETL Pipeline configuration model."""

    __tablename__ = "pipelines"
    __table_args__ = {"schema": "etl"}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    source_id = Column(String(36), ForeignKey("etl.data_sources.id"), nullable=False)

    # Pipeline configuration
    extract_config = Column(JSON, nullable=False)  # Query, file path, API endpoint, etc.
    transform_config = Column(JSON, nullable=False)  # List of transformations
    load_config = Column(JSON, nullable=False)  # Destination configuration

    # Validation and quality settings
    validation_rules = Column(JSON, nullable=True)
    deduplication_config = Column(JSON, nullable=True)

    # Pipeline settings
    is_active = Column(Boolean, default=True)
    schedule = Column(String(100), nullable=True)  # Cron expression
    parallel_processing = Column(Boolean, default=False)
    batch_size = Column(Integer, default=1000)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=True)
    last_run = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Pipeline(name='{self.name}', active={self.is_active})>"
