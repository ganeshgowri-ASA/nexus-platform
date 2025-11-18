"""
Document Management System Type Definitions and Pydantic Schemas.

This module defines all Pydantic models for request/response validation,
data structures, and type definitions for the DMS.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Enums

class DocumentStatus(str, Enum):
    """Document status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    LOCKED = "locked"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class AccessLevel(str, Enum):
    """Access level enumeration."""

    NONE = "none"
    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"
    ADMIN = "admin"


class ShareType(str, Enum):
    """Share type enumeration."""

    PRIVATE = "private"
    LINK = "link"
    PUBLIC = "public"


class WorkflowStatus(str, Enum):
    """Workflow status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class SortOrder(str, Enum):
    """Sort order enumeration."""

    ASC = "asc"
    DESC = "desc"


class DocumentSortField(str, Enum):
    """Fields that can be used for sorting documents."""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    TITLE = "title"
    FILE_SIZE = "file_size"
    VIEW_COUNT = "view_count"


# Base Schemas

class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


# Document Schemas

class DocumentCreate(BaseSchema):
    """Schema for creating a new document."""

    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    description: Optional[str] = Field(None, description="Document description")
    folder_id: Optional[int] = Field(None, description="Parent folder ID")
    is_public: bool = Field(False, description="Whether document is public")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")


class DocumentUpdate(BaseSchema):
    """Schema for updating a document."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    folder_id: Optional[int] = None
    is_public: Optional[bool] = None
    status: Optional[DocumentStatus] = None


class DocumentResponse(BaseSchema):
    """Schema for document response."""

    id: int
    title: str
    description: Optional[str]
    file_name: str
    file_size: int
    mime_type: str
    status: DocumentStatus
    owner_id: int
    folder_id: Optional[int]
    is_public: bool
    view_count: int
    download_count: int
    current_version: int
    is_locked: bool
    locked_by_id: Optional[int]
    locked_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @field_validator("file_size")
    @classmethod
    def format_file_size(cls, v: int) -> int:
        """Ensure file size is non-negative."""
        return max(0, v)


class DocumentDetailResponse(DocumentResponse):
    """Detailed document response with relationships."""

    tags: List["TagResponse"] = []
    metadata: List["MetadataEntry"] = []
    permissions: List["PermissionResponse"] = []
    version_count: int = 0


class DocumentListResponse(BaseSchema):
    """Paginated list of documents."""

    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Folder Schemas

class FolderCreate(BaseSchema):
    """Schema for creating a folder."""

    name: str = Field(..., min_length=1, max_length=255, description="Folder name")
    description: Optional[str] = Field(None, description="Folder description")
    parent_id: Optional[int] = Field(None, description="Parent folder ID")
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name")


