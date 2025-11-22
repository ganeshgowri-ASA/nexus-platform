"""
Keyword research models.

Models for storing keyword data, metrics, and groups.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
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


class Keyword(Base, TimestampMixin):
    """
    Keyword model for storing keyword research data.

    Stores keyword information including search volume, difficulty,
    and related metrics.
    """

    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier",
    )

    keyword: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        doc="The keyword phrase",
    )

    domain: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="Associated domain",
    )

    # Search volume metrics
    search_volume: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        doc="Monthly search volume",
    )

    search_volume_trend: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Search volume trend (-1 to 1)",
    )

    # Difficulty metrics
    keyword_difficulty: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Keyword difficulty score (0-100)",
    )

    competition: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Competition level (0-1)",
    )

    # Cost metrics
    cpc: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Cost per click in USD",
    )

    # Intent classification
    intent: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Search intent: informational, navigational, transactional, commercial",
    )

    # SERP features
    serp_features: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of SERP features",
    )

    # Related keywords
    parent_topic: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        index=True,
        doc="Parent topic keyword",
    )

    # Status and metadata
    is_tracked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether keyword is actively tracked",
    )

    last_updated: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time metrics were updated",
    )

    # Relationships
    metrics: Mapped[list["KeywordMetric"]] = relationship(
        "KeywordMetric",
        back_populates="keyword",
        cascade="all, delete-orphan",
    )

    rankings: Mapped[list["Ranking"]] = relationship(
        "Ranking",
        back_populates="keyword",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_keyword_domain", "keyword", "domain"),
        Index("ix_keyword_difficulty", "keyword_difficulty"),
        Index("ix_search_volume", "search_volume"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Keyword(id={self.id}, keyword='{self.keyword}', volume={self.search_volume})>"


class KeywordMetric(Base, TimestampMixin):
    """
    Historical keyword metrics.

    Stores historical data for keyword metrics over time.
    """

    __tablename__ = "keyword_metrics"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    keyword_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("keywords.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Date of the metric snapshot",
    )

    search_volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    keyword_difficulty: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cpc: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    competition: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    keyword: Mapped["Keyword"] = relationship("Keyword", back_populates="metrics")

    __table_args__ = (Index("ix_keyword_metric_date", "keyword_id", "date"),)

    def __repr__(self) -> str:
        """String representation."""
        return f"<KeywordMetric(keyword_id={self.keyword_id}, date={self.date})>"


class KeywordGroup(Base, TimestampMixin):
    """
    Keyword groups for organization.

    Allows organizing keywords into logical groups or campaigns.
    """

    __tablename__ = "keyword_groups"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Group name",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Group description",
    )

    domain: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    keyword_ids: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of keyword IDs",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<KeywordGroup(id={self.id}, name='{self.name}')>"
