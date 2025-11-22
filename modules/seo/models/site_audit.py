"""
Site audit models.

Models for storing site audit data, issues, and page analysis.
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


class AuditStatus(str, enum.Enum):
    """Audit status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueSeverity(str, enum.Enum):
    """Issue severity levels."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class SiteAudit(Base, TimestampMixin):
    """
    Site audit model.

    Stores site audit metadata and overall results.
    """

    __tablename__ = "site_audits"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Domain being audited",
    )

    start_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Starting URL for crawl",
    )

    # Audit status
    status: Mapped[AuditStatus] = mapped_column(
        SQLEnum(AuditStatus),
        default=AuditStatus.PENDING,
        nullable=False,
        index=True,
        doc="Current audit status",
    )

    # Audit metrics
    pages_crawled: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of pages crawled",
    )

    pages_with_issues: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of pages with issues",
    )

    total_issues: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total issues found",
    )

    critical_issues: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    errors: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    warnings: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Health score
    health_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Overall site health score (0-100)",
    )

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When audit started",
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When audit completed",
    )

    duration: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Audit duration in seconds",
    )

    # Configuration
    max_depth: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        doc="Maximum crawl depth",
    )

    max_pages: Mapped[int] = mapped_column(
        Integer,
        default=1000,
        nullable=False,
        doc="Maximum pages to crawl",
    )

    # Relationships
    issues: Mapped[list["AuditIssue"]] = relationship(
        "AuditIssue",
        back_populates="audit",
        cascade="all, delete-orphan",
    )

    pages: Mapped[list["AuditPage"]] = relationship(
        "AuditPage",
        back_populates="audit",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_audit_domain_created", "domain", "created_at"),
        Index("ix_audit_status", "status"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<SiteAudit(id={self.id}, domain='{self.domain}', "
            f"status={self.status.value})>"
        )


class AuditIssue(Base, TimestampMixin):
    """
    Issues found during site audit.

    Stores individual issues discovered during crawl.
    """

    __tablename__ = "audit_issues"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    audit_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("site_audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    page_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("audit_pages.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Issue details
    severity: Mapped[IssueSeverity] = mapped_column(
        SQLEnum(IssueSeverity),
        nullable=False,
        index=True,
        doc="Issue severity level",
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Issue category: seo, performance, accessibility, etc.",
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Issue title",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Detailed issue description",
    )

    affected_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="URL where issue was found",
    )

    # Fix information
    recommendation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="How to fix the issue",
    )

    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether issue has been resolved",
    )

    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When issue was resolved",
    )

    # Relationships
    audit: Mapped["SiteAudit"] = relationship(
        "SiteAudit",
        back_populates="issues",
    )

    page: Mapped[Optional["AuditPage"]] = relationship(
        "AuditPage",
        back_populates="issues",
    )

    __table_args__ = (
        Index("ix_issue_severity_category", "severity", "category"),
        Index("ix_issue_audit_severity", "audit_id", "severity"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AuditIssue(id={self.id}, severity={self.severity.value}, "
            f"title='{self.title[:50]}')>"
        )


class AuditPage(Base, TimestampMixin):
    """
    Individual pages analyzed during audit.

    Stores data for each page crawled during audit.
    """

    __tablename__ = "audit_pages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    audit_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("site_audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Page URL",
    )

    # HTTP response
    status_code: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        doc="HTTP status code",
    )

    # Page content
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

    h1: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="H1 heading",
    )

    word_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Word count",
    )

    # Links
    internal_links: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of internal links",
    )

    external_links: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of external links",
    )

    # Performance
    load_time: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Page load time in seconds",
    )

    page_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Page size in bytes",
    )

    # SEO
    is_indexable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether page is indexable",
    )

    canonical_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Canonical URL",
    )

    # Depth
    depth: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Crawl depth",
    )

    # Relationships
    audit: Mapped["SiteAudit"] = relationship(
        "SiteAudit",
        back_populates="pages",
    )

    issues: Mapped[list["AuditIssue"]] = relationship(
        "AuditIssue",
        back_populates="page",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_page_audit_url", "audit_id", "url", mysql_length={"url": 255}),
        Index("ix_page_status_code", "status_code"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<AuditPage(id={self.id}, url='{self.url[:50]}...')>"
