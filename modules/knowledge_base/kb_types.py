"""
Knowledge Base Type Definitions

Comprehensive type definitions for all KB entities including articles, categories,
FAQs, tutorials, videos, and more.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator


class ContentStatus(str, Enum):
    """Content publication status."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class ContentType(str, Enum):
    """Type of knowledge base content."""
    ARTICLE = "article"
    FAQ = "faq"
    TUTORIAL = "tutorial"
    GUIDE = "guide"
    VIDEO = "video"
    GLOSSARY = "glossary"
    RESOURCE = "resource"


class AccessLevel(str, Enum):
    """Content access level."""
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    INTERNAL = "internal"
    RESTRICTED = "restricted"


class Language(str, Enum):
    """Supported languages."""
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"
    PT = "pt"
    ZH = "zh"
    JA = "ja"
    KO = "ko"
    RU = "ru"
    AR = "ar"
    HI = "hi"


class DifficultyLevel(str, Enum):
    """Content difficulty level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class MediaType(str, Enum):
    """Media attachment types."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    CODE = "code"
    EMBED = "embed"


class Author(BaseModel):
    """Content author information."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    email: str
    avatar_url: Optional[HttpUrl] = None
    bio: Optional[str] = None
    role: str = "author"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Tag(BaseModel):
    """Content tag."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    slug: str
    description: Optional[str] = None
    color: Optional[str] = None
    usage_count: int = 0


