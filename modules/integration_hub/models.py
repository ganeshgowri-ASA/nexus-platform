"""
SQLAlchemy database models for Integration Hub.

This module defines the core database schema for managing integrations,
connections, sync jobs, webhooks, and credentials.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON,
    ForeignKey, Enum, Float, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from cryptography.fernet import Fernet
import json

Base = declarative_base()


class AuthType(str, PyEnum):
    """Authentication types supported by connectors."""
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    JWT = "jwt"
    BASIC = "basic"
    CUSTOM = "custom"


class IntegrationStatus(str, PyEnum):
    """Integration connection status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"
    EXPIRED = "expired"


class SyncStatus(str, PyEnum):
    """Synchronization job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class SyncDirection(str, PyEnum):
    """Direction of data synchronization."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class WebhookStatus(str, PyEnum):
    """Webhook delivery status."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class Integration(Base):
    """
    Represents an integration configuration for a third-party service.

    An integration defines the type of service (e.g., Salesforce, Slack)
    and its base configuration. Multiple connections can be created for
    a single integration.
    """
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    provider = Column(String(100), nullable=False, index=True)
    auth_type = Column(Enum(AuthType), nullable=False)
    icon_url = Column(String(500))
    category = Column(String(100), index=True)

    # Configuration
    config = Column(JSON, default={})
    default_scopes = Column(JSON, default=[])
    api_base_url = Column(String(500))
    documentation_url = Column(String(500))

    # Rate limiting
    rate_limit_requests = Column(Integer)
    rate_limit_period = Column(Integer)  # seconds

    # Features
    supports_webhooks = Column(Boolean, default=False)
    supports_bidirectional_sync = Column(Boolean, default=False)
    supports_batch_operations = Column(Boolean, default=False)

    # Metadata
    version = Column(String(50))
    is_active = Column(Boolean, default=True, index=True)
    is_premium = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    connections = relationship("Connection", back_populates="integration", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Integration(id={self.id}, name='{self.name}', provider='{self.provider}')>"


class Connection(Base):
    """
    Represents an active connection to a third-party service.

    A connection is an instance of an integration with specific credentials
    and configuration for a user or organization.
    """
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)

    # Connection details
    name = Column(String(255), nullable=False)
    status = Column(Enum(IntegrationStatus), default=IntegrationStatus.PENDING, index=True)

    # Credentials (encrypted)
    credential_id = Column(Integer, ForeignKey("credentials.id"), nullable=True)

    # Connection-specific config
    config = Column(JSON, default={})
    scopes = Column(JSON, default=[])

    # Connection metadata
    connected_account_id = Column(String(255))  # ID in the third-party service
    connected_account_name = Column(String(255))
    connected_account_email = Column(String(255))

    # Health tracking
    last_sync_at = Column(DateTime(timezone=True))
    last_success_at = Column(DateTime(timezone=True))
    last_error_at = Column(DateTime(timezone=True))
    last_error_message = Column(Text)
    consecutive_failures = Column(Integer, default=0)

    # Metadata
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))

    # Relationships
    integration = relationship("Integration", back_populates="connections")
    credential = relationship("Credential", back_populates="connections")
    sync_jobs = relationship("SyncJob", back_populates="connection", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="connection", cascade="all, delete-orphan")
    field_mappings = relationship("FieldMapping", back_populates="connection", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_connection_user_integration', 'user_id', 'integration_id'),
    )

    def __repr__(self) -> str:
        return f"<Connection(id={self.id}, name='{self.name}', status='{self.status.value}')>"


class Credential(Base):
    """
    Stores encrypted credentials for integrations.

    Credentials are encrypted at rest and only decrypted when needed
    for API calls. Supports various authentication methods.
    """
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, index=True)
    auth_type = Column(Enum(AuthType), nullable=False)

    # Encrypted credential data
    encrypted_data = Column(Text, nullable=False)
    encryption_key_id = Column(String(100))  # For key rotation

    # OAuth-specific fields
    access_token_encrypted = Column(Text)
    refresh_token_encrypted = Column(Text)
    token_expires_at = Column(DateTime(timezone=True))
    token_type = Column(String(50))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True))

    # Relationships
    connections = relationship("Connection", back_populates="credential")

    def encrypt_data(self, data: Dict[str, Any], key: bytes) -> None:
        """Encrypt credential data."""
        fernet = Fernet(key)
        json_data = json.dumps(data)
        self.encrypted_data = fernet.encrypt(json_data.encode()).decode()

    def decrypt_data(self, key: bytes) -> Dict[str, Any]:
        """Decrypt credential data."""
        fernet = Fernet(key)
        decrypted = fernet.decrypt(self.encrypted_data.encode()).decode()
        return json.loads(decrypted)

    def __repr__(self) -> str:
        return f"<Credential(id={self.id}, auth_type='{self.auth_type.value}')>"


class SyncJob(Base):
    """
    Represents a data synchronization job between systems.

    Tracks the execution of sync operations, including status,
    progress, errors, and metrics.
    """
    __tablename__ = "sync_jobs"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=False, index=True)

    # Job details
    name = Column(String(255))
    direction = Column(Enum(SyncDirection), nullable=False)
    status = Column(Enum(SyncStatus), default=SyncStatus.PENDING, index=True)

    # Sync configuration
    entity_type = Column(String(100))  # e.g., 'contact', 'deal', 'task'
    sync_config = Column(JSON, default={})
    filters = Column(JSON, default={})
    field_mapping_id = Column(Integer, ForeignKey("field_mappings.id"))

    # Execution tracking
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    next_retry_at = Column(DateTime(timezone=True))
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Progress metrics
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    skipped_records = Column(Integer, default=0)

    # Performance metrics
    duration_seconds = Column(Float)
    records_per_second = Column(Float)
    api_calls_made = Column(Integer, default=0)

    # Error tracking
    error_message = Column(Text)
    error_details = Column(JSON)
    failed_record_ids = Column(JSON, default=[])

    # Scheduling
    is_scheduled = Column(Boolean, default=False)
    schedule_cron = Column(String(100))
    last_run_at = Column(DateTime(timezone=True))

    # Metadata
    celery_task_id = Column(String(255), index=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    connection = relationship("Connection", back_populates="sync_jobs")
    field_mapping = relationship("FieldMapping", back_populates="sync_jobs")
    sync_logs = relationship("SyncLog", back_populates="sync_job", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_sync_status_created', 'status', 'created_at'),
        Index('idx_sync_connection_status', 'connection_id', 'status'),
    )

    def calculate_metrics(self) -> None:
        """Calculate job metrics after completion."""
        if self.started_at and self.completed_at:
            delta = (self.completed_at - self.started_at).total_seconds()
            self.duration_seconds = delta
            if delta > 0 and self.processed_records > 0:
                self.records_per_second = self.processed_records / delta

    def __repr__(self) -> str:
        return f"<SyncJob(id={self.id}, status='{self.status.value}', records={self.processed_records}/{self.total_records})>"


class SyncLog(Base):
    """
    Detailed logs for sync job execution.

    Provides granular tracking of individual record processing,
    errors, and transformations during sync operations.
    """
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    sync_job_id = Column(Integer, ForeignKey("sync_jobs.id"), nullable=False, index=True)

    # Log details
    level = Column(String(20))  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text)
    record_id = Column(String(255))
    record_type = Column(String(100))

    # Details
    details = Column(JSON)
    stack_trace = Column(Text)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    sync_job = relationship("SyncJob", back_populates="sync_logs")

    __table_args__ = (
        Index('idx_synclog_job_level', 'sync_job_id', 'level'),
    )

    def __repr__(self) -> str:
        return f"<SyncLog(id={self.id}, level='{self.level}', message='{self.message[:50]}')>"


class Webhook(Base):
    """
    Manages webhook configurations and deliveries.

    Supports both incoming webhooks (from third-party services)
    and outgoing webhooks (to notify external systems).
    """
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=False, index=True)

    # Webhook details
    name = Column(String(255))
    url = Column(String(1000))
    method = Column(String(10), default="POST")

    # Configuration
    events = Column(JSON, default=[])  # Events to listen for
    is_incoming = Column(Boolean, default=False)  # True for receiving, False for sending
    is_active = Column(Boolean, default=True, index=True)

    # Security
    secret = Column(String(255))  # For signature validation
    signature_header = Column(String(100))  # Header name for signature
    signature_algorithm = Column(String(50))  # e.g., 'sha256', 'sha1'

    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)
    timeout_seconds = Column(Integer, default=30)

    # Headers
    custom_headers = Column(JSON, default={})

    # Status tracking
    last_triggered_at = Column(DateTime(timezone=True))
    last_success_at = Column(DateTime(timezone=True))
    last_failure_at = Column(DateTime(timezone=True))
    last_error_message = Column(Text)
    consecutive_failures = Column(Integer, default=0)
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    connection = relationship("Connection", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Webhook(id={self.id}, name='{self.name}', url='{self.url}')>"


class WebhookDelivery(Base):
    """
    Tracks individual webhook delivery attempts.

    Stores the payload, response, timing, and retry information
    for each webhook delivery.
    """
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id"), nullable=False, index=True)

    # Delivery details
    status = Column(Enum(WebhookStatus), default=WebhookStatus.PENDING, index=True)
    event_type = Column(String(100))

    # Request
    payload = Column(JSON)
    headers = Column(JSON)

    # Response
    response_status_code = Column(Integer)
    response_body = Column(Text)
    response_headers = Column(JSON)

    # Timing
    attempted_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_ms = Column(Integer)

    # Retry tracking
    retry_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime(timezone=True))

    # Error details
    error_message = Column(Text)
    error_details = Column(JSON)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    webhook = relationship("Webhook", back_populates="deliveries")

    __table_args__ = (
        Index('idx_delivery_webhook_status', 'webhook_id', 'status'),
        Index('idx_delivery_retry', 'status', 'next_retry_at'),
    )

    def __repr__(self) -> str:
        return f"<WebhookDelivery(id={self.id}, status='{self.status.value}', event='{self.event_type}')>"


class FieldMapping(Base):
    """
    Defines field mappings between systems for data transformation.

    Maps fields from source system to target system with optional
    transformation rules and validation.
    """
    __tablename__ = "field_mappings"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=False, index=True)

    # Mapping details
    name = Column(String(255))
    description = Column(Text)
    entity_type = Column(String(100))  # e.g., 'contact', 'deal'
    direction = Column(Enum(SyncDirection), nullable=False)

    # Mapping configuration
    mappings = Column(JSON, default={})  # {source_field: target_field}
    transformations = Column(JSON, default={})  # {field: {type: 'transform', rule: '...'}}
    default_values = Column(JSON, default={})

    # Validation
    required_fields = Column(JSON, default=[])
    validation_rules = Column(JSON, default={})

    # AI-assisted mapping
    ai_suggested = Column(Boolean, default=False)
    ai_confidence = Column(Float)

    # Status
    is_active = Column(Boolean, default=True)
    is_template = Column(Boolean, default=False)

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    connection = relationship("Connection", back_populates="field_mappings")
    sync_jobs = relationship("SyncJob", back_populates="field_mapping")

    def __repr__(self) -> str:
        return f"<FieldMapping(id={self.id}, name='{self.name}', entity='{self.entity_type}')>"


class RateLimitTracker(Base):
    """
    Tracks API rate limit usage for connections.

    Monitors request counts, timing, and enforces rate limits
    to prevent API quota exhaustion.
    """
    __tablename__ = "rate_limit_trackers"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=False, index=True)

    # Rate limit details
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    request_count = Column(Integer, default=0)
    limit = Column(Integer, nullable=False)

    # Status
    is_throttled = Column(Boolean, default=False)
    throttle_until = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_ratelimit_window', 'connection_id', 'window_start', 'window_end'),
        UniqueConstraint('connection_id', 'window_start', name='uq_connection_window'),
    )

    def __repr__(self) -> str:
        return f"<RateLimitTracker(id={self.id}, count={self.request_count}/{self.limit})>"


class IntegrationMetric(Base):
    """
    Stores performance and usage metrics for integrations.

    Tracks API performance, error rates, and usage patterns
    for monitoring and analytics.
    """
    __tablename__ = "integration_metrics"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=False, index=True)

    # Metric details
    metric_type = Column(String(100), nullable=False)  # api_call, sync, error, etc.
    metric_name = Column(String(255))
    value = Column(Float)

    # Dimensions
    dimensions = Column(JSON, default={})

    # Timing
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index('idx_metric_type_time', 'metric_type', 'timestamp'),
        Index('idx_metric_connection_type', 'connection_id', 'metric_type', 'timestamp'),
    )

    def __repr__(self) -> str:
        return f"<IntegrationMetric(id={self.id}, type='{self.metric_type}', value={self.value})>"


# Placeholder for foreign key relationships (to be replaced with actual NEXUS models)
class User(Base):
    """Placeholder for NEXUS user model."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Organization(Base):
    """Placeholder for NEXUS organization model."""
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
