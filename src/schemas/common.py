"""
Common Pydantic schemas used across the application.

This module defines shared request and response schemas.
"""
from typing import Optional, List, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response wrapper."""
    success: bool = Field(..., description="Request success status")
    data: Optional[T] = Field(None, description="Response data")
    errors: Optional[List[Dict[str, str]]] = Field(None, description="Error messages")
    message: Optional[str] = Field(None, description="Response message")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class SortParams(BaseModel):
    """Sort parameters."""
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="Sort order")


class FilterParams(BaseModel):
    """Filter parameters."""
    filters: Optional[Dict[str, Any]] = Field(default={}, description="Filter conditions")


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current timestamp")
    database: str = Field(..., description="Database status")
    redis: str = Field(..., description="Redis status")


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    status_code: int = Field(..., description="HTTP status code")
