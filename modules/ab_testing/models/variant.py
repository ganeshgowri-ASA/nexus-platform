"""Variant model for experiment variations."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modules.ab_testing.models.base import Base

if TYPE_CHECKING:
    from modules.ab_testing.models.experiment import Experiment
    from modules.ab_testing.models.participant import ParticipantVariant


class Variant(Base):
    """
    Variant model representing a single variation in an experiment.

    Attributes:
        experiment_id: Foreign key to parent experiment
        name: Variant name (e.g., "Control", "Treatment A")
        description: Detailed description of the variant
        is_control: Whether this is the control/baseline variant
        traffic_weight: Traffic allocation weight (relative to other variants)
        config: Configuration/parameters for this variant as JSON
        experiment: Parent experiment relationship
        participants: List of participants assigned to this variant
    """

    __tablename__ = "variants"

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
    is_control: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Traffic Configuration
    traffic_weight: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )

    # Variant Configuration
    config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    experiment: Mapped["Experiment"] = relationship(
        "Experiment",
        back_populates="variants",
        foreign_keys=[experiment_id],
    )

    participants: Mapped[List["ParticipantVariant"]] = relationship(
        "ParticipantVariant",
        back_populates="variant",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation of the variant."""
        control_str = " (Control)" if self.is_control else ""
        return f"<Variant(id={self.id}, name='{self.name}'{control_str})>"

    @property
    def participant_count(self) -> int:
        """Get the number of participants assigned to this variant."""
        return len(self.participants)
