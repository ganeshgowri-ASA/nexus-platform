"""
Rank tracking models.

Models for storing search ranking data and history.
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


class Ranking(Base, TimestampMixin):
    """
    Current ranking positions for keywords.

    Stores the current ranking position for keywords across
    different search engines and locations.
    """

    __tablename__ = "rankings"

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
        doc="Associated keyword ID",
    )

    domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Domain being tracked",
    )

    url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Ranking URL",
    )

    # Ranking data
    position: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        doc="Current ranking position",
    )

    previous_position: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Previous ranking position",
    )

    position_change: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Change in position (negative = improvement)",
    )

    # Search engine and location
    search_engine: Mapped[str] = mapped_column(
        String(50),
        default="google",
        nullable=False,
        index=True,
        doc="Search engine: google, bing, yahoo, etc.",
    )

    location: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Geographic location for search",
    )

    device: Mapped[str] = mapped_column(
        String(20),
        default="desktop",
        nullable=False,
        doc="Device type: desktop, mobile, tablet",
    )

    # SERP data
    serp_features: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of SERP features present",
    )

    featured_snippet: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether URL has featured snippet",
    )

    # Metrics
    estimated_traffic: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Estimated traffic from this ranking",
    )

    ctr: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Click-through rate",
    )

    # Tracking metadata
    last_checked: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Last time ranking was checked",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether tracking is active",
    )

    # Relationships
    keyword: Mapped["Keyword"] = relationship(
        "Keyword",
        back_populates="rankings",
    )

    history: Mapped[list["RankingHistory"]] = relationship(
        "RankingHistory",
        back_populates="ranking",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_ranking_keyword_domain", "keyword_id", "domain"),
        Index("ix_ranking_position", "position"),
        Index("ix_ranking_last_checked", "last_checked"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Ranking(id={self.id}, domain='{self.domain}', "
            f"position={self.position})>"
        )


class RankingHistory(Base, TimestampMixin):
    """
    Historical ranking data.

    Stores historical ranking positions for trend analysis.
    """

    __tablename__ = "ranking_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    ranking_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rankings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Date of ranking snapshot",
    )

    position: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Ranking position on this date",
    )

    url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Ranking URL on this date",
    )

    serp_features: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="SERP features present",
    )

    estimated_traffic: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Relationships
    ranking: Mapped["Ranking"] = relationship(
        "Ranking",
        back_populates="history",
    )

    __table_args__ = (Index("ix_ranking_history_date", "ranking_id", "date"),)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<RankingHistory(ranking_id={self.ranking_id}, "
            f"date={self.date}, position={self.position})>"
        )
