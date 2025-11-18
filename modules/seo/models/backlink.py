"""
Backlink analysis models.

Models for storing backlink data and metrics.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modules.seo.config.database import Base
from .base import TimestampMixin


class Backlink(Base, TimestampMixin):
    """
    Backlink model.

    Stores backlink data including source, target, and metrics.
    """

    __tablename__ = "backlinks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    target_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Target domain receiving the backlink",
    )

    target_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Target URL",
    )

    source_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Source domain of the backlink",
    )

    source_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Source URL containing the link",
    )

    # Link attributes
    anchor_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Anchor text of the link",
    )

    link_type: Mapped[str] = mapped_column(
        String(50),
        default="dofollow",
        nullable=False,
        index=True,
        doc="Link type: dofollow, nofollow, sponsored, ugc",
    )

    is_image: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether link is an image link",
    )

    # Metrics
    domain_rating: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Domain rating of source (0-100)",
    )

    page_rating: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Page rating of source (0-100)",
    )

    domain_authority: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Moz Domain Authority (0-100)",
    )

    page_authority: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Moz Page Authority (0-100)",
    )

    spam_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Spam score (0-100)",
    )

    # Traffic estimates
    estimated_traffic: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Estimated monthly traffic to source page",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether backlink is still active",
    )

    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When backlink was first discovered",
    )

    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="When backlink was last verified",
    )

    lost_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When backlink was lost",
    )

    # Relationships
    history: Mapped[list["BacklinkHistory"]] = relationship(
        "BacklinkHistory",
        back_populates="backlink",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_backlink_target_source", "target_domain", "source_domain"),
        Index("ix_backlink_active", "is_active"),
        Index("ix_backlink_first_seen", "first_seen"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Backlink(id={self.id}, from='{self.source_domain}', "
            f"to='{self.target_domain}')>"
        )


class BacklinkHistory(Base, TimestampMixin):
    """
    Historical backlink data.

    Tracks changes to backlink metrics over time.
    """

    __tablename__ = "backlink_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    backlink_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("backlinks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Date of snapshot",
    )

    # Historical metrics
    domain_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    page_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    domain_authority: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    page_authority: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    spam_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_traffic: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    backlink: Mapped["Backlink"] = relationship(
        "Backlink",
        back_populates="history",
    )

    __table_args__ = (Index("ix_backlink_history_date", "backlink_id", "date"),)

    def __repr__(self) -> str:
        """String representation."""
        return f"<BacklinkHistory(backlink_id={self.backlink_id}, date={self.date})>"
