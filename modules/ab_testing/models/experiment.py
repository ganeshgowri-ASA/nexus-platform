"""Experiment model and related enums."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
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
    from modules.ab_testing.models.metric import Metric
    from modules.ab_testing.models.participant import ParticipantVariant
    from modules.ab_testing.models.segment import Segment
    from modules.ab_testing.models.variant import Variant


class ExperimentStatus(str, enum.Enum):
    """Experiment status enumeration."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ExperimentType(str, enum.Enum):
    """Experiment type enumeration."""

    AB = "ab"  # A/B test
    MULTIVARIATE = "multivariate"  # Multivariate test
    MULTI_ARMED_BANDIT = "multi_armed_bandit"  # MAB optimization


class Experiment(Base):
    """
    Experiment model representing an A/B test or multivariate experiment.

    Attributes:
        name: Experiment name
        description: Detailed description of the experiment
        hypothesis: Hypothesis being tested
        type: Type of experiment (A/B, multivariate, etc.)
        status: Current status of the experiment
        start_date: When the experiment started
        end_date: When the experiment ended (if completed)
        target_sample_size: Target number of participants per variant
        confidence_level: Required confidence level (e.g., 0.95 for 95%)
        traffic_allocation: Overall traffic allocation percentage (0.0-1.0)
        auto_winner_enabled: Whether automatic winner selection is enabled
        winner_variant_id: ID of the winning variant (if determined)
        metadata: Additional metadata as JSON
        variants: List of variants in this experiment
        metrics: List of metrics being tracked
        segments: List of segments this experiment targets
        participants: List of participant assignments
    """

    __tablename__ = "experiments"

    # Basic Information
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hypothesis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Experiment Configuration
    type: Mapped[ExperimentType] = mapped_column(
        Enum(ExperimentType),
        default=ExperimentType.AB,
        nullable=False,
    )
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus),
        default=ExperimentStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # Timing
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Statistical Configuration
    target_sample_size: Mapped[int] = mapped_column(
        Integer,
        default=1000,
        nullable=False,
    )
    confidence_level: Mapped[float] = mapped_column(
        Float,
        default=0.95,
        nullable=False,
    )

    # Traffic Configuration
    traffic_allocation: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )

    # Winner Detection
    auto_winner_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    winner_variant_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("variants.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    variants: Mapped[List["Variant"]] = relationship(
        "Variant",
        back_populates="experiment",
        foreign_keys="Variant.experiment_id",
        cascade="all, delete-orphan",
    )

    metrics: Mapped[List["Metric"]] = relationship(
        "Metric",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )

    segments: Mapped[List["Segment"]] = relationship(
        "Segment",
        secondary="experiment_segments",
        back_populates="experiments",
    )

    participants: Mapped[List["ParticipantVariant"]] = relationship(
        "ParticipantVariant",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation of the experiment."""
        return f"<Experiment(id={self.id}, name='{self.name}', status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Check if experiment is currently active."""
        return self.status == ExperimentStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        """Check if experiment is completed."""
        return self.status == ExperimentStatus.COMPLETED

    @property
    def has_winner(self) -> bool:
        """Check if experiment has a determined winner."""
        return self.winner_variant_id is not None


# Association table for many-to-many relationship between experiments and segments
class ExperimentSegment(Base):
    """Association table linking experiments to target segments."""

    __tablename__ = "experiment_segments"

    experiment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    segment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("segments.id", ondelete="CASCADE"),
        nullable=False,
    )
