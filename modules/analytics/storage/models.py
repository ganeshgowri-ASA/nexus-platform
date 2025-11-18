"""
ORM Models

SQLAlchemy ORM models for analytics entities.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from modules.analytics.storage.database import Base


class EventORM(Base):
    """Event ORM model."""

    __tablename__ = "analytics_events"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    properties = Column(JSON, default={})

    # User and session tracking
    user_id = Column(String(36), index=True)
    session_id = Column(String(36), index=True)

    # Context
    module = Column(String(100), index=True)
    page_url = Column(String(2048))
    page_title = Column(String(255))
    referrer = Column(String(2048))

    # Technical details
    user_agent = Column(String(512))
    ip_address = Column(String(45))
    country = Column(String(2), index=True)
    city = Column(String(100))
    device_type = Column(String(50), index=True)
    browser = Column(String(50))
    os = Column(String(50))

    # Timestamps
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Processing
    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime)

    __table_args__ = (
        Index("ix_events_user_timestamp", "user_id", "timestamp"),
        Index("ix_events_session_timestamp", "session_id", "timestamp"),
        Index("ix_events_type_timestamp", "event_type", "timestamp"),
        Index("ix_events_module_timestamp", "module", "timestamp"),
    )


class MetricORM(Base):
    """Metric ORM model."""

    __tablename__ = "analytics_metrics"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    dimensions = Column(JSON, default={})
    period = Column(String(20), index=True)
    module = Column(String(100), index=True)

    # Timestamps
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_metrics_name_timestamp", "name", "timestamp"),
        Index("ix_metrics_type_timestamp", "metric_type", "timestamp"),
        Index("ix_metrics_name_period_timestamp", "name", "period", "timestamp"),
    )


class UserORM(Base):
    """User ORM model."""

    __tablename__ = "analytics_users"

    id = Column(String(36), primary_key=True)
    external_id = Column(String(255), unique=True, index=True)
    email = Column(String(255), index=True)
    name = Column(String(255))
    properties = Column(JSON, default={})

    # Analytics
    first_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_sessions = Column(Integer, default=0)
    total_events = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    lifetime_value = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sessions = relationship("SessionORM", back_populates="user", lazy="dynamic")
    conversions = relationship("GoalConversionORM", back_populates="user", lazy="dynamic")


class SessionORM(Base):
    """Session ORM model."""

    __tablename__ = "analytics_sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("analytics_users.id"), nullable=False, index=True)

    # Session details
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    last_activity_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, index=True)
    duration_seconds = Column(Integer)

    # Technical details
    ip_address = Column(String(45))
    user_agent = Column(String(512))
    country = Column(String(2), index=True)
    city = Column(String(100))
    device_type = Column(String(50), index=True)
    browser = Column(String(50), index=True)
    os = Column(String(50))

    # Attribution
    referrer = Column(String(2048))
    landing_page = Column(String(2048))
    utm_source = Column(String(255), index=True)
    utm_medium = Column(String(255), index=True)
    utm_campaign = Column(String(255), index=True)

    # Analytics
    page_views = Column(Integer, default=0)
    events_count = Column(Integer, default=0)
    is_bounce = Column(Boolean, default=False, index=True)
    converted = Column(Boolean, default=False, index=True)
    conversion_value = Column(Float)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("UserORM", back_populates="sessions")

    __table_args__ = (
        Index("ix_sessions_user_started", "user_id", "started_at"),
        Index("ix_sessions_started_ended", "started_at", "ended_at"),
    )


class FunnelORM(Base):
    """Funnel ORM model."""

    __tablename__ = "analytics_funnels"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    enabled = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    steps = relationship("FunnelStepORM", back_populates="funnel", cascade="all, delete-orphan", order_by="FunnelStepORM.order")


class FunnelStepORM(Base):
    """Funnel step ORM model."""

    __tablename__ = "analytics_funnel_steps"

    id = Column(String(36), primary_key=True)
    funnel_id = Column(String(36), ForeignKey("analytics_funnels.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    event_type = Column(String(50), nullable=False)
    order = Column(Integer, nullable=False)
    description = Column(Text)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    funnel = relationship("FunnelORM", back_populates="steps")

    __table_args__ = (
        UniqueConstraint("funnel_id", "order", name="uq_funnel_step_order"),
    )


class CohortORM(Base):
    """Cohort ORM model."""

    __tablename__ = "analytics_cohorts"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    cohort_type = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    criteria = Column(JSON, nullable=False)
    period = Column(String(20), default="day")
    user_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class GoalORM(Base):
    """Goal ORM model."""

    __tablename__ = "analytics_goals"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    event_type = Column(String(50), nullable=False, index=True)
    conditions = Column(JSON, default={})
    value = Column(Float)
    enabled = Column(Boolean, default=True, index=True)

    # Analytics
    total_conversions = Column(Integer, default=0)
    total_value = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    conversions = relationship("GoalConversionORM", back_populates="goal", lazy="dynamic")


class GoalConversionORM(Base):
    """Goal conversion ORM model."""

    __tablename__ = "analytics_goal_conversions"

    id = Column(String(36), primary_key=True)
    goal_id = Column(String(36), ForeignKey("analytics_goals.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("analytics_users.id"), nullable=False, index=True)
    session_id = Column(String(36), index=True)
    event_id = Column(String(36), nullable=False)
    value = Column(Float)
    properties = Column(JSON, default={})

    # Timestamps
    converted_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    goal = relationship("GoalORM", back_populates="conversions")
    user = relationship("UserORM", back_populates="conversions")

    __table_args__ = (
        Index("ix_conversions_goal_date", "goal_id", "converted_at"),
        Index("ix_conversions_user_date", "user_id", "converted_at"),
    )


class ABTestORM(Base):
    """A/B test ORM model."""

    __tablename__ = "analytics_ab_tests"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    hypothesis = Column(Text)
    goal_metric = Column(String(255), nullable=False)
    variants = Column(JSON, nullable=False)  # List of variant names
    traffic_split = Column(JSON, nullable=False)  # Dict of variant: percentage
    status = Column(String(20), default="draft", index=True)

    # Test period
    start_date = Column(DateTime, index=True)
    end_date = Column(DateTime, index=True)
    min_sample_size = Column(Integer, default=1000)

    # Results
    total_participants = Column(Integer, default=0)
    winner = Column(String(50))
    confidence_level = Column(Float)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignments = relationship("ABTestAssignmentORM", back_populates="test", lazy="dynamic")


class ABTestAssignmentORM(Base):
    """A/B test assignment ORM model."""

    __tablename__ = "analytics_ab_test_assignments"

    id = Column(String(36), primary_key=True)
    test_id = Column(String(36), ForeignKey("analytics_ab_tests.id"), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    variant = Column(String(50), nullable=False, index=True)

    # Timestamps
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    test = relationship("ABTestORM", back_populates="assignments")

    __table_args__ = (
        UniqueConstraint("test_id", "user_id", name="uq_test_user_assignment"),
        Index("ix_assignments_test_variant", "test_id", "variant"),
    )


class DashboardORM(Base):
    """Dashboard ORM model."""

    __tablename__ = "analytics_dashboards"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    config = Column(JSON, nullable=False)  # Dashboard configuration
    is_public = Column(Boolean, default=False)
    owner_id = Column(String(36), index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExportJobORM(Base):
    """Export job ORM model."""

    __tablename__ = "analytics_export_jobs"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    export_type = Column(String(50), nullable=False, index=True)  # events, metrics, etc.
    format = Column(String(20), nullable=False)  # csv, json, excel, pdf
    query_params = Column(JSON)  # Query parameters used for export

    # Status
    status = Column(String(20), default="pending", index=True)
    file_path = Column(String(1024))
    file_size = Column(Integer)
    row_count = Column(Integer)
    error_message = Column(Text)

    # User
    user_id = Column(String(36), index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime, index=True)  # When export file expires

    __table_args__ = (
        Index("ix_exports_user_created", "user_id", "created_at"),
        Index("ix_exports_status_created", "status", "created_at"),
    )
