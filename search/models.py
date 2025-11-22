"""Data models for search functionality."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Supported document types in Nexus platform."""

    DOCUMENT = "document"
    EMAIL = "email"
    FILE = "file"
    CHAT = "chat"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    PROJECT = "project"
    NOTE = "note"


class SearchOperator(str, Enum):
    """Search operators for filtering."""

    AND = "and"
    OR = "or"
    NOT = "not"


class SortOrder(str, Enum):
    """Sort order options."""

    ASC = "asc"
    DESC = "desc"


class BaseDocument(BaseModel):
    """Base document model for indexing."""

    id: str
    type: DocumentType
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    owner_id: str
    owner_name: str
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentDocument(BaseDocument):
    """Document-specific fields."""

    type: DocumentType = DocumentType.DOCUMENT
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    language: Optional[str] = "en"


class EmailDocument(BaseDocument):
    """Email-specific fields."""

    type: DocumentType = DocumentType.EMAIL
    sender: str
    recipients: List[str] = Field(default_factory=list)
    cc: List[str] = Field(default_factory=list)
    bcc: List[str] = Field(default_factory=list)
    subject: str
    has_attachments: bool = False
    attachment_names: List[str] = Field(default_factory=list)
    importance: str = "normal"
    folder: str = "inbox"


class FileDocument(BaseDocument):
    """File-specific fields."""

    type: DocumentType = DocumentType.FILE
    file_name: str
    file_path: str
    file_type: str
    file_size: int
    mime_type: str
    extension: str
    parent_folder: Optional[str] = None


class ChatDocument(BaseDocument):
    """Chat message-specific fields."""

    type: DocumentType = DocumentType.CHAT
    channel_id: str
    channel_name: str
    sender: str
    message: str
    participants: List[str] = Field(default_factory=list)
    thread_id: Optional[str] = None
    has_attachments: bool = False
    reactions: List[str] = Field(default_factory=list)


class SearchFilters(BaseModel):
    """Search filter options."""

    document_types: Optional[List[DocumentType]] = None
    owner_ids: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    file_types: Optional[List[str]] = None
    folders: Optional[List[str]] = None
    has_attachments: Optional[bool] = None
    custom_filters: Dict[str, Any] = Field(default_factory=dict)


class FacetRequest(BaseModel):
    """Facet aggregation request."""

    field: str
    size: int = 10
    min_count: int = 1


class SearchRequest(BaseModel):
    """Search request parameters."""

    query: str
    filters: Optional[SearchFilters] = None
    facets: Optional[List[FacetRequest]] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: SortOrder = SortOrder.DESC
    highlight: bool = True
    highlight_fields: Optional[List[str]] = None
    autocomplete: bool = False
    operator: SearchOperator = SearchOperator.AND


class HighlightedText(BaseModel):
    """Highlighted text snippet."""

    field: str
    fragments: List[str]


class SearchHit(BaseModel):
    """Individual search result."""

    id: str
    type: DocumentType
    title: str
    content: str
    score: float
    highlights: List[HighlightedText] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class FacetBucket(BaseModel):
    """Facet aggregation bucket."""

    key: str
    count: int


class FacetResult(BaseModel):
    """Facet aggregation result."""

    field: str
    buckets: List[FacetBucket]


class SearchResponse(BaseModel):
    """Search response with results and metadata."""

    query: str
    total: int
    page: int
    page_size: int
    total_pages: int
    hits: List[SearchHit]
    facets: List[FacetResult] = Field(default_factory=list)
    took_ms: int
    suggestions: List[str] = Field(default_factory=list)


class IndexStats(BaseModel):
    """Index statistics."""

    index_name: str
    document_count: int
    size_in_bytes: int
    created_at: Optional[datetime] = None


class HealthStatus(BaseModel):
    """Health check status."""

    status: str
    cluster_name: str
    indices: Dict[str, IndexStats]
    timestamp: datetime
