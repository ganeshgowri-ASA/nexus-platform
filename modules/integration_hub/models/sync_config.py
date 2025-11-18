"""Sync Configuration model."""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.sql import func
from shared.database.base import Base
import uuid


class SyncConfig(Base):
    """Data synchronization configuration."""

    __tablename__ = "sync_configs"
    __table_args__ = {"schema": "integration_hub"}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    integration_id = Column(String(36), ForeignKey("integration_hub.integrations.id"), nullable=False)
    connection_id = Column(
        String(36), nullable=False
    )  # Reference to OAuth or APIKey connection

    # Sync configuration
    name = Column(String(255), nullable=False)
    sync_direction = Column(String(50), nullable=False)  # inbound, outbound, bidirectional
    source_config = Column(JSON, nullable=False)  # Source data configuration
    destination_config = Column(JSON, nullable=False)  # Destination configuration

    # Mapping and transformation
    field_mapping = Column(JSON, nullable=True)  # Field mapping rules
    transformation_rules = Column(JSON, nullable=True)  # Data transformation rules

    # Scheduling
    schedule_type = Column(String(50), nullable=False)  # cron, interval, realtime
    schedule_expression = Column(String(255), nullable=False)
    batch_size = Column(Integer, default=100)

    # Status
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    next_sync = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<SyncConfig(name='{self.name}', direction='{self.sync_direction}')>"
