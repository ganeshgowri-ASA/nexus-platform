"""
Wiki Type Definitions

Comprehensive type definitions for the NEXUS Wiki System including:
- Page, Section, Category, Tag, Link, Attachment, History, Comment
- Enums for page status, content format, permission levels
- Pydantic models for validation and serialization

Author: NEXUS Platform Team
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============================================================================
# ENUMS
# ============================================================================

class PageStatus(str, Enum):
    """Status of a wiki page."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ContentFormat(str, Enum):
    """Format of page content."""
    MARKDOWN = "markdown"
    HTML = "html"
    RICH_TEXT = "rich_text"
    PLAIN_TEXT = "plain_text"


class PermissionLevel(str, Enum):
    """Permission levels for wiki access."""
    NONE = "none"
    READ = "read"
    COMMENT = "comment"
    EDIT = "edit"
    ADMIN = "admin"
    OWNER = "owner"


class LinkType(str, Enum):
    """Type of wiki link."""
    INTERNAL = "internal"
    EXTERNAL = "external"
    ANCHOR = "anchor"
    REDIRECT = "redirect"


class AttachmentType(str, Enum):
    """Type of attachment."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    CODE = "code"
    OTHER = "other"


class TemplateCategory(str, Enum):
    """Category of page template."""
    MEETING_NOTES = "meeting_notes"
    PROJECT_DOC = "project_doc"
    HOW_TO = "how_to"
    API_DOC = "api_doc"
    TROUBLESHOOTING = "troubleshooting"
    DECISION_LOG = "decision_log"
    BLANK = "blank"
    CUSTOM = "custom"


class MacroType(str, Enum):
    """Type of wiki macro."""
    TABLE_OF_CONTENTS = "toc"
    PAGE_LIST = "page_list"
    CODE_BLOCK = "code_block"
    CHART = "chart"
    EMBED = "embed"
    QUERY = "query"
    CALENDAR = "calendar"
    CUSTOM = "custom"


class ExportFormat(str, Enum):
    """Export format options."""
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    DOCX = "docx"
    CONFLUENCE = "confluence"


class ImportSource(str, Enum):
    """Import source types."""
    CONFLUENCE = "confluence"
    MEDIAWIKI = "mediawiki"
    NOTION = "notion"
    GOOGLE_DOCS = "google_docs"
    MARKDOWN = "markdown"
    HTML = "html"


class ChangeType(str, Enum):
    """Type of change in version history."""
    CREATED = "created"
    EDITED = "edited"
    MOVED = "moved"
    RENAMED = "renamed"
    DELETED = "deleted"
    RESTORED = "restored"
    PERMISSION_CHANGED = "permission_changed"


class NotificationType(str, Enum):
    """Type of notification."""
    PAGE_EDITED = "page_edited"
    COMMENT_ADDED = "comment_added"
    MENTION = "mention"
    PERMISSION_CHANGED = "permission_changed"
    PAGE_MOVED = "page_moved"
    PAGE_DELETED = "page_deleted"


# ============================================================================
# BASE MODELS
# ============================================================================

class WikiBaseModel(BaseModel):
    """Base model for all wiki entities."""
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
    )


# ============================================================================
# CORE MODELS
# ============================================================================

class WikiTag(WikiBaseModel):
    """Represents a tag for categorization."""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    description: Optional[str] = None
    usage_count: int = Field(default=0, ge=0)
    created_at: Optional[datetime] = None

    @field_validator("name")
    @classmethod
    def validate_tag_name(cls, v: str) -> str:
        """Validate and normalize tag name."""
        return v.strip().lower()


class WikiCategory(WikiBaseModel):
    """Represents a hierarchical category."""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    order: int = Field(default=0)
    page_count: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Relationships
    children: List["WikiCategory"] = Field(default_factory=list)
    parent: Optional["WikiCategory"] = None


class WikiLink(WikiBaseModel):
    """Represents a link between pages or to external resources."""
    id: Optional[int] = None
    source_page_id: int
    target_page_id: Optional[int] = None
    target_url: Optional[str] = None
    link_type: LinkType
    anchor: Optional[str] = None
    title: Optional[str] = None
    is_broken: bool = Field(default=False)
    created_at: Optional[datetime] = None

    @field_validator("target_url")
    @classmethod
    def validate_target(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure either target_page_id or target_url is set."""
        if v is None and info.data.get("target_page_id") is None:
            raise ValueError("Either target_page_id or target_url must be set")
        return v


class WikiAttachment(WikiBaseModel):
    """Represents a file attachment to a wiki page."""
    id: Optional[int] = None
    page_id: int
    filename: str = Field(..., min_length=1, max_length=255)
    original_filename: str
    file_path: str
    file_size: int = Field(..., ge=0)
    mime_type: str
    attachment_type: AttachmentType
    version: int = Field(default=1, ge=1)
    description: Optional[str] = None
    uploaded_by: int
    uploaded_at: Optional[datetime] = None
    is_deleted: bool = Field(default=False)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WikiSection(WikiBaseModel):
    """Represents a section within a wiki page."""
    id: Optional[int] = None
    page_id: int
    title: str = Field(..., min_length=1, max_length=200)
    content: str
    order: int = Field(default=0)
    level: int = Field(default=1, ge=1, le=6)
    anchor_id: str
    parent_section_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WikiComment(WikiBaseModel):
    """Represents a comment or discussion on a wiki page."""
    id: Optional[int] = None
    page_id: int
    parent_comment_id: Optional[int] = None
    author_id: int
    content: str = Field(..., min_length=1)
    is_resolved: bool = Field(default=False)
    is_deleted: bool = Field(default=False)
    mentions: List[int] = Field(default_factory=list)
    reactions: Dict[str, List[int]] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Relationships
    replies: List["WikiComment"] = Field(default_factory=list)
    author_name: Optional[str] = None


