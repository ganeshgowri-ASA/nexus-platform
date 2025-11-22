"""
Document-related Pydantic schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class DocumentBase(BaseModel):
    """Base document schema"""

    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., description="Document content")
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[list[str]] = Field(default_factory=list)
    is_public: bool = False
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DocumentCreate(DocumentBase):
    """Schema for document creation"""

    pass


class DocumentUpdate(BaseModel):
    """Schema for document update"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[list[str]] = None
    is_public: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseModel):
    """Schema for document response"""

    id: int
    title: str
    content: str
    category: Optional[str]
    tags: list[str]
    is_public: bool
    metadata: Dict[str, Any]
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    version: int = Field(default=1, description="Document version number")

    model_config = ConfigDict(from_attributes=True)


class DocumentSearch(BaseModel):
    """Schema for document search"""

    query: str = Field(..., min_length=1)
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    is_public: Optional[bool] = None
    owner_id: Optional[int] = None
