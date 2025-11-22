"""
Reporting models.

Models for SEO reports and analytics.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
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


class ReportType(str, enum.Enum):
    """Report type enumeration."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    CUSTOM = "custom"


class ReportFormat(str, enum.Enum):
    """Report format enumeration."""

    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    CSV = "csv"


class Report(Base, TimestampMixin):
    """
    SEO report model.

    Stores SEO report metadata and data.
    """

    __tablename__ = "reports"

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

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Report title",
    )

    report_type: Mapped[ReportType] = mapped_column(
        SQLEnum(ReportType),
        nullable=False,
        index=True,
        doc="Report type",
    )

    report_format: Mapped[ReportFormat] = mapped_column(
        SQLEnum(ReportFormat),
        default=ReportFormat.HTML,
        nullable=False,
        doc="Report format",
    )

    # Date range
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Report start date",
    )

    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Report end date",
    )

    # Generation
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When report was generated",
    )

    generated_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="User who generated report",
    )

    # Summary metrics
    summary_data: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON object with summary metrics",
    )

    # File info
    file_path: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Path to generated report file",
    )

    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Report file size in bytes",
    )

    # Relationships
    sections: Mapped[list["ReportSection"]] = relationship(
        "ReportSection",
        back_populates="report",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_report_domain_dates", "domain", "start_date", "end_date"),
        Index("ix_report_type", "report_type"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Report(id={self.id}, domain='{self.domain}', "
            f"type={self.report_type.value})>"
        )


class ReportSection(Base, TimestampMixin):
    """
    Report section model.

    Individual sections within a report.
    """

    __tablename__ = "report_sections"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    report_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    section_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Section type: keywords, rankings, audit, backlinks, etc.",
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Section title",
    )

    order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Section order in report",
    )

    # Content
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Section content (HTML or markdown)",
    )

    data: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON object with section data",
    )

    # Charts and visualizations
    charts: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of chart configurations",
    )

    # Relationships
    report: Mapped["Report"] = relationship(
        "Report",
        back_populates="sections",
    )

    __table_args__ = (
        Index("ix_section_report_order", "report_id", "order"),
        Index("ix_section_type", "section_type"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ReportSection(id={self.id}, report_id={self.report_id}, "
            f"type='{self.section_type}')>"
        )
