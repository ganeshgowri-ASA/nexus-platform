"""Database models for NEXUS Platform."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    BigInteger,
    Enum,
    Index,
    Table,
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
import enum


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Association table for file sharing
file_shares = Table(
    'file_shares',
    Base.metadata,
    Column('file_id', Integer, ForeignKey('files.id', ondelete='CASCADE')),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('permission', String(20)),  # owner, editor, commenter, viewer
    Column('shared_at', DateTime, default=datetime.utcnow),
)


# Association table for file tags
file_tags = Table(
    'file_tags',
    Base.metadata,
    Column('file_id', Integer, ForeignKey('files.id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE')),
)


class PermissionLevel(enum.Enum):
    """File permission levels."""
    OWNER = "owner"
    EDITOR = "editor"
    COMMENTER = "commenter"
    VIEWER = "viewer"


class User(Base):
    """User model."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    files = relationship("File", back_populates="owner", foreign_keys="File.owner_id")
    file_versions = relationship("FileVersion", back_populates="user")
    folders = relationship("Folder", back_populates="owner")
    access_logs = relationship("FileAccessLog", back_populates="user")


class Folder(Base):
    """Folder model for organizing files."""
    __tablename__ = 'folders'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey('folders.id', ondelete='CASCADE'), nullable=True)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    path = Column(Text)  # Full path for quick lookups
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="folders")
    parent = relationship("Folder", remote_side=[id], backref="children")
    files = relationship("File", back_populates="folder")

    # Indexes
    __table_args__ = (
        Index('idx_folder_owner', 'owner_id'),
        Index('idx_folder_parent', 'parent_id'),
        Index('idx_folder_deleted', 'is_deleted'),
    )


class File(Base):
    """File model for storing file metadata."""
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)  # Physical path on disk/cloud
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    mime_type = Column(String(100))
    file_hash = Column(String(64), index=True)  # SHA-256 hash

    # File organization
    folder_id = Column(Integer, ForeignKey('folders.id', ondelete='SET NULL'), nullable=True)
    category = Column(String(50))  # document, image, video, audio, archive, other
    description = Column(Text)

    # Ownership and tracking
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    last_modified_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))

    # Version control
    version_number = Column(Integer, default=1)
    current_version_id = Column(Integer, ForeignKey('file_versions.id', ondelete='SET NULL'))

    # Status flags
    is_favorite = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Metadata
    thumbnail_path = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)  # For search
    download_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    last_modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="files", foreign_keys=[owner_id])
    folder = relationship("Folder", back_populates="files")
    versions = relationship("FileVersion", back_populates="file", foreign_keys="FileVersion.file_id")
    tags = relationship("Tag", secondary=file_tags, back_populates="files")
    access_logs = relationship("FileAccessLog", back_populates="file")
    public_links = relationship("PublicLink", back_populates="file")

    # Indexes
    __table_args__ = (
        Index('idx_file_owner', 'owner_id'),
        Index('idx_file_folder', 'folder_id'),
        Index('idx_file_category', 'category'),
        Index('idx_file_deleted', 'is_deleted'),
        Index('idx_file_hash', 'file_hash'),
        Index('idx_file_uploaded', 'uploaded_at'),
    )


class FileVersion(Base):
    """File version history."""
    __tablename__ = 'file_versions'

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey('files.id', ondelete='CASCADE'), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_path = Column(Text, nullable=False)  # Path to versioned file
    file_size = Column(BigInteger, nullable=False)
    file_hash = Column(String(64))

    # Change tracking
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    changes_description = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    file = relationship("File", back_populates="versions", foreign_keys=[file_id])
    user = relationship("User", back_populates="file_versions")

    # Indexes
    __table_args__ = (
        Index('idx_version_file', 'file_id'),
        Index('idx_version_number', 'file_id', 'version_number'),
    )


class Tag(Base):
    """Tag model for file categorization."""
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    color = Column(String(7), default='#808080')  # Hex color code
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    files = relationship("File", secondary=file_tags, back_populates="tags")


class PublicLink(Base):
    """Public sharing links for files."""
    __tablename__ = 'public_links'

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey('files.id', ondelete='CASCADE'), nullable=False)
    link_token = Column(String(64), unique=True, index=True, nullable=False)

    # Access control
    password_hash = Column(String(255), nullable=True)
    max_downloads = Column(Integer, nullable=True)
    download_count = Column(Integer, default=0)
    allow_download = Column(Boolean, default=True)

    # Expiration
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Tracking
    created_by = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed_at = Column(DateTime, nullable=True)

    # Relationships
    file = relationship("File", back_populates="public_links")

    # Indexes
    __table_args__ = (
        Index('idx_link_token', 'link_token'),
        Index('idx_link_file', 'file_id'),
        Index('idx_link_active', 'is_active'),
    )


class FileAccessLog(Base):
    """Audit log for file access."""
    __tablename__ = 'file_access_logs'

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey('files.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Access details
    action = Column(String(50), nullable=False)  # view, download, edit, delete, share
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # Timestamp
    accessed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    file = relationship("File", back_populates="access_logs")
    user = relationship("User", back_populates="access_logs")

    # Indexes
    __table_args__ = (
        Index('idx_access_file', 'file_id'),
        Index('idx_access_user', 'user_id'),
        Index('idx_access_action', 'action'),
        Index('idx_access_time', 'accessed_at'),
    )


class Document(Base):
    """Document model for word processing, spreadsheets, presentations."""
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey('files.id', ondelete='CASCADE'), nullable=True)
    title = Column(String(255), nullable=False)
    doc_type = Column(String(50))  # word, excel, powerpoint, etc.
    content = Column(Text)

    # Ownership
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_doc_owner', 'owner_id'),
        Index('idx_doc_type', 'doc_type'),
    )
