"""
Database Models for Knowledge Base System

SQLAlchemy models for PostgreSQL with full-text search, relationships,
and optimized indexing.
"""

from datetime import datetime
from typing import List
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Association tables for many-to-many relationships
article_tags = Table(
    "kb_article_tags",
    Base.metadata,
    Column("article_id", UUID(as_uuid=True), ForeignKey("kb_articles.id")),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("kb_tags.id")),
)

tutorial_tags = Table(
    "kb_tutorial_tags",
    Base.metadata,
    Column("tutorial_id", UUID(as_uuid=True), ForeignKey("kb_tutorials.id")),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("kb_tags.id")),
)

video_tags = Table(
    "kb_video_tags",
    Base.metadata,
    Column("video_id", UUID(as_uuid=True), ForeignKey("kb_videos.id")),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("kb_tags.id")),
)

faq_tags = Table(
    "kb_faq_tags",
    Base.metadata,
    Column("faq_id", UUID(as_uuid=True), ForeignKey("kb_faqs.id")),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("kb_tags.id")),
)

glossary_tags = Table(
    "kb_glossary_tags",
    Base.metadata,
    Column("glossary_id", UUID(as_uuid=True), ForeignKey("kb_glossary_terms.id")),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("kb_tags.id")),
)


class Author(Base):
    """Author model."""
    __tablename__ = "kb_authors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    avatar_url = Column(String(500))
    bio = Column(Text)
    role = Column(String(100), default="author")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    articles = relationship("Article", back_populates="author")
    tutorials = relationship("Tutorial", back_populates="author")
    videos = relationship("Video", back_populates="author")


class Tag(Base):
    """Tag model."""
    __tablename__ = "kb_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    color = Column(String(20))
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    articles = relationship("Article", secondary=article_tags, back_populates="tags")
    tutorials = relationship("Tutorial", secondary=tutorial_tags, back_populates="tags")
    videos = relationship("Video", secondary=video_tags, back_populates="tags")
    faqs = relationship("FAQ", secondary=faq_tags, back_populates="tags")
    glossary_terms = relationship("GlossaryTerm", secondary=glossary_tags, back_populates="tags")


class Category(Base):
    """Category model with hierarchical structure."""
    __tablename__ = "kb_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("kb_categories.id"))
    icon = Column(String(100))
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    article_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parent = relationship("Category", remote_side=[id], backref="children")
    articles = relationship("Article", back_populates="category")
    faqs = relationship("FAQ", back_populates="category")
    tutorials = relationship("Tutorial", back_populates="category")
    videos = relationship("Video", back_populates="category")
    glossary_terms = relationship("GlossaryTerm", back_populates="category")

    __table_args__ = (Index("ix_kb_categories_parent_id", parent_id),)


class Article(Base):
    """Article model."""
    __tablename__ = "kb_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False, index=True)
    slug = Column(String(500), unique=True, nullable=False, index=True)
    summary = Column(Text)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="article", index=True)
    status = Column(String(50), default="draft", index=True)
    access_level = Column(String(50), default="public", index=True)
    language = Column(String(10), default="en", index=True)

    # Foreign keys
    author_id = Column(UUID(as_uuid=True), ForeignKey("kb_authors.id"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("kb_categories.id"), index=True)

    # Media
    featured_image_url = Column(String(500))
    attachments = Column(JSONB, default=list)

    # SEO
    meta_title = Column(String(500))
    meta_description = Column(Text)
    meta_keywords = Column(ARRAY(String))

    # Analytics
    view_count = Column(Integer, default=0, index=True)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0, index=True)

    # Versioning
    version = Column(Integer, default=1)
    is_latest = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, index=True)
    archived_at = Column(DateTime)

    # Relationships
    author = relationship("Author", back_populates="articles")
    category = relationship("Category", back_populates="articles")
    tags = relationship("Tag", secondary=article_tags, back_populates="articles")
    ratings = relationship("Rating", back_populates="article")
    versions = relationship("ArticleVersion", back_populates="article")

    # Indexes for full-text search and performance
    __table_args__ = (
        Index("ix_kb_articles_status_published", status, published_at),
        Index("ix_kb_articles_category_status", category_id, status),
        Index("ix_kb_articles_language_status", language, status),
    )


