"""Data source model."""
from sqlalchemy import Column, String, Integer, JSON, DateTime, Boolean, Text
from sqlalchemy.sql import func
from shared.database.base import Base
import uuid


class DataSource(Base):
    """Data source configuration model."""

    __tablename__ = "data_sources"
    __table_args__ = {"schema": "etl"}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    source_type = Column(
        String(50), nullable=False
    )  # csv, json, sql, api, s3, ftp, mongodb, etc.
    connection_config = Column(JSON, nullable=False)  # Connection details (encrypted)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<DataSource(name='{self.name}', type='{self.source_type}')>"