class WikiHistory(WikiBaseModel):
    """Represents a version in the page history."""
    id: Optional[int] = None
    page_id: int
    version: int = Field(..., ge=1)
    title: str
    content: str
    change_type: ChangeType
    change_summary: Optional[str] = None
    changed_by: int
    changed_at: Optional[datetime] = None
    content_size: int = Field(default=0, ge=0)
    diff_size: int = Field(default=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Relationships
    changed_by_name: Optional[str] = None


class WikiPermission(WikiBaseModel):
    """Represents access permissions for a wiki page or category."""
    id: Optional[int] = None
    page_id: Optional[int] = None
    category_id: Optional[int] = None
    user_id: Optional[int] = None
    role: Optional[str] = None
    permission_level: PermissionLevel
    granted_by: int
    granted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_inherited: bool = Field(default=False)


class WikiTemplate(WikiBaseModel):
    """Represents a page template."""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: TemplateCategory
    content: str
    thumbnail: Optional[str] = None
    variables: List[str] = Field(default_factory=list)
    is_public: bool = Field(default=True)
    usage_count: int = Field(default=0, ge=0)
    created_by: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WikiPage(WikiBaseModel):
    """Represents a complete wiki page with all metadata."""
    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    content: str
    content_format: ContentFormat = Field(default=ContentFormat.MARKDOWN)
    summary: Optional[str] = Field(None, max_length=500)
    status: PageStatus = Field(default=PageStatus.DRAFT)

    # Organization
    category_id: Optional[int] = None
    parent_page_id: Optional[int] = None
    namespace: Optional[str] = None
    path: str = Field(default="/")

    # Metadata
    author_id: int
    current_version: int = Field(default=1, ge=1)
    view_count: int = Field(default=0, ge=0)
    like_count: int = Field(default=0, ge=0)
    comment_count: int = Field(default=0, ge=0)

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    # Features
    is_featured: bool = Field(default=False)
    is_locked: bool = Field(default=False)
    is_template: bool = Field(default=False)
    is_deleted: bool = Field(default=False)

    # Additional data
    tags: List[WikiTag] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Relationships (populated on demand)
    category: Optional[WikiCategory] = None
    author_name: Optional[str] = None
    sections: List[WikiSection] = Field(default_factory=list)
    attachments: List[WikiAttachment] = Field(default_factory=list)
    links: List[WikiLink] = Field(default_factory=list)
    comments: List[WikiComment] = Field(default_factory=list)
    permissions: List[WikiPermission] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate and normalize slug."""
        import re
        normalized = re.sub(r"[^a-z0-9-]", "-", v.lower())
        normalized = re.sub(r"-+", "-", normalized).strip("-")
        if not normalized:
            raise ValueError("Slug cannot be empty after normalization")
        return normalized


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PageCreateRequest(WikiBaseModel):
    """Request model for creating a new page."""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(default="")
    content_format: ContentFormat = Field(default=ContentFormat.MARKDOWN)
    summary: Optional[str] = None
    category_id: Optional[int] = None
    parent_page_id: Optional[int] = None
    namespace: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    status: PageStatus = Field(default=PageStatus.DRAFT)
    template_id: Optional[int] = None


class PageUpdateRequest(WikiBaseModel):
    """Request model for updating a page."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    content_format: Optional[ContentFormat] = None
    summary: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[PageStatus] = None
    tags: Optional[List[str]] = None
    change_summary: Optional[str] = None


class PageSearchRequest(WikiBaseModel):
    """Request model for searching pages."""
    query: str = Field(..., min_length=1)
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    status: Optional[PageStatus] = None
    author_id: Optional[int] = None
    namespace: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    include_content: bool = Field(default=False)


class PageSearchResult(WikiBaseModel):
    """Result model for page search."""
    page: WikiPage
    score: float = Field(..., ge=0.0, le=1.0)
    highlights: List[str] = Field(default_factory=list)
    matched_fields: List[str] = Field(default_factory=list)


class PageTreeNode(WikiBaseModel):
    """Represents a node in the page tree structure."""
    page: WikiPage
    children: List["PageTreeNode"] = Field(default_factory=list)
    depth: int = Field(default=0, ge=0)


class BreadcrumbItem(WikiBaseModel):
    """Represents a breadcrumb navigation item."""
    page_id: int
    title: str
    slug: str
    url: str


class AnalyticsData(WikiBaseModel):
    """Analytics data for pages and users."""
    page_id: Optional[int] = None
    user_id: Optional[int] = None
    total_views: int = Field(default=0, ge=0)
    unique_views: int = Field(default=0, ge=0)
    total_edits: int = Field(default=0, ge=0)
    total_comments: int = Field(default=0, ge=0)
    avg_time_on_page: Optional[float] = None
    popular_pages: List[Dict[str, Any]] = Field(default_factory=list)
    top_contributors: List[Dict[str, Any]] = Field(default_factory=list)
    activity_heatmap: Dict[str, int] = Field(default_factory=dict)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# Update forward references
WikiCategory.model_rebuild()
WikiComment.model_rebuild()
PageTreeNode.model_rebuild()