class FAQ(Base):
    """FAQ model."""
    __tablename__ = "kb_faqs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    question = Column(Text, nullable=False, index=True)
    answer = Column(Text, nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("kb_categories.id"), index=True)
    language = Column(String(10), default="en", index=True)

    # Related content
    related_article_ids = Column(ARRAY(UUID(as_uuid=True)))

    # Analytics
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)

    # Auto-generation metadata
    auto_generated = Column(Boolean, default=False)
    source_type = Column(String(100))

    # Status
    status = Column(String(50), default="published", index=True)
    order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship("Category", back_populates="faqs")
    tags = relationship("Tag", secondary=faq_tags, back_populates="faqs")


class Tutorial(Base):
    """Tutorial model."""
    __tablename__ = "kb_tutorials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False, index=True)
    slug = Column(String(500), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    difficulty = Column(String(50), default="beginner", index=True)
    language = Column(String(10), default="en", index=True)

    # Content
    steps = Column(JSONB, default=list)
    prerequisites = Column(ARRAY(String))
    learning_objectives = Column(ARRAY(String))

    # Metadata
    author_id = Column(UUID(as_uuid=True), ForeignKey("kb_authors.id"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("kb_categories.id"), index=True)
    estimated_duration = Column(Integer, default=0)

    # Status
    status = Column(String(50), default="draft", index=True)
    access_level = Column(String(50), default="public", index=True)

    # Analytics
    completion_count = Column(Integer, default=0)
    average_completion_time = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    author = relationship("Author", back_populates="tutorials")
    category = relationship("Category", back_populates="tutorials")
    tags = relationship("Tag", secondary=tutorial_tags, back_populates="tutorials")
    progress_records = relationship("TutorialProgress", back_populates="tutorial")


class TutorialProgress(Base):
    """Tutorial progress tracking."""
    __tablename__ = "kb_tutorial_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tutorial_id = Column(UUID(as_uuid=True), ForeignKey("kb_tutorials.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    current_step = Column(Integer, default=0)
    completed_steps = Column(ARRAY(Integer), default=list)
    is_completed = Column(Boolean, default=False)
    completion_percentage = Column(Float, default=0.0)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    last_accessed_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    tutorial = relationship("Tutorial", back_populates="progress_records")

    __table_args__ = (UniqueConstraint("tutorial_id", "user_id", name="uq_tutorial_user"),)


class Video(Base):
    """Video model."""
    __tablename__ = "kb_videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False, index=True)
    slug = Column(String(500), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)

    # Video details
    video_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500))
    duration = Column(Integer, nullable=False)  # seconds
    resolution = Column(String(50))
    file_size = Column(Integer)  # bytes

    # Enhanced features
    chapters = Column(JSONB, default=list)
    transcripts = Column(JSONB, default=list)

    # Metadata
    author_id = Column(UUID(as_uuid=True), ForeignKey("kb_authors.id"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("kb_categories.id"), index=True)
    language = Column(String(10), default="en", index=True)

    # Status
    status = Column(String(50), default="draft", index=True)
    access_level = Column(String(50), default="public", index=True)

    # Analytics
    view_count = Column(Integer, default=0)
    watch_time = Column(Integer, default=0)  # total seconds watched
    average_completion_rate = Column(Float, default=0.0)
    average_rating = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    author = relationship("Author", back_populates="videos")
    category = relationship("Category", back_populates="videos")
    tags = relationship("Tag", secondary=video_tags, back_populates="videos")


class GlossaryTerm(Base):
    """Glossary term model."""
    __tablename__ = "kb_glossary_terms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    term = Column(String(255), nullable=False, index=True, unique=True)
    definition = Column(Text, nullable=False)
    abbreviation = Column(String(50))
    pronunciation = Column(String(255))

    # Related content
    related_terms = Column(ARRAY(UUID(as_uuid=True)))
    related_articles = Column(ARRAY(UUID(as_uuid=True)))

    # Multi-language
    language = Column(String(10), default="en", index=True)
    translations = Column(JSONB, default=dict)

    # Metadata
    category_id = Column(UUID(as_uuid=True), ForeignKey("kb_categories.id"), index=True)

    # Analytics
    view_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship("Category", back_populates="glossary_terms")
    tags = relationship("Tag", secondary=glossary_tags, back_populates="glossary_terms")


class Rating(Base):
    """Rating model."""
    __tablename__ = "kb_ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    content_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    content_type = Column(String(50), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Rating
    rating = Column(Integer, nullable=False)
    is_helpful = Column(Boolean)

    # Feedback
    comment = Column(Text)
    feedback_tags = Column(ARRAY(String))

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (polymorphic)
    article_id = Column(UUID(as_uuid=True), ForeignKey("kb_articles.id"))
    article = relationship("Article", back_populates="ratings")

    __table_args__ = (
        UniqueConstraint("content_id", "user_id", name="uq_content_user_rating"),
        Index("ix_kb_ratings_content", content_type, content_id),
    )


class ArticleVersion(Base):
    """Article version history."""
    __tablename__ = "kb_article_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("kb_articles.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)

    # Change tracking
    changed_by = Column(UUID(as_uuid=True), nullable=False)
    change_summary = Column(Text)
    diff = Column(JSONB)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    article = relationship("Article", back_populates="versions")

    __table_args__ = (UniqueConstraint("article_id", "version", name="uq_article_version"),)


