"""
Sitemap models.

Models for sitemap generation and management.
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
    Enum as SQLEnum,
)
import enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modules.seo.config.database import Base
from .base import TimestampMixin


class ChangeFrequency(str, enum.Enum):
    """Sitemap change frequency values."""

    ALWAYS = "always"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    NEVER = "never"


class Sitemap(Base, TimestampMixin):
    """
    Sitemap model.

    Stores sitemap metadata and configuration.
    """

    __tablename__ = "sitemaps"

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

    sitemap_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Sitemap URL",
    )

    sitemap_type: Mapped[str] = mapped_column(
        String(50),
        default="url",
        nullable=False,
        doc="Sitemap type: url, video, image, news",
    )

    # Generation info
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When sitemap was generated",
    )

    url_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of URLs in sitemap",
    )

    # File info
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Sitemap file size in bytes",
    )

    is_compressed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether sitemap is gzipped",
    )

    # Status
    is_submitted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Submitted to search engines",
    )

    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When sitemap was submitted",
    )

    # Relationships
    urls: Mapped[list["SitemapUrl"]] = relationship(
        "SitemapUrl",
        back_populates="sitemap",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_sitemap_domain_generated", "domain", "generated_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Sitemap(id={self.id}, domain='{self.domain}', "
            f"urls={self.url_count})>"
        )


class SitemapUrl(Base, TimestampMixin):
    """
    Individual URLs in sitemap.

    Stores URL entries with their metadata.
    """

    __tablename__ = "sitemap_urls"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    sitemap_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sitemaps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Page URL",
    )

    lastmod: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last modification date",
    )

    changefreq: Mapped[Optional[ChangeFrequency]] = mapped_column(
        SQLEnum(ChangeFrequency),
        nullable=True,
        doc="Change frequency",
    )

    priority: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Priority (0.0-1.0)",
    )

    # Additional metadata for specific sitemap types
    image_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Image URL for image sitemaps",
    )

    video_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Video URL for video sitemaps",
    )

    # Relationships
    sitemap: Mapped["Sitemap"] = relationship(
        "Sitemap",
        back_populates="urls",
    )

    __table_args__ = (
        Index("ix_sitemap_url", "sitemap_id", "url", mysql_length={"url": 255}),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<SitemapUrl(id={self.id}, url='{self.url[:50]}')>"
