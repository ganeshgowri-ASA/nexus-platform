"""Metric models for tracking experiment goals and outcomes."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modules.ab_testing.models.base import Base

if TYPE_CHECKING:
    from modules.ab_testing.models.experiment import Experiment


class MetricType(str, enum.Enum):
    """Metric type enumeration."""

    CONVERSION = "conversion"  # Binary conversion (e.g., signup, purchase)
    REVENUE = "revenue"  # Monetary value
    ENGAGEMENT = "engagement"  # Continuous metric (e.g., time on site, page views)
    CUSTOM = "custom"  # Custom metric type


class Metric(Base):
    """
    Metric model representing a goal or KPI for an experiment.

    Attributes:
        experiment_id: Foreign key to parent experiment
        name: Metric name
        description: Detailed description
        type: Type of metric (conversion, revenue, etc.)
        is_primary: Whether this is the primary metric for the experiment
        goal_value: Target/goal value for this metric (optional)
        metadata: Additional metadata as JSON
        experiment: Parent experiment relationship
        events: List of metric events recorded
    """

    __tablename__ = "metrics"

    # Foreign Keys
    experiment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic Information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metric Configuration
    type: Mapped[MetricType] = mapped_column(
        Enum(MetricType),
        default=MetricType.CONVERSION,
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    goal_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    experiment: Mapped["Experiment"] = relationship(
        "Experiment",
        back_populates="metrics",
    )

    events: Mapped[List["MetricEvent"]] = relationship(
        "MetricEvent",
        back_populates="metric",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation of the metric."""
        primary_str = " (Primary)" if self.is_primary else ""
        return f"<Metric(id={self.id}, name='{self.name}'{primary_str})>"


class MetricEvent(Base):
    """
    MetricEvent model representing individual metric measurements.

    Attributes:
        metric_id: Foreign key to parent metric
        participant_id: ID of the participant who triggered this event
        variant_id: ID of the variant the participant was assigned to
        value: Metric value (e.g., 1 for conversion, dollar amount for revenue)
        timestamp: When the event occurred
        properties: Additional event properties as JSON
        metric: Parent metric relationship
    """

    __tablename__ = "metric_events"

    # Foreign Keys
    metric_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("metrics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    variant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Event Data
    value: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
    properties: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    metric: Mapped["Metric"] = relationship(
        "Metric",
        back_populates="events",
    )

    def __repr__(self) -> str:
        """String representation of the metric event."""
        return (
            f"<MetricEvent(id={self.id}, metric_id={self.metric_id}, "
            f"value={self.value})>"
        )
