"""Transformation schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class TransformationBase(BaseModel):
    """Base transformation schema."""

    name: str = Field(..., description="Transformation name")
    description: Optional[str] = Field(None, description="Transformation description")
    category: str = Field(..., description="Transformation category")
    transformation_type: str = Field(..., description="Transformation type")
    config: Dict[str, Any] = Field(..., description="Transformation configuration")
    is_public: bool = Field(False, description="Whether the transformation is public")


class TransformationCreate(TransformationBase):
    """Schema for creating a transformation."""

    pass


class TransformationUpdate(BaseModel):
    """Schema for updating a transformation."""

    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    transformation_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None


class TransformationResponse(TransformationBase):
    """Schema for transformation response."""

    id: str
    usage_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True
