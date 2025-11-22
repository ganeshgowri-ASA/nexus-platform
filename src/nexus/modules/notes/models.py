"""Database models for notes module."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from nexus.core.database import Base

import enum


class PermissionLevel(str, enum.Enum):
    """Permission levels for note sharing."""

    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"
    ADMIN = "admin"


class NoteStatus(str, enum.Enum):
    """Status of a note."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class TemplateType(str, enum.Enum):
    """Types of note templates."""

    MEETING = "meeting"
    PROJECT = "project"
    TODO = "todo"
    JOURNAL = "journal"
    CUSTOM = "custom"


class Notebook(Base):
    """Notebook model for organizing notes."""

    __tablename__ = "notebooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(50), default="#4A90E2")
    icon = Column(String(50), default="📓")
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sections = relationship("Section", back_populates="notebook", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="notebook")

    __table_args__ = (Index("ix_notebooks_user_id_name", "user_id", "name"),)


class Section(Base):
    """Section model for organizing notes within notebooks."""

    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    notebook_id = Column(Integer, ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    notebook = relationship("Notebook", back_populates="sections")
    notes = relationship("Note", back_populates="section")

    __table_args__ = (Index("ix_sections_notebook_id_order", "notebook_id", "order"),)


class Note(Base):
    """Main note model."""

    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    notebook_id = Column(Integer, ForeignKey("notebooks.id"), nullable=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=True, index=True)

    # Content
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    content_html = Column(Text, nullable=True)
    content_markdown = Column(Text, nullable=True)

    # Metadata
    status = Column(
        Enum(NoteStatus), default=NoteStatus.ACTIVE, nullable=False, index=True
    )
    is_favorite = Column(Boolean, default=False, index=True)
    is_pinned = Column(Boolean, default=False)
    color = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    last_viewed_at = Column(DateTime, nullable=True)

    # Collaboration
    shared_with = Column(JSON, nullable=True)  # List of user IDs and permissions
    is_public = Column(Boolean, default=False, index=True)

    # Integration
    calendar_event_id = Column(String(255), nullable=True, index=True)
    project_id = Column(Integer, nullable=True, index=True)
    chat_id = Column(String(255), nullable=True, index=True)

    # AI metadata
    ai_summary = Column(Text, nullable=True)
    ai_tags = Column(JSON, nullable=True)  # Auto-generated tags
    extracted_tasks = Column(JSON, nullable=True)  # Auto-extracted tasks

    # Version tracking
    version = Column(Integer, default=1)
    parent_version_id = Column(Integer, ForeignKey("note_versions.id"), nullable=True)

    # Relationships
    notebook = relationship("Notebook", back_populates="notes")
    section = relationship("Section", back_populates="notes")
    tags = relationship("Tag", secondary="note_tags", back_populates="notes")
    attachments = relationship("Attachment", back_populates="note", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="note", cascade="all, delete-orphan")
    versions = relationship("NoteVersion", back_populates="note", foreign_keys="NoteVersion.note_id")

    __table_args__ = (
        Index("ix_notes_user_id_status", "user_id", "status"),
        Index("ix_notes_user_id_favorite", "user_id", "is_favorite"),
        Index("ix_notes_updated_at", "updated_at"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert note to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "notebook_id": self.notebook_id,
            "section_id": self.section_id,
            "title": self.title,
            "content": self.content,
            "status": self.status.value if self.status else None,
            "is_favorite": self.is_favorite,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": [tag.name for tag in self.tags] if self.tags else [],
        }


class NoteVersion(Base):
    """Version history for notes."""

    __tablename__ = "note_versions"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)

    # Content snapshot
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    content_html = Column(Text, nullable=True)

    # Metadata
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    change_summary = Column(String(500), nullable=True)

    # Relationships
    note = relationship("Note", back_populates="versions", foreign_keys=[note_id])

    __table_args__ = (
        Index("ix_note_versions_note_id_version", "note_id", "version", unique=True),
    )


class Tag(Base):
    """Tag model for categorizing notes."""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    color = Column(String(50), default="#6B7280")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    notes = relationship("Note", secondary="note_tags", back_populates="tags")

    __table_args__ = (Index("ix_tags_user_id_name", "user_id", "name", unique=True),)


# Association table for many-to-many relationship between notes and tags
class NoteTag(Base):
    """Association table for notes and tags."""

    __tablename__ = "note_tags"

    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Template(Base):
    """Template model for creating notes from predefined structures."""

    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)  # NULL for system templates
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(Enum(TemplateType), default=TemplateType.CUSTOM, index=True)
    content = Column(Text, nullable=False)
    content_html = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False, index=True)
    is_public = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("ix_templates_user_id_type", "user_id", "template_type"),)


class Attachment(Base):
    """Attachment model for files, images, audio, etc."""

    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_type = Column(String(100), nullable=False)  # image, audio, video, document, link
    mime_type = Column(String(200), nullable=True)
    file_size = Column(Integer, nullable=True)  # in bytes
    file_path = Column(String(1000), nullable=True)  # local file path or URL
    url = Column(String(2000), nullable=True)  # for links
    thumbnail_path = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    note = relationship("Note", back_populates="attachments")

    __table_args__ = (Index("ix_attachments_note_id_type", "note_id", "file_type"),)


class Comment(Base):
    """Comment model for collaborative notes."""

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)  # For threaded comments
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    note = relationship("Note", back_populates="comments")
    replies = relationship("Comment", backref="parent", remote_side=[id])

    __table_args__ = (Index("ix_comments_note_id_created", "note_id", "created_at"),)


class SavedSearch(Base):
    """Saved search queries for quick access."""

    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    query = Column(String(1000), nullable=False)
    filters = Column(JSON, nullable=True)  # Tag filters, date ranges, etc.
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    __table_args__ = (Index("ix_saved_searches_user_id_pinned", "user_id", "is_pinned"),)
