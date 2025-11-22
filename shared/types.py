"""
Shared type definitions for NEXUS platform.

This module contains common Pydantic models and type definitions
used across multiple modules.
"""

from typing import Generic, TypeVar, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for API requests."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    model_config = ConfigDict(frozen=True)

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """
        Create paginated response from items and parameters.

        Args:
            items: List of items for current page.
            total: Total number of items.
            page: Current page number.
            page_size: Items per page.

        Returns:
            PaginatedResponse instance.
        """
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


class FilterParams(BaseModel):
    """Generic filter parameters."""

    field: str = Field(description="Field name to filter on")
    operator: str = Field(
        default="eq",
        description="Filter operator (eq, ne, gt, lt, gte, lte, in, like)",
    )
    value: Any = Field(description="Filter value")

    model_config = ConfigDict(frozen=True)


class SortParams(BaseModel):
    """Sorting parameters."""

    field: str = Field(description="Field name to sort by")
    direction: str = Field(
        default="asc",
        description="Sort direction (asc or desc)",
    )

    model_config = ConfigDict(frozen=True)


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class APIResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool = Field(description="Whether the request was successful")
    message: Optional[str] = Field(default=None, description="Response message")
    data: Optional[Any] = Field(default=None, description="Response data")
    errors: Optional[list[str]] = Field(default=None, description="Error messages")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def success_response(
        cls,
        data: Any = None,
        message: str = "Success",
    ) -> "APIResponse":
        """Create success response."""
        return cls(success=True, message=message, data=data)

    @classmethod
    def error_response(
        cls,
        message: str = "Error",
        errors: Optional[list[str]] = None,
    ) -> "APIResponse":
        """Create error response."""
        return cls(success=False, message=message, errors=errors)


class WebhookPayload(BaseModel):
    """Generic webhook payload."""

    event: str = Field(description="Event type")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any] = Field(description="Event data")
    source: Optional[str] = Field(default=None, description="Event source")

    model_config = ConfigDict(from_attributes=True)


class MetricsSnapshot(BaseModel):
    """Generic metrics snapshot."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metrics: dict[str, float] = Field(description="Metric values")
    dimensions: Optional[dict[str, str]] = Field(
        default=None,
        description="Metric dimensions/tags",
    )

    model_config = ConfigDict(from_attributes=True)
