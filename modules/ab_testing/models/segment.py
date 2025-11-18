"""Segment models for targeting specific user groups."""

import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modules.ab_testing.models.base import Base

if TYPE_CHECKING:
    from modules.ab_testing.models.experiment import Experiment


class SegmentOperator(str, enum.Enum):
    """Operators for segment conditions."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    REGEX = "regex"


class Segment(Base):
    """
    Segment model for defining target audiences.

    Segments allow experiments to target specific user groups based on
    various conditions (demographics, behavior, properties, etc.).

    Attributes:
        name: Segment name
        description: Detailed description
        conditions: List of conditions that define this segment
        experiments: List of experiments using this segment
    """

    __tablename__ = "segments"

    # Basic Information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    conditions: Mapped[List["SegmentCondition"]] = relationship(
        "SegmentCondition",
        back_populates="segment",
        cascade="all, delete-orphan",
    )

    experiments: Mapped[List["Experiment"]] = relationship(
        "Experiment",
        secondary="experiment_segments",
        back_populates="segments",
    )

    def __repr__(self) -> str:
        """String representation of the segment."""
        return f"<Segment(id={self.id}, name='{self.name}')>"


class SegmentCondition(Base):
    """
    SegmentCondition model for defining segment rules.

    Attributes:
        segment_id: Foreign key to parent segment
        property_name: Name of the property to evaluate (e.g., "age", "country")
        operator: Comparison operator
        value: Value to compare against (stored as JSON for flexibility)
        segment: Parent segment relationship
    """

    __tablename__ = "segment_conditions"

    # Foreign Keys
    segment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("segments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Condition Details
    property_name: Mapped[str] = mapped_column(String(255), nullable=False)
    operator: Mapped[SegmentOperator] = mapped_column(
        Enum(SegmentOperator),
        nullable=False,
    )
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Relationships
    segment: Mapped["Segment"] = relationship(
        "Segment",
        back_populates="conditions",
    )

    def __repr__(self) -> str:
        """String representation of the segment condition."""
        return (
            f"<SegmentCondition(id={self.id}, "
            f"property='{self.property_name}', "
            f"operator={self.operator})>"
        )

    def evaluate(self, properties: dict) -> bool:
        """
        Evaluate this condition against participant properties.

        Args:
            properties: Dictionary of participant properties

        Returns:
            bool: True if condition is met, False otherwise
        """
        if self.property_name not in properties:
            return False

        property_value = properties[self.property_name]
        condition_value = self.value.get("value")

        if self.operator == SegmentOperator.EQUALS:
            return property_value == condition_value
        elif self.operator == SegmentOperator.NOT_EQUALS:
            return property_value != condition_value
        elif self.operator == SegmentOperator.GREATER_THAN:
            return property_value > condition_value
        elif self.operator == SegmentOperator.LESS_THAN:
            return property_value < condition_value
        elif self.operator == SegmentOperator.GREATER_THAN_OR_EQUAL:
            return property_value >= condition_value
        elif self.operator == SegmentOperator.LESS_THAN_OR_EQUAL:
            return property_value <= condition_value
        elif self.operator == SegmentOperator.CONTAINS:
            return condition_value in property_value
        elif self.operator == SegmentOperator.NOT_CONTAINS:
            return condition_value not in property_value
        elif self.operator == SegmentOperator.IN:
            return property_value in condition_value
        elif self.operator == SegmentOperator.NOT_IN:
            return property_value not in condition_value
        elif self.operator == SegmentOperator.REGEX:
            import re
            return bool(re.search(condition_value, str(property_value)))

        return False
