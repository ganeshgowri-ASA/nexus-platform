"""
Content optimization models.

Models for content analysis and optimization.
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
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modules.seo.config.database import Base
from .base import TimestampMixin


class Content(Base, TimestampMixin):
    """
    Content model.

    Stores content for analysis and optimization.
    """

    __tablename__ = "contents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Associated domain",
    )

    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Content URL",
    )

    title: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Content title",
    )

    content_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Content text",
    )

    target_keyword: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        index=True,
        doc="Target keyword for optimization",
    )

    # Relationships
    analyses: Mapped[list["ContentAnalysis"]] = relationship(
        "ContentAnalysis",
        back_populates="content",
        cascade="all, delete-orphan",
    )

    optimizations: Mapped[list["ContentOptimization"]] = relationship(
        "ContentOptimization",
        back_populates="content",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("ix_content_domain_url", "domain", "url", mysql_length={"url": 255}),)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Content(id={self.id}, url='{self.url[:50]}')>"


class ContentAnalysis(Base, TimestampMixin):
    """
    Content analysis results.

    Stores analysis results for content.
    """

    __tablename__ = "content_analyses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    content_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When analysis was performed",
    )

    # Readability metrics
    word_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Word count",
    )

    readability_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Readability score (0-100)",
    )

    sentence_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Number of sentences",
    )

    avg_sentence_length: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Average sentence length",
    )

    # Keyword metrics
    keyword_density: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Target keyword density",
    )

    keyword_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Target keyword count",
    )

    # SEO metrics
    seo_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Overall SEO score (0-100)",
    )

    # NLP analysis
    sentiment_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Sentiment score (-1 to 1)",
    )

    entities: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of extracted entities",
    )

    topics: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of identified topics",
    )

    # Relationships
    content: Mapped["Content"] = relationship(
        "Content",
        back_populates="analyses",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ContentAnalysis(content_id={self.content_id}, "
            f"score={self.seo_score})>"
        )


class ContentOptimization(Base, TimestampMixin):
    """
    Content optimization recommendations.

    AI-generated recommendations for content improvement.
    """

    __tablename__ = "content_optimizations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    content_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When recommendations were generated",
    )

    # Recommendations
    title_suggestions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of title suggestions",
    )

    meta_description_suggestions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of meta description suggestions",
    )

    heading_suggestions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON object with heading suggestions",
    )

    content_improvements: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="AI-generated content improvement suggestions",
    )

    keyword_suggestions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of related keyword suggestions",
    )

    # AI metadata
    ai_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="AI model used for optimization",
    )

    # Relationships
    content: Mapped["Content"] = relationship(
        "Content",
        back_populates="optimizations",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ContentOptimization(content_id={self.content_id}, "
            f"generated_at={self.generated_at})>"
        )
