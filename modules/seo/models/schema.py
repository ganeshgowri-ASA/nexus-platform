"""
Schema markup models.

Models for storing and managing structured data schema.
"""

from typing import Optional

from sqlalchemy import Integer, String, Text, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from modules.seo.config.database import Base
from .base import TimestampMixin


class SchemaMarkup(Base, TimestampMixin):
    """
    Schema markup model.

    Stores generated schema markup for pages.
    """

    __tablename__ = "schema_markups"

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

    schema_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Schema type: Article, Product, LocalBusiness, etc.",
    )

    schema_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="JSON-LD schema markup",
    )

    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether schema is valid",
    )

    validation_errors: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of validation errors",
    )

    is_deployed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether schema is deployed to page",
    )

    __table_args__ = (
        Index("ix_schema_domain_url", "domain", "url", mysql_length={"url": 255}),
        Index("ix_schema_type", "schema_type"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<SchemaMarkup(id={self.id}, type='{self.schema_type}', "
            f"url='{self.url[:50]}')>"
        )
