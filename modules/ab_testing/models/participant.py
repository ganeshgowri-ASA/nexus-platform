"""Participant models for tracking experiment assignments."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modules.ab_testing.models.base import Base

if TYPE_CHECKING:
    from modules.ab_testing.models.experiment import Experiment
    from modules.ab_testing.models.variant import Variant


class Participant(Base):
    """
    Participant model representing a unique user/entity in experiments.

    Attributes:
        participant_id: Unique identifier for the participant (user ID, session ID, etc.)
        properties: Additional participant properties as JSON (demographics, etc.)
    """

    __tablename__ = "participants"

    # Unique participant identifier
    participant_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # Participant Properties
    properties: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        """String representation of the participant."""
        return f"<Participant(id={self.id}, participant_id='{self.participant_id}')>"


class ParticipantVariant(Base):
    """
    ParticipantVariant model representing variant assignments.

    This is the assignment table that maps participants to specific variants
    in experiments. Each participant gets one variant per experiment.

    Attributes:
        experiment_id: Foreign key to experiment
        participant_id: Participant identifier (string)
        variant_id: Foreign key to assigned variant
        assigned_at: When the assignment was made
        metadata: Additional assignment metadata as JSON
        experiment: Parent experiment relationship
        variant: Assigned variant relationship
    """

    __tablename__ = "participant_variants"

    # Foreign Keys
    experiment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("experiments.id", ondelete="CASCADE"),
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

    # Assignment Details
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    experiment: Mapped["Experiment"] = relationship(
        "Experiment",
        back_populates="participants",
    )
    variant: Mapped["Variant"] = relationship(
        "Variant",
        back_populates="participants",
    )

    def __repr__(self) -> str:
        """String representation of the participant variant assignment."""
        return (
            f"<ParticipantVariant(experiment_id={self.experiment_id}, "
            f"participant_id='{self.participant_id}', variant_id={self.variant_id})>"
        )
