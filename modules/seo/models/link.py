"""
Link building models.

Models for link building opportunities and campaigns.
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


class OpportunityStatus(str, enum.Enum):
    """Link opportunity status."""

    IDENTIFIED = "identified"
    CONTACTED = "contacted"
    NEGOTIATING = "negotiating"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class Link(Base, TimestampMixin):
    """
    Link building link model.

    Tracks links acquired through link building campaigns.
    """

    __tablename__ = "links"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    campaign_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        doc="Associated campaign ID",
    )

    opportunity_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("link_opportunities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Associated opportunity ID",
    )

    target_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Your domain",
    )

    target_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Your URL being linked to",
    )

    source_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Source domain",
    )

    source_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Source URL containing link",
    )

    anchor_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Anchor text",
    )

    # Link status
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When link was acquired",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether link is still active",
    )

    # Metrics
    domain_rating: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Domain rating of source",
    )

    # Cost
    cost: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Cost to acquire link (if paid)",
    )

    # Relationships
    opportunity: Mapped[Optional["LinkOpportunity"]] = relationship(
        "LinkOpportunity",
        back_populates="links",
    )

    __table_args__ = (
        Index("ix_link_target_source", "target_domain", "source_domain"),
        Index("ix_link_acquired", "acquired_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Link(id={self.id}, from='{self.source_domain}', "
            f"to='{self.target_domain}')>"
        )


class LinkOpportunity(Base, TimestampMixin):
    """
    Link building opportunity.

    Tracks potential link building opportunities.
    """

    __tablename__ = "link_opportunities"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    target_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Your domain",
    )

    opportunity_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Opportunity domain",
    )

    opportunity_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Opportunity URL",
    )

    # Status
    status: Mapped[OpportunityStatus] = mapped_column(
        SQLEnum(OpportunityStatus),
        default=OpportunityStatus.IDENTIFIED,
        nullable=False,
        index=True,
        doc="Opportunity status",
    )

    # Opportunity type
    opportunity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Type: guest post, broken link, resource page, etc.",
    )

    # Metrics
    domain_rating: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Domain rating",
    )

    estimated_traffic: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Estimated monthly traffic",
    )

    relevance_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Relevance score (0-100)",
    )

    # Contact info
    contact_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Contact email",
    )

    contact_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Contact name",
    )

    # Outreach
    outreach_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether outreach email was sent",
    )

    outreach_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When outreach was sent",
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Notes about opportunity",
    )

    # Relationships
    links: Mapped[list["Link"]] = relationship(
        "Link",
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_opportunity_target_domain", "target_domain"),
        Index("ix_opportunity_status", "status"),
        Index("ix_opportunity_type", "opportunity_type"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<LinkOpportunity(id={self.id}, domain='{self.opportunity_domain}', "
            f"status={self.status.value})>"
        )
