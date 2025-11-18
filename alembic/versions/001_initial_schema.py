"""Initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-11-18 00:00:00.000000

This migration creates the initial database schema for the NEXUS platform,
including users, documents, folders, permissions, and all related tables.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("password_changed_at", sa.DateTime(), nullable=False),
        sa.Column("storage_quota", sa.BigInteger(), nullable=False),
        sa.Column("storage_used", sa.BigInteger(), nullable=False),
        sa.Column("preferences", sa.Text(), nullable=True),
        sa.Column("api_key_hash", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # Create folders table
    op.create_table(
        "folders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("path", sa.String(length=2000), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["folders.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "parent_id", "name", name="uq_folder_path"),
    )
    op.create_index(op.f("ix_folders_id"), "folders", ["id"], unique=False)
    op.create_index(op.f("ix_folders_name"), "folders", ["name"], unique=False)
    op.create_index(op.f("ix_folders_owner_id"), "folders", ["owner_id"], unique=False)
    op.create_index(op.f("ix_folders_parent_id"), "folders", ["parent_id"], unique=False)
    op.create_index(op.f("ix_folders_path"), "folders", ["path"], unique=False)

    # Create tags table
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tags_id"), "tags", ["id"], unique=False)
    op.create_index(op.f("ix_tags_name"), "tags", ["name"], unique=True)

    # Create documents table
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_name", sa.String(length=500), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(length=200), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "ACTIVE",
                "ARCHIVED",
                "DELETED",
                "LOCKED",
                "IN_REVIEW",
                "APPROVED",
                "REJECTED",
                name="documentstatus",
            ),
            nullable=False,
        ),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("folder_id", sa.Integer(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("view_count", sa.Integer(), nullable=False),
        sa.Column("download_count", sa.Integer(), nullable=False),
        sa.Column("current_version", sa.Integer(), nullable=False),
        sa.Column("is_locked", sa.Boolean(), nullable=False),
        sa.Column("locked_by_id", sa.Integer(), nullable=True),
        sa.Column("locked_at", sa.DateTime(), nullable=True),
        sa.Column("retention_date", sa.DateTime(), nullable=True),
        sa.Column("is_on_legal_hold", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["folder_id"],
            ["folders.id"],
        ),
        sa.ForeignKeyConstraint(
            ["locked_by_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_document_folder_status", "documents", ["folder_id", "status"], unique=False
    )
    op.create_index(
        "idx_document_owner_status", "documents", ["owner_id", "status"], unique=False
    )
    op.create_index(op.f("ix_documents_file_hash"), "documents", ["file_hash"], unique=False)
    op.create_index(op.f("ix_documents_folder_id"), "documents", ["folder_id"], unique=False)
    op.create_index(op.f("ix_documents_id"), "documents", ["id"], unique=False)
    op.create_index(op.f("ix_documents_owner_id"), "documents", ["owner_id"], unique=False)
    op.create_index(op.f("ix_documents_status"), "documents", ["status"], unique=False)
    op.create_index(op.f("ix_documents_title"), "documents", ["title"], unique=False)

    # Create folder_permissions table
    op.create_table(
        "folder_permissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("folder_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column(
            "access_level",
            sa.Enum("NONE", "VIEW", "COMMENT", "EDIT", "ADMIN", name="accesslevel"),
            nullable=False,
        ),
        sa.Column("granted_by_id", sa.Integer(), nullable=False),
        sa.Column("is_inherited", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["folder_id"],
            ["folders.id"],
        ),
        sa.ForeignKeyConstraint(
            ["granted_by_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_folder_permissions_folder_id"), "folder_permissions", ["folder_id"], unique=False
    )
    op.create_index(
        op.f("ix_folder_permissions_id"), "folder_permissions", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_folder_permissions_user_id"), "folder_permissions", ["user_id"], unique=False
    )

    # Create document_audit_logs table
    op.create_table(
        "document_audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_created", "document_audit_logs", ["created_at"], unique=False)
    op.create_index(
        "idx_audit_document_action",
        "document_audit_logs",
        ["document_id", "action"],
        unique=False,
    )
    op.create_index(
        "idx_audit_user_action", "document_audit_logs", ["user_id", "action"], unique=False
    )
    op.create_index(
        op.f("ix_document_audit_logs_action"), "document_audit_logs", ["action"], unique=False
    )
    op.create_index(
        op.f("ix_document_audit_logs_document_id"),
        "document_audit_logs",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_audit_logs_id"), "document_audit_logs", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_document_audit_logs_user_id"), "document_audit_logs", ["user_id"], unique=False
    )

    # Create document_comments table
    op.create_table(
        "document_comments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["document_comments.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_document_comments_document_id"),
        "document_comments",
        ["document_id"],
        unique=False,
    )
    op.create_index(op.f("ix_document_comments_id"), "document_comments", ["id"], unique=False)

    # Create document_metadata table
    op.create_table(
        "document_metadata",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("value_type", sa.String(length=50), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "key", name="uq_document_metadata"),
    )
    op.create_index(
        op.f("ix_document_metadata_document_id"), "document_metadata", ["document_id"], unique=False
    )
    op.create_index(op.f("ix_document_metadata_id"), "document_metadata", ["id"], unique=False)
    op.create_index(op.f("ix_document_metadata_key"), "document_metadata", ["key"], unique=False)

    # Create document_permissions table
    op.create_table(
        "document_permissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column(
            "access_level",
            sa.Enum("NONE", "VIEW", "COMMENT", "EDIT", "ADMIN", name="accesslevel"),
            nullable=False,
        ),
        sa.Column("granted_by_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.ForeignKeyConstraint(
            ["granted_by_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_permission_user_document",
        "document_permissions",
        ["user_id", "document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_permissions_document_id"),
        "document_permissions",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_permissions_id"), "document_permissions", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_document_permissions_user_id"), "document_permissions", ["user_id"], unique=False
    )

    # Create document_tags table
    op.create_table(
        "document_tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column("added_by_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["added_by_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tags.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "tag_id", name="uq_document_tag"),
    )
    op.create_index(
        op.f("ix_document_tags_document_id"), "document_tags", ["document_id"], unique=False
    )
    op.create_index(op.f("ix_document_tags_id"), "document_tags", ["id"], unique=False)
    op.create_index(op.f("ix_document_tags_tag_id"), "document_tags", ["tag_id"], unique=False)

    # Create document_versions table
    op.create_table(
        "document_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "version_number", name="uq_document_version"),
    )
    op.create_index(
        "idx_version_document",
        "document_versions",
        ["document_id", "version_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_versions_document_id"),
        "document_versions",
        ["document_id"],
        unique=False,
    )
    op.create_index(op.f("ix_document_versions_id"), "document_versions", ["id"], unique=False)

    # Create document_workflows table
    op.create_table(
        "document_workflows",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("workflow_name", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING", "IN_PROGRESS", "APPROVED", "REJECTED", "CANCELLED", name="workflowstatus"
            ),
            nullable=False,
        ),
        sa.Column("initiated_by_id", sa.Integer(), nullable=False),
        sa.Column("current_step", sa.Integer(), nullable=False),
        sa.Column("total_steps", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.ForeignKeyConstraint(
            ["initiated_by_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_document_workflows_document_id"),
        "document_workflows",
        ["document_id"],
        unique=False,
    )
    op.create_index(op.f("ix_document_workflows_id"), "document_workflows", ["id"], unique=False)

    # Create share_links table
    op.create_table(
        "share_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=100), nullable=False),
        sa.Column(
            "share_type",
            sa.Enum("PRIVATE", "LINK", "PUBLIC", name="sharetype"),
            nullable=False,
        ),
        sa.Column(
            "access_level",
            sa.Enum("NONE", "VIEW", "COMMENT", "EDIT", "ADMIN", name="accesslevel"),
            nullable=False,
        ),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("max_downloads", sa.Integer(), nullable=True),
        sa.Column("download_count", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_share_links_document_id"), "share_links", ["document_id"], unique=False
    )
    op.create_index(op.f("ix_share_links_id"), "share_links", ["id"], unique=False)
    op.create_index(op.f("ix_share_links_token"), "share_links", ["token"], unique=True)

    # Create workflow_steps table
    op.create_table(
        "workflow_steps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("workflow_id", sa.Integer(), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("step_name", sa.String(length=255), nullable=False),
        sa.Column("assignee_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING", "IN_PROGRESS", "APPROVED", "REJECTED", "CANCELLED", name="workflowstatus"
            ),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["assignee_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workflow_id"],
            ["document_workflows.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflow_steps_id"), "workflow_steps", ["id"], unique=False)
    op.create_index(
        op.f("ix_workflow_steps_workflow_id"), "workflow_steps", ["workflow_id"], unique=False
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index(op.f("ix_workflow_steps_workflow_id"), table_name="workflow_steps")
    op.drop_index(op.f("ix_workflow_steps_id"), table_name="workflow_steps")
    op.drop_table("workflow_steps")
    op.drop_index(op.f("ix_share_links_token"), table_name="share_links")
    op.drop_index(op.f("ix_share_links_id"), table_name="share_links")
    op.drop_index(op.f("ix_share_links_document_id"), table_name="share_links")
    op.drop_table("share_links")
    op.drop_index(op.f("ix_document_workflows_id"), table_name="document_workflows")
    op.drop_index(op.f("ix_document_workflows_document_id"), table_name="document_workflows")
    op.drop_table("document_workflows")
    op.drop_index(op.f("ix_document_versions_id"), table_name="document_versions")
    op.drop_index(op.f("ix_document_versions_document_id"), table_name="document_versions")
    op.drop_index("idx_version_document", table_name="document_versions")
    op.drop_table("document_versions")
    op.drop_index(op.f("ix_document_tags_tag_id"), table_name="document_tags")
    op.drop_index(op.f("ix_document_tags_id"), table_name="document_tags")
    op.drop_index(op.f("ix_document_tags_document_id"), table_name="document_tags")
    op.drop_table("document_tags")
    op.drop_index(op.f("ix_document_permissions_user_id"), table_name="document_permissions")
    op.drop_index(op.f("ix_document_permissions_id"), table_name="document_permissions")
    op.drop_index(op.f("ix_document_permissions_document_id"), table_name="document_permissions")
    op.drop_index("idx_permission_user_document", table_name="document_permissions")
    op.drop_table("document_permissions")
    op.drop_index(op.f("ix_document_metadata_key"), table_name="document_metadata")
    op.drop_index(op.f("ix_document_metadata_id"), table_name="document_metadata")
    op.drop_index(op.f("ix_document_metadata_document_id"), table_name="document_metadata")
    op.drop_table("document_metadata")
    op.drop_index(op.f("ix_document_comments_id"), table_name="document_comments")
    op.drop_index(op.f("ix_document_comments_document_id"), table_name="document_comments")
    op.drop_table("document_comments")
    op.drop_index(op.f("ix_document_audit_logs_user_id"), table_name="document_audit_logs")
    op.drop_index(op.f("ix_document_audit_logs_id"), table_name="document_audit_logs")
    op.drop_index(op.f("ix_document_audit_logs_document_id"), table_name="document_audit_logs")
    op.drop_index(op.f("ix_document_audit_logs_action"), table_name="document_audit_logs")
    op.drop_index("idx_audit_user_action", table_name="document_audit_logs")
    op.drop_index("idx_audit_document_action", table_name="document_audit_logs")
    op.drop_index("idx_audit_created", table_name="document_audit_logs")
    op.drop_table("document_audit_logs")
    op.drop_index(op.f("ix_folder_permissions_user_id"), table_name="folder_permissions")
    op.drop_index(op.f("ix_folder_permissions_id"), table_name="folder_permissions")
    op.drop_index(op.f("ix_folder_permissions_folder_id"), table_name="folder_permissions")
    op.drop_table("folder_permissions")
    op.drop_index(op.f("ix_documents_title"), table_name="documents")
    op.drop_index(op.f("ix_documents_status"), table_name="documents")
    op.drop_index(op.f("ix_documents_owner_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_folder_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_file_hash"), table_name="documents")
    op.drop_index("idx_document_owner_status", table_name="documents")
    op.drop_index("idx_document_folder_status", table_name="documents")
    op.drop_table("documents")
    op.drop_index(op.f("ix_tags_name"), table_name="tags")
    op.drop_index(op.f("ix_tags_id"), table_name="tags")
    op.drop_table("tags")
    op.drop_index(op.f("ix_folders_path"), table_name="folders")
    op.drop_index(op.f("ix_folders_parent_id"), table_name="folders")
    op.drop_index(op.f("ix_folders_owner_id"), table_name="folders")
    op.drop_index(op.f("ix_folders_name"), table_name="folders")
    op.drop_index(op.f("ix_folders_id"), table_name="folders")
    op.drop_table("folders")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
