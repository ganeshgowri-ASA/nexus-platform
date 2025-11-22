"""
<<<<<<< HEAD
Database configuration and models for NEXUS platform.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine,
    Boolean,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum,
    JSON,
    Float,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import StaticPool
import enum

from config import settings

# Create engine
engine = create_engine(
    str(settings.database_url),
    pool_pre_ping=True,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Enums
class ContentStatus(str, enum.Enum):
    """Content status enum."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    ARCHIVED = "archived"


class ContentType(str, enum.Enum):
    """Content type enum."""

    SOCIAL_POST = "social_post"
    BLOG_POST = "blog_post"
    EMAIL = "email"
    VIDEO = "video"
    IMAGE = "image"
    STORY = "story"
    REEL = "reel"
    ARTICLE = "article"


class Channel(str, enum.Enum):
    """Publishing channel enum."""

    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    BLOG = "blog"
    EMAIL = "email"


class WorkflowStatus(str, enum.Enum):
    """Workflow status enum."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


# Models
class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    avatar_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    content_items = relationship("ContentItem", back_populates="creator")
    assignments = relationship("Assignment", back_populates="assignee")
    comments = relationship("Comment", back_populates="author")
    approvals = relationship("Approval", back_populates="reviewer")


class ContentItem(Base):
    """Content item model."""

    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(Enum(ContentType), nullable=False)
    status = Column(Enum(ContentStatus), default=ContentStatus.DRAFT)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)

    # Scheduling
    scheduled_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    timezone = Column(String(50), default="UTC")

    # Channels
    channels = Column(JSON, default=list)  # List of channels to publish to

    # Media
    media_urls = Column(JSON, default=list)
    thumbnail_url = Column(String(500))

    # Metadata
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    version = Column(Integer, default=1)

    # Analytics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="content_items")
    campaign = relationship("Campaign", back_populates="content_items")
    assignments = relationship("Assignment", back_populates="content_item")
    comments = relationship("Comment", back_populates="content_item")
    approvals = relationship("Approval", back_populates="content_item")
    versions = relationship("ContentVersion", back_populates="content_item")


class Campaign(Base):
    """Campaign model for organizing content."""

    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String(50), default="active")
    budget = Column(Float, nullable=True)
    goals = Column(JSON, default=dict)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    content_items = relationship("ContentItem", back_populates="campaign")


class Assignment(Base):
    """Assignment model for task management."""

    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    content_item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(100))  # writer, editor, reviewer, etc.
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING)
    due_date = Column(DateTime, nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    content_item = relationship("ContentItem", back_populates="assignments")
    assignee = relationship("User", back_populates="assignments")


class Comment(Base):
    """Comment model for collaboration."""

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content_item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    content_item = relationship("ContentItem", back_populates="comments")
    author = relationship("User", back_populates="comments")
    replies = relationship("Comment", backref="parent", remote_side=[id])


class Approval(Base):
    """Approval model for workflow management."""

    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    content_item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING)
    feedback = Column(Text)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    content_item = relationship("ContentItem", back_populates="approvals")
    reviewer = relationship("User", back_populates="approvals")


class ContentVersion(Base):
    """Content version for version control."""

    __tablename__ = "content_versions"

    id = Column(Integer, primary_key=True, index=True)
    content_item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    title = Column(String(500))
    content = Column(Text)
    changes_summary = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    content_item = relationship("ContentItem", back_populates="versions")


class Template(Base):
    """Content template model."""

    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    content_type = Column(Enum(ContentType), nullable=False)
    template_content = Column(Text, nullable=False)
    variables = Column(JSON, default=list)  # List of variable names
    is_active = Column(Boolean, default=True)
    category = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Analytics(Base):
    """Analytics model for tracking performance."""

    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    content_item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    channel = Column(Enum(Channel), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(JSON, default=dict)


# Database utilities
def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)
=======
Database configuration and session management.
"""
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import get_settings

settings = get_settings()

# Async engine for FastAPI
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Sync engine for Celery and migrations
sync_engine = create_engine(
    settings.database_sync_url,
    echo=settings.environment == "development",
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Async session maker
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi
