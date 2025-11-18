"""Transformation model."""
from sqlalchemy import Column, String, Integer, JSON, DateTime, Boolean, Text
from sqlalchemy.sql import func
from shared.database.base import Base
import uuid


class Transformation(Base):
    """Reusable transformation template model."""

    __tablename__ = "transformations"
    __table_args__ = {"schema": "etl"}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # filter, map, aggregate, join, etc.

    # Transformation definition
    transformation_type = Column(
        String(100), nullable=False
    )  # rename_columns, filter_rows, convert_type, etc.
    config = Column(JSON, nullable=False)  # Transformation parameters

    # Metadata
    is_public = Column(Boolean, default=False)  # Shared transformation
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<Transformation(name='{self.name}', type='{self.transformation_type}')>"
