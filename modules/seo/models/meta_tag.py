"""
Meta tag models.

Models for meta tag optimization and management.
"""

from typing import Optional

from sqlalchemy import Boolean, Float, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from modules.seo.config.database import Base
from .base import TimestampMixin


class MetaTag(Base, TimestampMixin):
    """
    Meta tag model.

    Stores and manages meta tags for pages.
    """

    __tablename__ = "meta_tags"

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
        doc="Page URL",
    )

    # Basic meta tags
    title: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Page title",
    )

    meta_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Meta description",
    )

    meta_keywords: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Meta keywords (deprecated but still used)",
    )

    # Open Graph tags
    og_title: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Open Graph title",
    )

    og_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Open Graph description",
    )

    og_image: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Open Graph image URL",
    )

    og_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Open Graph type",
    )

    og_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Open Graph URL",
    )

    # Twitter Card tags
    twitter_card: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Twitter card type",
    )

    twitter_title: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Twitter title",
    )

    twitter_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Twitter description",
    )

    twitter_image: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Twitter image URL",
    )

    twitter_site: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Twitter site handle",
    )

    # Robots meta tag
    robots: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Robots meta tag value",
    )

    # Canonical
    canonical_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Canonical URL",
    )

    # Validation
    is_optimized: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether meta tags are optimized",
    )

    optimization_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Meta tag optimization score (0-100)",
    )

    issues: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of meta tag issues",
    )

    __table_args__ = (
        Index("ix_meta_domain_url", "domain", "url", mysql_length={"url": 255}),
        Index("ix_meta_optimized", "is_optimized"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<MetaTag(id={self.id}, url='{self.url[:50]}', "
            f"optimized={self.is_optimized})>"
        )