class FolderUpdate(BaseSchema):
    """Schema for updating a folder."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)


class FolderResponse(BaseSchema):
    """Schema for folder response."""

    id: int
    name: str
    description: Optional[str]
    path: str
    parent_id: Optional[int]
    owner_id: int
    is_public: bool
    color: Optional[str]
    icon: Optional[str]
    created_at: datetime
    updated_at: datetime


class FolderTreeResponse(FolderResponse):
    """Folder response with children."""

    children: List["FolderTreeResponse"] = []
    document_count: int = 0


# Version Schemas

class VersionCreate(BaseSchema):
    """Schema for creating a new version."""

    change_summary: Optional[str] = Field(None, description="Summary of changes")


class VersionResponse(BaseSchema):
    """Schema for version response."""

    id: int
    document_id: int
    version_number: int
    file_size: int
    file_hash: str
    change_summary: Optional[str]
    created_by_id: int
    created_at: datetime


# Metadata Schemas

class MetadataEntry(BaseSchema):
    """Schema for metadata key-value pair."""

    key: str = Field(..., min_length=1, max_length=255)
    value: Any
    value_type: str = Field("string", description="Type of value")
    is_system: bool = Field(False, description="System metadata flag")


class MetadataUpdate(BaseSchema):
    """Schema for updating metadata."""

    metadata: Dict[str, Any] = Field(..., description="Metadata to update")


# Tag Schemas

class TagCreate(BaseSchema):
    """Schema for creating a tag."""

    name: str = Field(..., min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TagResponse(BaseSchema):
    """Schema for tag response."""

    id: int
    name: str
    color: Optional[str]
    created_at: datetime


# Permission Schemas

class PermissionCreate(BaseSchema):
    """Schema for creating a permission."""

    user_id: Optional[int] = Field(None, description="User ID (null for public)")
    access_level: AccessLevel = Field(..., description="Access level")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")


class PermissionResponse(BaseSchema):
    """Schema for permission response."""

    id: int
    document_id: int
    user_id: Optional[int]
    access_level: AccessLevel
    granted_by_id: int
    expires_at: Optional[datetime]
    created_at: datetime


# Share Link Schemas

class ShareLinkCreate(BaseSchema):
    """Schema for creating a share link."""

    share_type: ShareType = Field(ShareType.LINK, description="Share type")
    access_level: AccessLevel = Field(AccessLevel.VIEW, description="Access level")
    password: Optional[str] = Field(None, min_length=4, description="Optional password")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    max_downloads: Optional[int] = Field(None, ge=1, description="Max downloads")


class ShareLinkResponse(BaseSchema):
    """Schema for share link response."""

    id: int
    document_id: int
    token: str
    share_type: ShareType
    access_level: AccessLevel
    expires_at: Optional[datetime]
    max_downloads: Optional[int]
    download_count: int
    created_by_id: int
    created_at: datetime


# Comment Schemas

class CommentCreate(BaseSchema):
    """Schema for creating a comment."""

    content: str = Field(..., min_length=1, description="Comment content")
    parent_id: Optional[int] = Field(None, description="Parent comment ID for replies")


class CommentUpdate(BaseSchema):
    """Schema for updating a comment."""

    content: str = Field(..., min_length=1)
    is_resolved: Optional[bool] = None


class CommentResponse(BaseSchema):
    """Schema for comment response."""

    id: int
    document_id: int
    user_id: int
    content: str
    parent_id: Optional[int]
    is_resolved: bool
    created_at: datetime
    updated_at: datetime


# Workflow Schemas

class WorkflowStepCreate(BaseSchema):
    """Schema for workflow step."""

    step_name: str = Field(..., min_length=1, max_length=255)
    assignee_id: int = Field(..., description="User assigned to this step")


class WorkflowCreate(BaseSchema):
    """Schema for creating a workflow."""

    workflow_name: str = Field(..., min_length=1, max_length=255)
    steps: List[WorkflowStepCreate] = Field(..., min_items=1, description="Workflow steps")


class WorkflowStepResponse(BaseSchema):
    """Schema for workflow step response."""

    id: int
    step_number: int
    step_name: str
    assignee_id: int
    status: WorkflowStatus
    completed_at: Optional[datetime]
    comments: Optional[str]
    created_at: datetime


class WorkflowResponse(BaseSchema):
    """Schema for workflow response."""

    id: int
    document_id: int
    workflow_name: str
    status: WorkflowStatus
    initiated_by_id: int
    current_step: int
    total_steps: int
    steps: List[WorkflowStepResponse] = []
    created_at: datetime
    updated_at: datetime


# Search Schemas

class SearchQuery(BaseSchema):
    """Schema for search query."""

    query: str = Field(..., min_length=1, description="Search query")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    sort_by: DocumentSortField = Field(DocumentSortField.UPDATED_AT, description="Sort field")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    include_archived: bool = Field(False, description="Include archived documents")


class SearchResult(BaseSchema):
    """Schema for search result."""

    document: DocumentResponse
    score: float = Field(..., description="Relevance score")
    highlights: Dict[str, List[str]] = Field(default_factory=dict, description="Search highlights")


class SearchResponse(BaseSchema):
    """Schema for search response."""

    results: List[SearchResult]
    total: int
    page: int
    page_size: int
    query: str
    took_ms: int = Field(..., description="Search time in milliseconds")


# Bulk Operation Schemas

class BulkOperationType(str, Enum):
    """Bulk operation types."""

    UPLOAD = "upload"
    DOWNLOAD = "download"
    MOVE = "move"
    DELETE = "delete"
    TAG = "tag"
    METADATA_UPDATE = "metadata_update"


class BulkOperationCreate(BaseSchema):
    """Schema for creating a bulk operation."""

    operation_type: BulkOperationType
    document_ids: List[int] = Field(..., min_items=1, description="Document IDs")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")


class BulkOperationStatus(str, Enum):
    """Bulk operation status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BulkOperationResponse(BaseSchema):
    """Schema for bulk operation response."""

    id: str = Field(..., description="Operation task ID")
    operation_type: BulkOperationType
    status: BulkOperationStatus
    total_items: int
    processed_items: int
    failed_items: int
    progress_percentage: float
    created_at: datetime
    completed_at: Optional[datetime]


# Audit Log Schemas

class AuditLogEntry(BaseSchema):
    """Schema for audit log entry."""

    id: int
    document_id: Optional[int]
    user_id: int
    action: str
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime


# Statistics Schemas

class DocumentStatistics(BaseSchema):
    """Schema for document statistics."""

    total_documents: int
    total_size: int
    total_views: int
    total_downloads: int
    documents_by_status: Dict[str, int]
    documents_by_type: Dict[str, int]
    recent_activity_count: int


class StorageStatistics(BaseSchema):
    """Schema for storage statistics."""

    total_storage: int
    used_storage: int
    available_storage: int
    usage_percentage: float
    file_count: int
    average_file_size: int
    largest_files: List[DocumentResponse]


# Upload Schemas

class UploadRequest(BaseSchema):
    """Schema for file upload request."""

    title: Optional[str] = Field(None, description="Document title (defaults to filename)")
    description: Optional[str] = None
    folder_id: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_public: bool = False


class ChunkedUploadInit(BaseSchema):
    """Schema for initializing chunked upload."""

    file_name: str
    file_size: int
    mime_type: str
    chunk_size: int = Field(5242880, description="Chunk size in bytes (5MB default)")
    total_chunks: int


class ChunkedUploadComplete(BaseSchema):
    """Schema for completing chunked upload."""

    upload_id: str
    document_data: UploadRequest


# AI Assistant Schemas

class DocumentSummaryRequest(BaseSchema):
    """Schema for document summarization request."""

    max_length: int = Field(200, ge=50, le=1000, description="Max summary length in words")
    include_key_points: bool = Field(True, description="Include bullet points")


class DocumentSummaryResponse(BaseSchema):
    """Schema for document summary response."""

    summary: str
    key_points: List[str] = []
    word_count: int
    confidence_score: float


class EntityExtractionResponse(BaseSchema):
    """Schema for entity extraction response."""

    entities: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Extracted entities by type (person, organization, location, etc.)"
    )
    keywords: List[str] = []
    topics: List[str] = []


class ClassificationSuggestion(BaseSchema):
    """Schema for classification suggestion."""

    category: str
    confidence: float
    reasoning: str


class ClassificationResponse(BaseSchema):
    """Schema for classification response."""

    suggestions: List[ClassificationSuggestion]
    recommended_tags: List[str]
    recommended_folder: Optional[str]


# Update forward references
FolderTreeResponse.model_rebuild()
