"""
Common schemas used across the API
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field


DataT = TypeVar("DataT")


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Generic paginated response model"""

    items: List[DataT]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Generic message response"""

    message: str
    detail: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Error response model"""

    error: str
    detail: Optional[str] = None
    status_code: int

    class Config:
        from_attributes = True