class Category(BaseModel):
    """Hierarchical category."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    icon: Optional[str] = None
    order: int = 0
    is_active: bool = True
    article_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MediaAttachment(BaseModel):
    """Media attachment."""
    id: UUID = Field(default_factory=uuid4)
    type: MediaType
    url: HttpUrl
    thumbnail_url: Optional[HttpUrl] = None
    filename: str
    file_size: int  # in bytes
    mime_type: str
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class CodeBlock(BaseModel):
    """Code block with syntax highlighting."""
    language: str
    code: str
    filename: Optional[str] = None
    highlighted: bool = True
    line_numbers: bool = True


class Article(BaseModel):
    """Knowledge base article."""
    id: UUID = Field(default_factory=uuid4)
    title: str
    slug: str
    summary: Optional[str] = None
    content: str  # Rich HTML/Markdown content
    content_type: ContentType = ContentType.ARTICLE
    status: ContentStatus = ContentStatus.DRAFT
    access_level: AccessLevel = AccessLevel.PUBLIC
    language: Language = Language.EN

    # Relationships
    author_id: UUID
    category_id: Optional[UUID] = None
    tags: List[Tag] = Field(default_factory=list)

    # Media
    featured_image_url: Optional[HttpUrl] = None
    attachments: List[MediaAttachment] = Field(default_factory=list)

    # SEO
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: List[str] = Field(default_factory=list)

    # Analytics
    view_count: int = 0
    helpful_count: int = 0
    not_helpful_count: int = 0
    average_rating: float = 0.0

    # Versioning
    version: int = 1
    is_latest: bool = True

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None


class FAQ(BaseModel):
    """Frequently Asked Question."""
    id: UUID = Field(default_factory=uuid4)
    question: str
    answer: str
    category_id: Optional[UUID] = None
    tags: List[Tag] = Field(default_factory=list)
    language: Language = Language.EN

    # Related content
    related_article_ids: List[UUID] = Field(default_factory=list)

    # Analytics
    view_count: int = 0
    helpful_count: int = 0
    not_helpful_count: int = 0

    # Auto-generation metadata
    auto_generated: bool = False
    source_type: Optional[str] = None  # e.g., "support_ticket", "chat"

    # Status
    status: ContentStatus = ContentStatus.PUBLISHED
    order: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TutorialStep(BaseModel):
    """Single step in a tutorial."""
    id: UUID = Field(default_factory=uuid4)
    order: int
    title: str
    content: str
    code_blocks: List[CodeBlock] = Field(default_factory=list)
    images: List[MediaAttachment] = Field(default_factory=list)
    estimated_time: Optional[int] = None  # in minutes
    is_optional: bool = False


class Tutorial(BaseModel):
    """Interactive tutorial."""
    id: UUID = Field(default_factory=uuid4)
    title: str
    slug: str
    description: str
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    language: Language = Language.EN

    # Content
    steps: List[TutorialStep] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    learning_objectives: List[str] = Field(default_factory=list)

    # Metadata
    author_id: UUID
    category_id: Optional[UUID] = None
    tags: List[Tag] = Field(default_factory=list)
    estimated_duration: int = 0  # total minutes

    # Status
    status: ContentStatus = ContentStatus.DRAFT
    access_level: AccessLevel = AccessLevel.PUBLIC

    # Analytics
    completion_count: int = 0
    average_completion_time: int = 0  # minutes
    average_rating: float = 0.0

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VideoChapter(BaseModel):
    """Video chapter/timestamp."""
    id: UUID = Field(default_factory=uuid4)
    title: str
    start_time: int  # seconds
    end_time: int  # seconds
    description: Optional[str] = None


class VideoTranscript(BaseModel):
    """Video transcript segment."""
    id: UUID = Field(default_factory=uuid4)
    start_time: int  # seconds
    end_time: int  # seconds
    text: str
    language: Language = Language.EN


class Video(BaseModel):
    """Video knowledge resource."""
    id: UUID = Field(default_factory=uuid4)
    title: str
    slug: str
    description: str

    # Video details
    video_url: HttpUrl
    thumbnail_url: Optional[HttpUrl] = None
    duration: int  # seconds
    resolution: Optional[str] = None  # e.g., "1080p"
    file_size: Optional[int] = None  # bytes

    # Enhanced features
    chapters: List[VideoChapter] = Field(default_factory=list)
    transcripts: List[VideoTranscript] = Field(default_factory=list)

    # Metadata
    author_id: UUID
    category_id: Optional[UUID] = None
    tags: List[Tag] = Field(default_factory=list)
    language: Language = Language.EN

    # Status
    status: ContentStatus = ContentStatus.DRAFT
    access_level: AccessLevel = AccessLevel.PUBLIC

    # Analytics
    view_count: int = 0
    watch_time: int = 0  # total seconds watched
    average_completion_rate: float = 0.0
    average_rating: float = 0.0

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GlossaryTerm(BaseModel):
    """Glossary term definition."""
    id: UUID = Field(default_factory=uuid4)
    term: str
    definition: str
    abbreviation: Optional[str] = None
    pronunciation: Optional[str] = None

    # Related content
    related_terms: List[UUID] = Field(default_factory=list)
    related_articles: List[UUID] = Field(default_factory=list)

    # Multi-language
    language: Language = Language.EN
    translations: Dict[Language, str] = Field(default_factory=dict)

    # Metadata
    category_id: Optional[UUID] = None
    tags: List[Tag] = Field(default_factory=list)

    # Analytics
    view_count: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Rating(BaseModel):
    """Content rating and feedback."""
    id: UUID = Field(default_factory=uuid4)
    content_id: UUID
    content_type: ContentType
    user_id: UUID

    # Rating
    rating: int = Field(ge=1, le=5)
    is_helpful: Optional[bool] = None

    # Feedback
    comment: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SearchQuery(BaseModel):
    """Search query with filters."""
    query: str
    content_types: List[ContentType] = Field(default_factory=list)
    categories: List[UUID] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    access_levels: List[AccessLevel] = Field(default_factory=list)
    min_rating: Optional[float] = None
    limit: int = 20
    offset: int = 0


class SearchResult(BaseModel):
    """Search result item."""
    id: UUID
    title: str
    snippet: str
    content_type: ContentType
    url: str
    relevance_score: float
    highlights: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalyticsEvent(BaseModel):
    """Analytics event tracking."""
    id: UUID = Field(default_factory=uuid4)
    event_type: str  # view, search, helpful, rating, etc.
    content_id: Optional[UUID] = None
    content_type: Optional[ContentType] = None
    user_id: Optional[UUID] = None
    session_id: str

    # Event data
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Context
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    referrer: Optional[str] = None

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatMessage(BaseModel):
    """Chatbot conversation message."""
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    role: str  # user, assistant, system
    content: str

    # AI metadata
    intent: Optional[str] = None
    confidence: Optional[float] = None
    suggested_articles: List[UUID] = Field(default_factory=list)

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ArticleVersion(BaseModel):
    """Article version history."""
    id: UUID = Field(default_factory=uuid4)
    article_id: UUID
    version: int
    title: str
    content: str

    # Change tracking
    changed_by: UUID
    change_summary: Optional[str] = None
    diff: Optional[Dict[str, Any]] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewWorkflow(BaseModel):
    """Content review workflow."""
    id: UUID = Field(default_factory=uuid4)
    content_id: UUID
    content_type: ContentType

    # Workflow
    status: str  # pending, in_review, approved, rejected
    reviewer_id: Optional[UUID] = None

    # Feedback
    comments: List[str] = Field(default_factory=list)
    required_changes: List[str] = Field(default_factory=list)

    # Timestamps
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None


class Template(BaseModel):
    """Article template."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    content_type: ContentType

    # Template content
    template_content: str
    placeholders: List[str] = Field(default_factory=list)
    sections: List[Dict[str, str]] = Field(default_factory=list)

    # Metadata
    category: str
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True
    usage_count: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
