<<<<<<< HEAD
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
=======
"""Database models for all applications"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Boolean,
    Float, ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import declarative_base, relationship
import enum
import uuid

Base = declarative_base()

def generate_uuid():
    """Generate unique ID"""
    return str(uuid.uuid4())

# Base Model with common fields
class BaseModel(Base):
    __abstract__ = True

    id = Column(String, primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============================================
# POWERPOINT / PRESENTATION MODELS
# ============================================

class Presentation(BaseModel):
    __tablename__ = 'presentations'

    title = Column(String, nullable=False)
    theme = Column(String, default='Modern Blue')
    description = Column(Text)
    author = Column(String)
    slides_count = Column(Integer, default=0)

class Slide(BaseModel):
    __tablename__ = 'slides'

    presentation_id = Column(String, ForeignKey('presentations.id', ondelete='CASCADE'))
    slide_number = Column(Integer, nullable=False)
    title = Column(String)
    content = Column(Text)
    layout = Column(String, default='title_and_content')
    notes = Column(Text)
    background_color = Column(String)

    presentation = relationship("Presentation", backref="slides")

# ============================================
# EMAIL MODELS
# ============================================

class EmailMessage(BaseModel):
    __tablename__ = 'emails'

    subject = Column(String, nullable=False)
    sender = Column(String, nullable=False)
    recipients = Column(JSON)  # List of email addresses
    cc = Column(JSON)  # List of CC addresses
    bcc = Column(JSON)  # List of BCC addresses
    body = Column(Text)
    html_body = Column(Text)
    is_draft = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)
    category = Column(String, default='Primary')
    thread_id = Column(String)  # For email threading
    parent_id = Column(String, ForeignKey('emails.id'))
    attachments = Column(JSON)  # List of file paths

    replies = relationship("EmailMessage", backref="parent", remote_side=[BaseModel.id])

class EmailDraft(BaseModel):
    __tablename__ = 'email_drafts'

    subject = Column(String)
    recipients = Column(JSON)
    body = Column(Text)
    attachments = Column(JSON)

# ============================================
# CHAT MODELS
# ============================================

class ChatRoom(BaseModel):
    __tablename__ = 'chat_rooms'

    name = Column(String, nullable=False)
    description = Column(Text)
    room_type = Column(String, default='Group Chat')
    members = Column(JSON)  # List of member IDs/names
    is_active = Column(Boolean, default=True)
    avatar = Column(String)

class ChatMessage(BaseModel):
    __tablename__ = 'chat_messages'

    room_id = Column(String, ForeignKey('chat_rooms.id', ondelete='CASCADE'))
    sender = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String, default='text')  # text, file, image, emoji
    attachments = Column(JSON)
    reactions = Column(JSON)  # Dict of emoji: [users]
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    room = relationship("ChatRoom", backref="messages")

# ============================================
# PROJECT MANAGEMENT MODELS
# ============================================

class Project(BaseModel):
    __tablename__ = 'projects'

    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default='Planning')
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    progress = Column(Float, default=0.0)
    owner = Column(String)
    team_members = Column(JSON)
    budget = Column(Float)
    tags = Column(JSON)

class Task(BaseModel):
    __tablename__ = 'tasks'

    project_id = Column(String, ForeignKey('projects.id', ondelete='CASCADE'))
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default='Not Started')
    priority = Column(String, default='Medium')
    assignee = Column(String)
    start_date = Column(DateTime)
    due_date = Column(DateTime)
    completed_date = Column(DateTime)
    progress = Column(Float, default=0.0)
    dependencies = Column(JSON)  # List of task IDs
    estimated_hours = Column(Float)
    actual_hours = Column(Float)

    project = relationship("Project", backref="tasks")

class Milestone(BaseModel):
    __tablename__ = 'milestones'

    project_id = Column(String, ForeignKey('projects.id', ondelete='CASCADE'))
    title = Column(String, nullable=False)
    description = Column(Text)
    due_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    completion_date = Column(DateTime)

    project = relationship("Project", backref="milestones")

# ============================================
# CALENDAR MODELS
# ============================================

class CalendarEvent(BaseModel):
    __tablename__ = 'calendar_events'

    title = Column(String, nullable=False)
    description = Column(Text)
    event_type = Column(String, default='Meeting')
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String)
    attendees = Column(JSON)
    is_all_day = Column(Boolean, default=False)
    recurrence_pattern = Column(String, default='None')
    recurrence_end = Column(DateTime)
    reminder_minutes = Column(Integer, default=15)
    color = Column(String)
    organizer = Column(String)

# ============================================
# VIDEO CONFERENCE MODELS
# ============================================

class VideoConference(BaseModel):
    __tablename__ = 'video_conferences'

    title = Column(String, nullable=False)
    description = Column(Text)
    host = Column(String, nullable=False)
    participants = Column(JSON)
    scheduled_time = Column(DateTime)
    duration_minutes = Column(Integer)
    status = Column(String, default='Scheduled')  # Scheduled, Active, Ended
    recording_url = Column(String)
    is_recording = Column(Boolean, default=False)
    room_id = Column(String, unique=True)

class ConferenceRecording(BaseModel):
    __tablename__ = 'conference_recordings'

    conference_id = Column(String, ForeignKey('video_conferences.id', ondelete='CASCADE'))
    file_path = Column(String, nullable=False)
    duration_seconds = Column(Integer)
    file_size_mb = Column(Float)

    conference = relationship("VideoConference", backref="recordings")

# ============================================
# NOTES MODELS
# ============================================

class Note(BaseModel):
    __tablename__ = 'notes'

    title = Column(String, nullable=False)
    content = Column(Text)
    folder = Column(String, default='General')
    tags = Column(JSON)
    category = Column(String, default='Personal')
    is_favorite = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    color = Column(String)
    ai_summary = Column(Text)
    author = Column(String)

# ============================================
# CRM MODELS
# ============================================

class CRMContact(BaseModel):
    __tablename__ = 'crm_contacts'

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    company = Column(String)
    job_title = Column(String)
    contact_type = Column(String, default='Lead')
    address = Column(Text)
    notes = Column(Text)
    tags = Column(JSON)
    linkedin_url = Column(String)
    twitter_url = Column(String)
    website = Column(String)
    source = Column(String)  # How they were acquired
    owner = Column(String)  # Sales rep assigned

class CRMDeal(BaseModel):
    __tablename__ = 'crm_deals'

    contact_id = Column(String, ForeignKey('crm_contacts.id', ondelete='CASCADE'))
    title = Column(String, nullable=False)
    description = Column(Text)
    value = Column(Float)
    currency = Column(String, default='USD')
    stage = Column(String, default='Lead')
    probability = Column(Float, default=0.0)
    expected_close_date = Column(DateTime)
    actual_close_date = Column(DateTime)
    owner = Column(String)
    tags = Column(JSON)

    contact = relationship("CRMContact", backref="deals")

class CRMActivity(BaseModel):
    __tablename__ = 'crm_activities'

    contact_id = Column(String, ForeignKey('crm_contacts.id', ondelete='CASCADE'))
    deal_id = Column(String, ForeignKey('crm_deals.id', ondelete='SET NULL'))
    activity_type = Column(String, nullable=False)  # Email, Call, Meeting, Note
    subject = Column(String)
    description = Column(Text)
    due_date = Column(DateTime)
    completed_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    owner = Column(String)

    contact = relationship("CRMContact", backref="activities")
    deal = relationship("CRMDeal", backref="activities")
>>>>>>> origin/claude/productivity-suite-ai-01Uq8q3V9EdvDAuMPqDoBxZh