class AnalyticsEvent(Base):
    """Analytics event tracking."""
    __tablename__ = "kb_analytics_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type = Column(String(100), nullable=False, index=True)
    content_id = Column(UUID(as_uuid=True), index=True)
    content_type = Column(String(50), index=True)
    user_id = Column(UUID(as_uuid=True), index=True)
    session_id = Column(String(255), nullable=False, index=True)

    # Event data
    metadata = Column(JSONB, default=dict)

    # Context
    user_agent = Column(String(500))
    ip_address = Column(String(50))
    referrer = Column(String(500))

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_kb_analytics_events_content", content_type, content_id, timestamp),
        Index("ix_kb_analytics_events_user", user_id, timestamp),
    )


class ChatSession(Base):
    """Chatbot session."""
    __tablename__ = "kb_chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    language = Column(String(10), default="en")
    is_active = Column(Boolean, default=True)

    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime)
    last_message_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    """Chat message."""
    __tablename__ = "kb_chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("kb_chat_sessions.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)

    # AI metadata
    intent = Column(String(100))
    confidence = Column(Float)
    suggested_articles = Column(ARRAY(UUID(as_uuid=True)))

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationship
    session = relationship("ChatSession", back_populates="messages")


class ReviewWorkflow(Base):
    """Content review workflow."""
    __tablename__ = "kb_review_workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    content_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    content_type = Column(String(50), nullable=False, index=True)

    # Workflow
    status = Column(String(50), default="pending", index=True)
    reviewer_id = Column(UUID(as_uuid=True), index=True)

    # Feedback
    comments = Column(ARRAY(Text))
    required_changes = Column(ARRAY(Text))

    # Timestamps
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime)


class ContentTemplate(Base):
    """Content template."""
    __tablename__ = "kb_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    content_type = Column(String(50), nullable=False, index=True)

    # Template content
    template_content = Column(Text, nullable=False)
    placeholders = Column(ARRAY(String))
    sections = Column(JSONB, default=list)

    # Metadata
    category = Column(String(100))
    template_tags = Column(ARRAY(String))
    is_active = Column(Boolean, default=True, index=True)
    usage_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
