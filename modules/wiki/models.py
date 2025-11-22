"""
Wiki Database Models

SQLAlchemy ORM models for the NEXUS Wiki System.
Includes tables for pages, categories, tags, links, attachments, history, comments, etc.

Author: NEXUS Platform Team
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Index, Integer,
    String, Text, Table, UniqueConstraint, CheckConstraint, func
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property

from database import Base
from modules.wiki.wiki_types import (
    PageStatus, ContentFormat, PermissionLevel, LinkType,
    AttachmentType, TemplateCategory, ChangeType
)


# ============================================================================
# ASSOCIATION TABLES (Many-to-Many Relationships)
# ============================================================================

page_tags = Table(
    'wiki_page_tags',
    Base.metadata,
    Column('page_id', Integer, ForeignKey('wiki_pages.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('wiki_tags.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False),
    Index('idx_page_tags_page', 'page_id'),
    Index('idx_page_tags_tag', 'tag_id'),
)


page_watchers = Table(
    'wiki_page_watchers',
    Base.metadata,
    Column('page_id', Integer, ForeignKey('wiki_pages.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', Integer, nullable=False, primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False),
    Index('idx_page_watchers_page', 'page_id'),
    Index('idx_page_watchers_user', 'user_id'),
)


# ============================================================================
# CORE MODELS
# ============================================================================

class WikiTag(Base):
    """Tag model for categorizing wiki pages."""
    __tablename__ = 'wiki_tags'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    color = Column(String(7), default='#3498db')
    description = Column(Text, nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    pages = relationship('WikiPage', secondary=page_tags, back_populates='tags')

    def __repr__(self):
        return f"<WikiTag(id={self.id}, name='{self.name}')>"


class WikiCategory(Base):
    """Hierarchical category model for organizing wiki pages."""
    __tablename__ = 'wiki_categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey('wiki_categories.id', ondelete='SET NULL'), nullable=True)
    icon = Column(String(50), nullable=True)
    color = Column(String(7), default='#2c3e50')
    order = Column(Integer, default=0, nullable=False)
    page_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    metadata = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    parent = relationship('WikiCategory', remote_side=[id], back_populates='children')
    children = relationship('WikiCategory', back_populates='parent', cascade='all, delete-orphan')
    pages = relationship('WikiPage', back_populates='category')

    # Indexes
    __table_args__ = (
        Index('idx_category_parent', 'parent_id'),
        Index('idx_category_active', 'is_active'),
    )

    @hybrid_property
    def full_path(self) -> str:
        """Get the full hierarchical path of the category."""
        if self.parent:
            return f"{self.parent.full_path}/{self.slug}"
        return f"/{self.slug}"

    def __repr__(self):
        return f"<WikiCategory(id={self.id}, name='{self.name}')>"


class WikiPage(Base):
    """Main wiki page model."""
    __tablename__ = 'wiki_pages'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False, default='')
    content_format = Column(Enum(ContentFormat), default=ContentFormat.MARKDOWN, nullable=False)
    summary = Column(String(500), nullable=True)
    status = Column(Enum(PageStatus), default=PageStatus.DRAFT, nullable=False, index=True)

    # Organization
    category_id = Column(Integer, ForeignKey('wiki_categories.id', ondelete='SET NULL'), nullable=True)
    parent_page_id = Column(Integer, ForeignKey('wiki_pages.id', ondelete='SET NULL'), nullable=True)
    namespace = Column(String(100), nullable=True, index=True)
    path = Column(String(500), default='/', nullable=False)

    # Metadata
    author_id = Column(Integer, nullable=False, index=True)
    current_version = Column(Integer, default=1, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    published_at = Column(DateTime, nullable=True)
    last_viewed_at = Column(DateTime, nullable=True)

    # Features
    is_featured = Column(Boolean, default=False, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    # Additional data
    metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    category = relationship('WikiCategory', back_populates='pages')
    tags = relationship('WikiTag', secondary=page_tags, back_populates='pages')
    parent_page = relationship('WikiPage', remote_side=[id], back_populates='child_pages')
    child_pages = relationship('WikiPage', back_populates='parent_page', cascade='all, delete-orphan')
    sections = relationship('WikiSection', back_populates='page', cascade='all, delete-orphan')
    attachments = relationship('WikiAttachment', back_populates='page', cascade='all, delete-orphan')
    links_from = relationship('WikiLink', foreign_keys='WikiLink.source_page_id', back_populates='source_page', cascade='all, delete-orphan')
    links_to = relationship('WikiLink', foreign_keys='WikiLink.target_page_id', back_populates='target_page')
    comments = relationship('WikiComment', back_populates='page', cascade='all, delete-orphan')
    history = relationship('WikiHistory', back_populates='page', cascade='all, delete-orphan', order_by='WikiHistory.version.desc()')
    permissions = relationship('WikiPermission', back_populates='page', cascade='all, delete-orphan')

    # Indexes
    __table_args__ = (
        UniqueConstraint('namespace', 'slug', name='uq_page_namespace_slug'),
        Index('idx_page_author', 'author_id'),
        Index('idx_page_category', 'category_id'),
        Index('idx_page_parent', 'parent_page_id'),
        Index('idx_page_status_deleted', 'status', 'is_deleted'),
        Index('idx_page_created', 'created_at'),
        CheckConstraint('view_count >= 0', name='check_view_count'),
        CheckConstraint('like_count >= 0', name='check_like_count'),
        CheckConstraint('comment_count >= 0', name='check_comment_count'),
    )

    @hybrid_property
    def full_path(self) -> str:
        """Get the full path of the page."""
        if self.namespace:
            return f"/{self.namespace}/{self.slug}"
        return f"/{self.slug}"

    @hybrid_property
    def content_size(self) -> int:
        """Get the size of the content in bytes."""
        return len(self.content.encode('utf-8'))

    def __repr__(self):
        return f"<WikiPage(id={self.id}, title='{self.title}', status='{self.status}')>"


class WikiSection(Base):
    """Section within a wiki page for structured content."""
    __tablename__ = 'wiki_sections'

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey('wiki_pages.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False, default='')
    order = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    anchor_id = Column(String(100), nullable=False)
    parent_section_id = Column(Integer, ForeignKey('wiki_sections.id', ondelete='CASCADE'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    page = relationship('WikiPage', back_populates='sections')
    parent_section = relationship('WikiSection', remote_side=[id], back_populates='child_sections')
    child_sections = relationship('WikiSection', back_populates='parent_section')

    # Indexes
    __table_args__ = (
        Index('idx_section_page', 'page_id'),
        Index('idx_section_order', 'page_id', 'order'),
        CheckConstraint('level >= 1 AND level <= 6', name='check_section_level'),
    )

    def __repr__(self):
        return f"<WikiSection(id={self.id}, title='{self.title}', level={self.level})>"


class WikiLink(Base):
    """Links between wiki pages or to external resources."""
    __tablename__ = 'wiki_links'

    id = Column(Integer, primary_key=True, index=True)
    source_page_id = Column(Integer, ForeignKey('wiki_pages.id', ondelete='CASCADE'), nullable=False)
    target_page_id = Column(Integer, ForeignKey('wiki_pages.id', ondelete='SET NULL'), nullable=True)
    target_url = Column(String(2000), nullable=True)
    link_type = Column(Enum(LinkType), default=LinkType.INTERNAL, nullable=False)
    anchor = Column(String(100), nullable=True)
    title = Column(String(200), nullable=True)
    is_broken = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_checked_at = Column(DateTime, nullable=True)

    # Relationships
    source_page = relationship('WikiPage', foreign_keys=[source_page_id], back_populates='links_from')
    target_page = relationship('WikiPage', foreign_keys=[target_page_id], back_populates='links_to')

    # Indexes
    __table_args__ = (
        Index('idx_link_source', 'source_page_id'),
        Index('idx_link_target', 'target_page_id'),
        Index('idx_link_broken', 'is_broken'),
        CheckConstraint(
            '(target_page_id IS NOT NULL AND target_url IS NULL) OR '
            '(target_page_id IS NULL AND target_url IS NOT NULL)',
            name='check_link_target'
        ),
    )

    def __repr__(self):
        return f"<WikiLink(id={self.id}, type='{self.link_type}')>"


class WikiAttachment(Base):
    """File attachments for wiki pages."""
    __tablename__ = 'wiki_attachments'

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey('wiki_pages.id', ondelete='CASCADE'), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    attachment_type = Column(Enum(AttachmentType), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    description = Column(Text, nullable=True)
    uploaded_by = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    page = relationship('WikiPage', back_populates='attachments')

    # Indexes
    __table_args__ = (
        Index('idx_attachment_page', 'page_id'),
        Index('idx_attachment_uploader', 'uploaded_by'),
        Index('idx_attachment_type', 'attachment_type'),
        CheckConstraint('file_size >= 0', name='check_file_size'),
    )

    @hybrid_property
    def file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size / (1024 * 1024)

    def __repr__(self):
        return f"<WikiAttachment(id={self.id}, filename='{self.filename}')>"


class WikiComment(Base):
    """Comments and discussions on wiki pages."""
    __tablename__ = 'wiki_comments'

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey('wiki_pages.id', ondelete='CASCADE'), nullable=False)
    parent_comment_id = Column(Integer, ForeignKey('wiki_comments.id', ondelete='CASCADE'), nullable=True)
    author_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    mentions = Column(ARRAY(Integer), default=list, nullable=False)
    reactions = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    page = relationship('WikiPage', back_populates='comments')
    parent_comment = relationship('WikiComment', remote_side=[id], back_populates='replies')
    replies = relationship('WikiComment', back_populates='parent_comment', cascade='all, delete-orphan')

    # Indexes
    __table_args__ = (
        Index('idx_comment_page', 'page_id'),
        Index('idx_comment_author', 'author_id'),
        Index('idx_comment_parent', 'parent_comment_id'),
        Index('idx_comment_created', 'created_at'),
    )

    def __repr__(self):
        return f"<WikiComment(id={self.id}, page_id={self.page_id})>"


class WikiHistory(Base):
    """Version history for wiki pages."""
    __tablename__ = 'wiki_history'

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey('wiki_pages.id', ondelete='CASCADE'), nullable=False)
    version = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    change_type = Column(Enum(ChangeType), default=ChangeType.EDITED, nullable=False)
    change_summary = Column(Text, nullable=True)
    changed_by = Column(Integer, nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    content_size = Column(Integer, default=0, nullable=False)
    diff_size = Column(Integer, default=0, nullable=False)
    metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    page = relationship('WikiPage', back_populates='history')

    # Indexes
    __table_args__ = (
        UniqueConstraint('page_id', 'version', name='uq_page_version'),
        Index('idx_history_page', 'page_id'),
        Index('idx_history_version', 'page_id', 'version'),
        Index('idx_history_changed_by', 'changed_by'),
        Index('idx_history_changed_at', 'changed_at'),
    )

    def __repr__(self):
        return f"<WikiHistory(id={self.id}, page_id={self.page_id}, version={self.version})>"


class WikiPermission(Base):
    """Access permissions for wiki pages and categories."""
    __tablename__ = 'wiki_permissions'

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey('wiki_pages.id', ondelete='CASCADE'), nullable=True)
    category_id = Column(Integer, ForeignKey('wiki_categories.id', ondelete='CASCADE'), nullable=True)
    user_id = Column(Integer, nullable=True)
    role = Column(String(50), nullable=True)
    permission_level = Column(Enum(PermissionLevel), nullable=False)
    granted_by = Column(Integer, nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    is_inherited = Column(Boolean, default=False, nullable=False)

    # Relationships
    page = relationship('WikiPage', back_populates='permissions')
    category = relationship('WikiCategory')

    # Indexes
    __table_args__ = (
        Index('idx_permission_page', 'page_id'),
        Index('idx_permission_category', 'category_id'),
        Index('idx_permission_user', 'user_id'),
        Index('idx_permission_role', 'role'),
        CheckConstraint(
            '(page_id IS NOT NULL AND category_id IS NULL) OR '
            '(page_id IS NULL AND category_id IS NOT NULL)',
            name='check_permission_target'
        ),
        CheckConstraint(
            '(user_id IS NOT NULL AND role IS NULL) OR '
            '(user_id IS NULL AND role IS NOT NULL)',
            name='check_permission_subject'
        ),
    )

    def __repr__(self):
        return f"<WikiPermission(id={self.id}, level='{self.permission_level}')>"


class WikiTemplate(Base):
    """Page templates for quick page creation."""
    __tablename__ = 'wiki_templates'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    category = Column(Enum(TemplateCategory), nullable=False)
    content = Column(Text, nullable=False)
    thumbnail = Column(String(500), nullable=True)
    variables = Column(ARRAY(String), default=list, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_template_category', 'category'),
        Index('idx_template_public', 'is_public'),
    )

    def __repr__(self):
        return f"<WikiTemplate(id={self.id}, name='{self.name}')>"


class WikiAnalytics(Base):
    """Analytics and metrics for wiki pages."""
    __tablename__ = 'wiki_analytics'

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey('wiki_pages.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, nullable=True)
    event_type = Column(String(50), nullable=False)
    event_data = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    session_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_analytics_page', 'page_id'),
        Index('idx_analytics_user', 'user_id'),
        Index('idx_analytics_event', 'event_type'),
        Index('idx_analytics_date', 'created_at'),
        Index('idx_analytics_session', 'session_id'),
    )

    def __repr__(self):
        return f"<WikiAnalytics(id={self.id}, event='{self.event_type}')>"


class WikiMacro(Base):
    """Custom macros for dynamic content."""
    __tablename__ = 'wiki_macros'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    code = Column(Text, nullable=False)
    parameters = Column(JSONB, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<WikiMacro(id={self.id}, name='{self.name}')>"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_all_tables():
    """Create all wiki tables in the database."""
    from database import engine
    Base.metadata.create_all(bind=engine, tables=[
        WikiTag.__table__,
        WikiCategory.__table__,
        WikiPage.__table__,
        WikiSection.__table__,
        WikiLink.__table__,
        WikiAttachment.__table__,
        WikiComment.__table__,
        WikiHistory.__table__,
        WikiPermission.__table__,
        WikiTemplate.__table__,
        WikiAnalytics.__table__,
        WikiMacro.__table__,
    ])


def drop_all_tables():
    """Drop all wiki tables from the database."""
    from database import engine
    Base.metadata.drop_all(bind=engine, tables=[
        WikiTag.__table__,
        WikiCategory.__table__,
        WikiPage.__table__,
        WikiSection.__table__,
        WikiLink.__table__,
        WikiAttachment.__table__,
        WikiComment.__table__,
        WikiHistory.__table__,
        WikiPermission.__table__,
        WikiTemplate.__table__,
        WikiAnalytics.__table__,
        WikiMacro.__table__,
    ])
