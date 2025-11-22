"""Pydantic schemas for notes module validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from .models import NoteStatus, PermissionLevel, TemplateType


# Notebook Schemas
class NotebookBase(BaseModel):
    """Base notebook schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    color: str = "#4A90E2"
    icon: str = "📓"


class NotebookCreate(NotebookBase):
    """Schema for creating a notebook."""

    pass


class NotebookUpdate(BaseModel):
    """Schema for updating a notebook."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class NotebookResponse(NotebookBase):
    """Schema for notebook response."""

    id: int
    user_id: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Section Schemas
class SectionBase(BaseModel):
    """Base section schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    order: int = 0


class SectionCreate(SectionBase):
    """Schema for creating a section."""

    notebook_id: int


class SectionUpdate(BaseModel):
    """Schema for updating a section."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    order: Optional[int] = None


class SectionResponse(SectionBase):
    """Schema for section response."""

    id: int
    notebook_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Tag Schemas
class TagBase(BaseModel):
    """Base tag schema."""

    name: str = Field(..., min_length=1, max_length=100)
    color: str = "#6B7280"


class TagCreate(TagBase):
    """Schema for creating a tag."""

    pass


class TagUpdate(BaseModel):
    """Schema for updating a tag."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = None


class TagResponse(TagBase):
    """Schema for tag response."""

    id: int
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Note Schemas
class NoteBase(BaseModel):
    """Base note schema."""

    title: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = None
    content_markdown: Optional[str] = None
    color: Optional[str] = None


class NoteCreate(NoteBase):
    """Schema for creating a note."""

    notebook_id: Optional[int] = None
    section_id: Optional[int] = None
    tags: List[str] = []
    is_favorite: bool = False
    template_id: Optional[int] = None


class NoteUpdate(BaseModel):
    """Schema for updating a note."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    content_markdown: Optional[str] = None
    notebook_id: Optional[int] = None
    section_id: Optional[int] = None
    status: Optional[NoteStatus] = None
    is_favorite: Optional[bool] = None
    is_pinned: Optional[bool] = None
    color: Optional[str] = None
    tags: Optional[List[str]] = None


class NoteResponse(NoteBase):
    """Schema for note response."""

    id: int
    user_id: str
    notebook_id: Optional[int]
    section_id: Optional[int]
    status: NoteStatus
    is_favorite: bool
    is_pinned: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime
    last_viewed_at: Optional[datetime]
    version: int
    tags: List[str] = []
    attachment_count: int = 0
    comment_count: int = 0

    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    """Schema for list of notes."""

    id: int
    title: str
    notebook_id: Optional[int]
    status: NoteStatus
    is_favorite: bool
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    tags: List[str] = []
    preview: Optional[str] = None  # First 200 chars of content

    class Config:
        from_attributes = True


class NoteShareRequest(BaseModel):
    """Schema for sharing a note."""

    user_ids: List[str]
    permission: PermissionLevel = PermissionLevel.VIEW


class NoteShareResponse(BaseModel):
    """Schema for note sharing response."""

    note_id: int
    shared_with: List[Dict[str, str]]  # [{"user_id": "...", "permission": "..."}]


# Template Schemas
class TemplateBase(BaseModel):
    """Base template schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content: str
    template_type: TemplateType = TemplateType.CUSTOM


class TemplateCreate(TemplateBase):
    """Schema for creating a template."""

    is_public: bool = False


class TemplateUpdate(BaseModel):
    """Schema for updating a template."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    content: Optional[str] = None
    template_type: Optional[TemplateType] = None
    is_public: Optional[bool] = None


class TemplateResponse(TemplateBase):
    """Schema for template response."""

    id: int
    user_id: Optional[str]
    is_system: bool
    is_public: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Attachment Schemas
class AttachmentBase(BaseModel):
    """Base attachment schema."""

    filename: str
    file_type: str
    url: Optional[str] = None


class AttachmentCreate(AttachmentBase):
    """Schema for creating an attachment."""

    note_id: int
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class AttachmentResponse(AttachmentBase):
    """Schema for attachment response."""

    id: int
    note_id: int
    original_filename: str
    file_size: Optional[int]
    mime_type: Optional[str]
    file_path: Optional[str]
    thumbnail_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Comment Schemas
class CommentBase(BaseModel):
    """Base comment schema."""

    content: str = Field(..., min_length=1)


class CommentCreate(CommentBase):
    """Schema for creating a comment."""

    note_id: int
    parent_id: Optional[int] = None


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""

    content: Optional[str] = Field(None, min_length=1)
    is_resolved: Optional[bool] = None


class CommentResponse(CommentBase):
    """Schema for comment response."""

    id: int
    note_id: int
    user_id: str
    parent_id: Optional[int]
    is_resolved: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Search Schemas
class SearchFilters(BaseModel):
    """Schema for search filters."""

    tags: Optional[List[str]] = None
    notebooks: Optional[List[int]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_favorite: Optional[bool] = None
    status: Optional[NoteStatus] = None


class SearchRequest(BaseModel):
    """Schema for search request."""

    query: Optional[str] = None
    filters: Optional[SearchFilters] = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)


class SavedSearchCreate(BaseModel):
    """Schema for creating a saved search."""

    name: str = Field(..., min_length=1, max_length=255)
    query: str = Field(..., max_length=1000)
    filters: Optional[Dict[str, Any]] = None


class SavedSearchResponse(BaseModel):
    """Schema for saved search response."""

    id: int
    user_id: str
    name: str
    query: str
    filters: Optional[Dict[str, Any]]
    is_pinned: bool
    created_at: datetime
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


# Export Schemas
class ExportFormat(str):
    """Export format options."""

    PDF = "pdf"
    WORD = "word"
    MARKDOWN = "markdown"
    HTML = "html"


class ExportRequest(BaseModel):
    """Schema for export request."""

    note_ids: List[int]
    format: str = Field(..., pattern="^(pdf|word|markdown|html)$")
    include_attachments: bool = True
    include_comments: bool = False

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate export format."""
        valid_formats = ["pdf", "word", "markdown", "html"]
        if v not in valid_formats:
            raise ValueError(f"Format must be one of: {', '.join(valid_formats)}")
        return v


# AI Assistant Schemas
class AISummaryRequest(BaseModel):
    """Schema for AI summary request."""

    note_id: int
    max_length: int = Field(200, ge=50, le=500)


class AIExtractTasksRequest(BaseModel):
    """Schema for AI extract tasks request."""

    note_id: int


class AISmartTagsRequest(BaseModel):
    """Schema for AI smart tags request."""

    note_id: int
    max_tags: int = Field(5, ge=1, le=10)


class AIGrammarCheckRequest(BaseModel):
    """Schema for AI grammar check request."""

    note_id: int


class AIResponse(BaseModel):
    """Schema for AI response."""

    success: bool
    data: Any
    message: Optional[str] = None
