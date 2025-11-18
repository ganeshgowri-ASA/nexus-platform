"""
Technical SEO models.

Models for technical SEO checks and issues.
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


class CheckStatus(str, enum.Enum):
    """Technical check status."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    INFO = "info"


class TechnicalCheck(Base, TimestampMixin):
    """
    Technical SEO check model.

    Stores technical SEO audit results.
    """

    __tablename__ = "technical_checks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Domain being checked",
    )

    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When check was performed",
    )

    # Performance metrics
    page_speed_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="PageSpeed score (0-100)",
    )

    first_contentful_paint: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="FCP in seconds",
    )

    largest_contentful_paint: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="LCP in seconds",
    )

    cumulative_layout_shift: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="CLS score",
    )

    time_to_interactive: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="TTI in seconds",
    )

    # Mobile friendliness
    is_mobile_friendly: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        doc="Mobile friendly check",
    )

    mobile_usability_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Mobile usability score",
    )

    # HTTPS and security
    has_https: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="HTTPS enabled",
    )

    ssl_certificate_valid: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        doc="SSL certificate validity",
    )

    has_hsts: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="HSTS header present",
    )

    # Structured data
    has_structured_data: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Structured data present",
    )

    structured_data_types: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of structured data types",
    )

    # Robots and indexing
    has_robots_txt: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="robots.txt present",
    )

    robots_txt_valid: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        doc="robots.txt is valid",
    )

    has_sitemap: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Sitemap present",
    )

    sitemap_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Sitemap URL",
    )

    # Canonical and hreflang
    has_canonical: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Canonical tags present",
    )

    has_hreflang: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Hreflang tags present",
    )

    # Overall score
    technical_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Overall technical SEO score (0-100)",
    )

    # Relationships
    issues: Mapped[list["TechnicalIssue"]] = relationship(
        "TechnicalIssue",
        back_populates="check",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("ix_technical_domain_checked", "domain", "checked_at"),)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<TechnicalCheck(id={self.id}, domain='{self.domain}', "
            f"score={self.technical_score})>"
        )


class TechnicalIssue(Base, TimestampMixin):
    """
    Technical SEO issues.

    Individual technical issues found during checks.
    """

    __tablename__ = "technical_issues"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    check_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("technical_checks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[CheckStatus] = mapped_column(
        SQLEnum(CheckStatus),
        nullable=False,
        index=True,
        doc="Issue status",
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Issue category: performance, security, mobile, etc.",
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Issue title",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Issue description",
    )

    recommendation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Fix recommendation",
    )

    impact: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Issue impact: low, medium, high",
    )

    # Relationships
    check: Mapped["TechnicalCheck"] = relationship(
        "TechnicalCheck",
        back_populates="issues",
    )

    __table_args__ = (
        Index("ix_technical_issue_status", "check_id", "status"),
        Index("ix_technical_issue_category", "category"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<TechnicalIssue(id={self.id}, status={self.status.value}, "
            f"title='{self.title[:50]}')>"
        )
