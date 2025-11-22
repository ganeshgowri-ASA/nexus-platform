"""
SQLAlchemy database models for NEXUS Platform.

This module contains all core database models for the 24-module integrated platform,
including User, Document, Email, Chat, Project, Task, File, and AI_Interaction models.
"""

from typing import Optional
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSON, JSONB

from database.connection import Base


class User(Base):
    """
    User model for authentication and authorization.

    Stores user account information, preferences, and access control data.
    Supports role-based access control (RBAC) with admin, manager, user, and guest roles.
    """

    __tablename__ = "users"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Authentication
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile Information
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Authorization
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="user",
        server_default=text("'user'"),
        index=True
    )  # admin, manager, user, guest

    # User Preferences (stored as JSON)
    preferences: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))

    # Status Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    emails: Mapped[list["Email"]] = relationship("Email", back_populates="user", cascade="all, delete-orphan")
    chats: Mapped[list["Chat"]] = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    assigned_tasks: Mapped[list["Task"]] = relationship("Task", back_populates="assignee", foreign_keys="Task.assignee_id")
    files: Mapped[list["File"]] = relationship("File", back_populates="user", cascade="all, delete-orphan")
    ai_interactions: Mapped[list["AIInteraction"]] = relationship("AIInteraction", back_populates="user", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_users_role_active', 'role', 'is_active'),
        Index('ix_users_email_active', 'email', 'is_active'),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Document(Base):
    """
    Document model for Word, Excel, and PowerPoint files.

    Stores document content, metadata, versioning, and sharing information.
    Supports collaborative editing with version control and permission management.
    """

    __tablename__ = "documents"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Document Information
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # word, excel, ppt
    file_path: Mapped[Optional[str]] = mapped_column(String(1000))

    # Content and Version Control
    content: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))

    # Collaboration and Permissions
    shared_with: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))  # User IDs and permissions
    permissions: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))  # Detailed access control

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # Soft delete

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="documents")

    # Indexes
    __table_args__ = (
        Index('ix_documents_user_type', 'user_id', 'type'),
        Index('ix_documents_deleted_at', 'deleted_at'),
        Index('ix_documents_user_deleted', 'user_id', 'deleted_at'),
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title='{self.title}', type='{self.type}')>"


class Email(Base):
    """
    Email model for internal messaging system.

    Stores email messages with full support for attachments, threading,
    and status tracking (draft, sent, received).
    """

    __tablename__ = "emails"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Email Addressing
    from_addr: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    to_addr: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cc: Mapped[Optional[str]] = mapped_column(String(1000))
    bcc: Mapped[Optional[str]] = mapped_column(String(1000))

    # Email Content
    subject: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    attachments: Mapped[Optional[dict]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))

    # Email Metadata
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        server_default=text("'draft'"),
        index=True
    )  # draft, sent, received
    thread_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)

    # Status Flags
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)

    # Timestamps
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="emails")

    # Indexes
    __table_args__ = (
        Index('ix_emails_user_status', 'user_id', 'status'),
        Index('ix_emails_thread_id', 'thread_id'),
        Index('ix_emails_user_read', 'user_id', 'is_read'),
        Index('ix_emails_from_to', 'from_addr', 'to_addr'),
    )

    def __repr__(self) -> str:
        return f"<Email(id={self.id}, subject='{self.subject}', status='{self.status}')>"


class Chat(Base):
    """
    Chat model for real-time messaging.

    Stores chat messages with support for rooms/channels, threading,
    attachments, and message editing/deletion.
    """

    __tablename__ = "chats"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    replied_to_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("chats.id", ondelete="SET NULL"), index=True)

    # Message Content
    message: Mapped[str] = mapped_column(Text, nullable=False)
    attachments: Mapped[Optional[dict]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))

    # Status Flags
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chats")
    replied_to: Mapped[Optional["Chat"]] = relationship("Chat", remote_side=[id], backref="replies")

    # Indexes
    __table_args__ = (
        Index('ix_chats_room_created', 'room_id', 'created_at'),
        Index('ix_chats_user_room', 'user_id', 'room_id'),
        Index('ix_chats_replied_to', 'replied_to_id'),
    )

    def __repr__(self) -> str:
        return f"<Chat(id={self.id}, user_id={self.user_id}, room_id='{self.room_id}')>"


class Project(Base):
    """
    Project model for project management.

    Stores project information including status, priority, timeline,
    team members, and budget tracking.
    """

    __tablename__ = "projects"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Project Information
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Status and Priority
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="planning",
        server_default=text("'planning'"),
        index=True
    )  # planning, active, completed
    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="medium",
        server_default=text("'medium'"),
        index=True
    )  # low, medium, high, critical

    # Timeline
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completion_percentage: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0")
    )

    # Team and Budget
    team_members: Mapped[Optional[dict]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))  # User IDs and roles
    budget: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="project", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_projects_user_status', 'user_id', 'status'),
        Index('ix_projects_status_priority', 'status', 'priority'),
        Index('ix_projects_start_end', 'start_date', 'end_date'),
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"


class Task(Base):
    """
    Task model for task management within projects.

    Stores task details including assignments, status, priority, timeline,
    time tracking, dependencies, and tags.
    """

    __tablename__ = "tasks"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    assignee_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)

    # Task Information
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Status and Priority
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
        index=True
    )  # pending, in_progress, completed, blocked
    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="medium",
        server_default=text("'medium'"),
        index=True
    )  # low, medium, high, critical

    # Timeline
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Time Tracking
    estimated_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    actual_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))

    # Organization
    dependencies: Mapped[Optional[dict]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))  # Task IDs
    tags: Mapped[Optional[dict]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    assignee: Mapped[Optional["User"]] = relationship("User", back_populates="assigned_tasks", foreign_keys=[assignee_id])

    # Indexes
    __table_args__ = (
        Index('ix_tasks_project_status', 'project_id', 'status'),
        Index('ix_tasks_assignee_status', 'assignee_id', 'status'),
        Index('ix_tasks_status_priority', 'status', 'priority'),
        Index('ix_tasks_due_date', 'due_date'),
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"


class File(Base):
    """
    File model for file storage and management.

    Stores file metadata, paths, types, and download tracking.
    Supports public/private files with comprehensive metadata.
    """

    __tablename__ = "files"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # File Information
    filename: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    hash: Mapped[Optional[str]] = mapped_column(String(255), index=True)  # File hash for deduplication

    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))

    # Access Control
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    download_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="files")

    # Indexes
    __table_args__ = (
        Index('ix_files_user_type', 'user_id', 'file_type'),
        Index('ix_files_hash', 'hash'),
        Index('ix_files_created', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<File(id={self.id}, filename='{self.filename}', size={self.file_size})>"


class AIInteraction(Base):
    """
    AI Interaction model for tracking AI service usage.

    Stores AI prompts, responses, model information, token usage,
    cost tracking, and performance metrics.
    """

    __tablename__ = "ai_interactions"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Interaction Context
    module: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # Which module used AI

    # AI Content
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)

    # AI Metadata
    model_used: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))  # Cost in dollars
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)  # Duration in milliseconds

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="ai_interactions")

    # Indexes
    __table_args__ = (
        Index('ix_ai_interactions_user_module', 'user_id', 'module'),
        Index('ix_ai_interactions_model_created', 'model_used', 'created_at'),
        Index('ix_ai_interactions_user_created', 'user_id', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<AIInteraction(id={self.id}, module='{self.module}', model='{self.model_used}')>"
