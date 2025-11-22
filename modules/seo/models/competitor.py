"""
Competitor analysis models.

Models for storing competitor data and comparative metrics.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    BigInteger,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modules.seo.config.database import Base
from .base import TimestampMixin


class Competitor(Base, TimestampMixin):
    """
    Competitor model.

    Stores competitor domains and basic information.
    """

    __tablename__ = "competitors"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    your_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Your domain",
    )

    competitor_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Competitor domain",
    )

    name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Competitor name",
    )

    # Relationships
    keywords: Mapped[list["CompetitorKeyword"]] = relationship(
        "CompetitorKeyword",
        back_populates="competitor",
        cascade="all, delete-orphan",
    )

    metrics: Mapped[list["CompetitorMetric"]] = relationship(
        "CompetitorMetric",
        back_populates="competitor",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_competitor_your_competitor", "your_domain", "competitor_domain"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Competitor(id={self.id}, domain='{self.competitor_domain}')>"


class CompetitorKeyword(Base, TimestampMixin):
    """
    Keywords where competitors rank.

    Stores keywords that competitors rank for.
    """

    __tablename__ = "competitor_keywords"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    competitor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    keyword: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        doc="Keyword",
    )

    # Your ranking
    your_position: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Your ranking position",
    )

    # Competitor ranking
    competitor_position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        doc="Competitor ranking position",
    )

    competitor_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Competitor ranking URL",
    )

    # Keyword metrics
    search_volume: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        doc="Monthly search volume",
    )

    keyword_difficulty: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Keyword difficulty",
    )

    # Opportunity score
    opportunity_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Opportunity score for targeting this keyword",
    )

    # Relationships
    competitor: Mapped["Competitor"] = relationship(
        "Competitor",
        back_populates="keywords",
    )

    __table_args__ = (
        Index("ix_competitor_keyword", "competitor_id", "keyword"),
        Index("ix_competitor_position", "competitor_position"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<CompetitorKeyword(keyword='{self.keyword}', "
            f"position={self.competitor_position})>"
        )


class CompetitorMetric(Base, TimestampMixin):
    """
    Competitor metrics over time.

    Tracks competitor performance metrics.
    """

    __tablename__ = "competitor_metrics"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    competitor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Metric snapshot date",
    )

    # SEO metrics
    organic_keywords: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Number of organic keywords",
    )

    organic_traffic: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        doc="Estimated organic traffic",
    )

    organic_traffic_value: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Estimated organic traffic value in USD",
    )

    # Authority metrics
    domain_rating: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Domain rating (0-100)",
    )

    domain_authority: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Domain authority (0-100)",
    )

    # Backlink metrics
    backlinks: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        doc="Total backlinks",
    )

    referring_domains: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Number of referring domains",
    )

    # Content metrics
    indexed_pages: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Number of indexed pages",
    )

    # Relationships
    competitor: Mapped["Competitor"] = relationship(
        "Competitor",
        back_populates="metrics",
    )

    __table_args__ = (Index("ix_competitor_metric_date", "competitor_id", "date"),)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<CompetitorMetric(competitor_id={self.competitor_id}, "
            f"date={self.date})>"
        )
