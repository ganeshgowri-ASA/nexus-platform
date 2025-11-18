"""
Document management database models.

This module defines all models related to document management including
documents, folders, versions, metadata, tags, permissions, and more.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    BigInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.models.base import BaseModel


class DocumentStatus(str, PyEnum):
    """Document status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    LOCKED = "locked"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class AccessLevel(str, PyEnum):
    """Access level enumeration."""

    NONE = "none"
    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"
    ADMIN = "admin"


class ShareType(str, PyEnum):
    """Share type enumeration."""

    PRIVATE = "private"
    LINK = "link"
    PUBLIC = "public"


class WorkflowStatus(str, PyEnum):
    """Workflow status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Document(BaseModel):
    """
    Document model representing files in the system.

    Attributes:
        title: Document title
        description: Document description
        file_name: Original file name
        file_path: Path to file in storage
        file_size: File size in bytes
        mime_type: MIME type
        file_hash: SHA-256 hash for deduplication
        status: Document status
        owner_id: User who owns the document
        folder_id: Parent folder
        is_public: Whether document is publicly accessible
        view_count: Number of views
        download_count: Number of downloads
        current_version: Current version number
        is_locked: Whether document is locked for editing
        locked_by_id: User who locked the document
        locked_at: When document was locked
        retention_date: Date when document can be deleted
        is_on_legal_hold: Whether document is on legal hold
    """

    __tablename__ = "documents"

    # Basic info
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # File info
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(200), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256

    # Status
    status = Column(
        Enum(DocumentStatus), default=DocumentStatus.ACTIVE, nullable=False, index=True
    )

    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True, index=True)

    # Access control
    is_public = Column(Boolean, default=False, nullable=False)

    # Metrics
    view_count = Column(Integer, default=0, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)

    # Versioning
    current_version = Column(Integer, default=1, nullable=False)

    # Locking
    is_locked = Column(Boolean, default=False, nullable=False)
    locked_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    locked_at = Column(DateTime, nullable=True)

    # Retention & compliance
    retention_date = Column(DateTime, nullable=True)
    is_on_legal_hold = Column(Boolean, default=False, nullable=False)

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    folder = relationship("Folder", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    metadata_entries = relationship("DocumentMetadata", back_populates="document", cascade="all, delete-orphan")
    tags = relationship("DocumentTag", back_populates="document", cascade="all, delete-orphan")
    permissions = relationship("DocumentPermission", back_populates="document", cascade="all, delete-orphan")
    comments = relationship("DocumentComment", back_populates="document", cascade="all, delete-orphan")
    audit_logs = relationship("DocumentAuditLog", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_document_owner_status", "owner_id", "status"),
        Index("idx_document_folder_status", "folder_id", "status"),
    )


class Folder(BaseModel):
    """
    Folder model for organizing documents.

    Attributes:
        name: Folder name
        description: Folder description
        path: Full path to folder
        parent_id: Parent folder ID
        owner_id: Folder owner
        is_public: Whether folder is publicly accessible
        color: Folder color (hex)
        icon: Folder icon name
    """

    __tablename__ = "folders"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    path = Column(String(2000), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("folders.id"), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_public = Column(Boolean, default=False, nullable=False)
    color = Column(String(7), nullable=True)  # Hex color
    icon = Column(String(50), nullable=True)

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    parent = relationship("Folder", remote_side="Folder.id", backref="subfolders")
    documents = relationship("Document", back_populates="folder")
    permissions = relationship("FolderPermission", back_populates="folder", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("owner_id", "parent_id", "name", name="uq_folder_path"),
    )


class DocumentVersion(BaseModel):
    """
    Document version history.

    Attributes:
        document_id: Document ID
        version_number: Version number
        file_path: Path to version file
        file_size: File size
        file_hash: File hash
        change_summary: Summary of changes
        created_by_id: User who created version
    """

    __tablename__ = "document_versions"

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_hash = Column(String(64), nullable=False)
    change_summary = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="versions")
    created_by = relationship("User", foreign_keys=[created_by_id])

    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_document_version"),
        Index("idx_version_document", "document_id", "version_number"),
    )


class DocumentMetadata(BaseModel):
    """
    Document metadata key-value pairs.

    Attributes:
        document_id: Document ID
        key: Metadata key
        value: Metadata value
        value_type: Type of value (string, number, date, etc.)
        is_system: Whether this is system metadata
    """

    __tablename__ = "document_metadata"

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    key = Column(String(255), nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(50), default="string", nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="metadata_entries")

    __table_args__ = (
        UniqueConstraint("document_id", "key", name="uq_document_metadata"),
    )


class Tag(BaseModel):
    """
    Tag model for categorization.

    Attributes:
        name: Tag name
        color: Tag color
        created_by_id: User who created tag
    """

    __tablename__ = "tags"

    name = Column(String(100), unique=True, nullable=False, index=True)
    color = Column(String(7), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    document_tags = relationship("DocumentTag", back_populates="tag", cascade="all, delete-orphan")


class DocumentTag(BaseModel):
    """
    Association between documents and tags.

    Attributes:
        document_id: Document ID
        tag_id: Tag ID
        added_by_id: User who added tag
    """

    __tablename__ = "document_tags"

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False, index=True)
    added_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="tags")
    tag = relationship("Tag", back_populates="document_tags")
    added_by = relationship("User", foreign_keys=[added_by_id])

    __table_args__ = (
        UniqueConstraint("document_id", "tag_id", name="uq_document_tag"),
    )


class DocumentPermission(BaseModel):
    """
    Document-level permissions.

    Attributes:
        document_id: Document ID
        user_id: User ID (nullable for group permissions)
        access_level: Access level
        granted_by_id: User who granted permission
        expires_at: Permission expiration
    """

    __tablename__ = "document_permissions"

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    access_level = Column(Enum(AccessLevel), nullable=False)
    granted_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="permissions")
    user = relationship("User", foreign_keys=[user_id])
    granted_by = relationship("User", foreign_keys=[granted_by_id])

    __table_args__ = (
        Index("idx_permission_user_document", "user_id", "document_id"),
    )


class FolderPermission(BaseModel):
    """
    Folder-level permissions.

    Attributes:
        folder_id: Folder ID
        user_id: User ID
        access_level: Access level
        granted_by_id: User who granted permission
        is_inherited: Whether permission is inherited
    """

    __tablename__ = "folder_permissions"

    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    access_level = Column(Enum(AccessLevel), nullable=False)
    granted_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_inherited = Column(Boolean, default=False, nullable=False)

    # Relationships
    folder = relationship("Folder", back_populates="permissions")
    user = relationship("User", foreign_keys=[user_id])
    granted_by = relationship("User", foreign_keys=[granted_by_id])


class ShareLink(BaseModel):
    """
    Shareable links for documents.

    Attributes:
        document_id: Document ID
        token: Unique share token
        share_type: Type of share
        access_level: Access level
        password_hash: Optional password protection
        expires_at: Link expiration
        max_downloads: Maximum downloads allowed
        download_count: Current download count
        created_by_id: User who created link
    """

    __tablename__ = "share_links"

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    token = Column(String(100), unique=True, nullable=False, index=True)
    share_type = Column(Enum(ShareType), default=ShareType.LINK, nullable=False)
    access_level = Column(Enum(AccessLevel), default=AccessLevel.VIEW, nullable=False)
    password_hash = Column(String(255), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    max_downloads = Column(Integer, nullable=True)
    download_count = Column(Integer, default=0, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    document = relationship("Document")
    created_by = relationship("User", foreign_keys=[created_by_id])


class DocumentComment(BaseModel):
    """
    Comments on documents.

    Attributes:
        document_id: Document ID
        user_id: User who made comment
        content: Comment content
        parent_id: Parent comment for replies
        is_resolved: Whether comment is resolved
    """

    __tablename__ = "document_comments"

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("document_comments.id"), nullable=True)
    is_resolved = Column(Boolean, default=False, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="comments")
    user = relationship("User", foreign_keys=[user_id])
    parent = relationship("DocumentComment", remote_side="DocumentComment.id", backref="replies")


class DocumentWorkflow(BaseModel):
    """
    Document approval workflows.

    Attributes:
        document_id: Document ID
        workflow_name: Workflow name
        status: Workflow status
        initiated_by_id: User who initiated workflow
        current_step: Current workflow step
        total_steps: Total workflow steps
    """

    __tablename__ = "document_workflows"

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    workflow_name = Column(String(255), nullable=False)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING, nullable=False)
    initiated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_step = Column(Integer, default=1, nullable=False)
    total_steps = Column(Integer, nullable=False)

    # Relationships
    document = relationship("Document")
    initiated_by = relationship("User", foreign_keys=[initiated_by_id])
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowStep(BaseModel):
    """
    Individual workflow steps.

    Attributes:
        workflow_id: Workflow ID
        step_number: Step number
        step_name: Step name
        assignee_id: User assigned to step
        status: Step status
        completed_at: Completion timestamp
        comments: Step comments
    """

    __tablename__ = "workflow_steps"

    workflow_id = Column(Integer, ForeignKey("document_workflows.id"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(255), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    comments = Column(Text, nullable=True)

    # Relationships
    workflow = relationship("DocumentWorkflow", back_populates="steps")
    assignee = relationship("User", foreign_keys=[assignee_id])


class DocumentAuditLog(BaseModel):
    """
    Audit log for document actions.

    Attributes:
        document_id: Document ID
        user_id: User who performed action
        action: Action type
        details: Action details (JSON)
        ip_address: User IP address
        user_agent: User agent string
    """

    __tablename__ = "document_audit_logs"

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    details = Column(Text, nullable=True)  # JSON
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="audit_logs")
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_audit_document_action", "document_id", "action"),
        Index("idx_audit_user_action", "user_id", "action"),
        Index("idx_audit_created", "created_at"),
    )
