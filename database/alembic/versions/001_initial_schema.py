"""Initial schema - Create all core tables

Revision ID: 001
Revises:
Create Date: 2025-11-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial database tables."""

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('role', sa.String(length=50), server_default=sa.text("'user'"), nullable=False),
        sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )

    # Create indexes for users table
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_role_active', 'users', ['role', 'is_active'])
    op.create_index('ix_users_email_active', 'users', ['email', 'is_active'])

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=True),
        sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('version', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.Column('shared_with', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for documents table
    op.create_index('ix_documents_user_id', 'documents', ['user_id'])
    op.create_index('ix_documents_title', 'documents', ['title'])
    op.create_index('ix_documents_type', 'documents', ['type'])
    op.create_index('ix_documents_user_type', 'documents', ['user_id', 'type'])
    op.create_index('ix_documents_deleted_at', 'documents', ['deleted_at'])
    op.create_index('ix_documents_user_deleted', 'documents', ['user_id', 'deleted_at'])

    # Create emails table
    op.create_table(
        'emails',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('from_addr', sa.String(length=255), nullable=False),
        sa.Column('to_addr', sa.String(length=255), nullable=False),
        sa.Column('cc', sa.String(length=1000), nullable=True),
        sa.Column('bcc', sa.String(length=1000), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('attachments', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        sa.Column('status', sa.String(length=50), server_default=sa.text("'draft'"), nullable=False),
        sa.Column('thread_id', sa.String(length=255), nullable=True),
        sa.Column('is_read', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('is_starred', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('is_archived', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for emails table
    op.create_index('ix_emails_user_id', 'emails', ['user_id'])
    op.create_index('ix_emails_from_addr', 'emails', ['from_addr'])
    op.create_index('ix_emails_to_addr', 'emails', ['to_addr'])
    op.create_index('ix_emails_subject', 'emails', ['subject'])
    op.create_index('ix_emails_status', 'emails', ['status'])
    op.create_index('ix_emails_thread_id', 'emails', ['thread_id'])
    op.create_index('ix_emails_user_status', 'emails', ['user_id', 'status'])
    op.create_index('ix_emails_user_read', 'emails', ['user_id', 'is_read'])
    op.create_index('ix_emails_from_to', 'emails', ['from_addr', 'to_addr'])

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default=sa.text("'planning'"), nullable=False),
        sa.Column('priority', sa.String(length=50), server_default=sa.text("'medium'"), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completion_percentage', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('team_members', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        sa.Column('budget', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for projects table
    op.create_index('ix_projects_user_id', 'projects', ['user_id'])
    op.create_index('ix_projects_name', 'projects', ['name'])
    op.create_index('ix_projects_status', 'projects', ['status'])
    op.create_index('ix_projects_priority', 'projects', ['priority'])
    op.create_index('ix_projects_user_status', 'projects', ['user_id', 'status'])
    op.create_index('ix_projects_status_priority', 'projects', ['status', 'priority'])
    op.create_index('ix_projects_start_end', 'projects', ['start_date', 'end_date'])

    # Create chats table
    op.create_table(
        'chats',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.String(length=255), nullable=True),
        sa.Column('replied_to_id', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('attachments', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        sa.Column('is_edited', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['replied_to_id'], ['chats.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for chats table
    op.create_index('ix_chats_user_id', 'chats', ['user_id'])
    op.create_index('ix_chats_room_id', 'chats', ['room_id'])
    op.create_index('ix_chats_replied_to_id', 'chats', ['replied_to_id'])
    op.create_index('ix_chats_room_created', 'chats', ['room_id', 'created_at'])
    op.create_index('ix_chats_user_room', 'chats', ['user_id', 'room_id'])

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('assignee_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default=sa.text("'pending'"), nullable=False),
        sa.Column('priority', sa.String(length=50), server_default=sa.text("'medium'"), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_hours', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('actual_hours', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('dependencies', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for tasks table
    op.create_index('ix_tasks_project_id', 'tasks', ['project_id'])
    op.create_index('ix_tasks_assignee_id', 'tasks', ['assignee_id'])
    op.create_index('ix_tasks_title', 'tasks', ['title'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('ix_tasks_priority', 'tasks', ['priority'])
    op.create_index('ix_tasks_due_date', 'tasks', ['due_date'])
    op.create_index('ix_tasks_project_status', 'tasks', ['project_id', 'status'])
    op.create_index('ix_tasks_assignee_status', 'tasks', ['assignee_id', 'status'])
    op.create_index('ix_tasks_status_priority', 'tasks', ['status', 'priority'])

    # Create files table
    op.create_table(
        'files',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('file_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('mime_type', sa.String(length=255), nullable=False),
        sa.Column('hash', sa.String(length=255), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('is_public', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('download_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_path')
    )

    # Create indexes for files table
    op.create_index('ix_files_user_id', 'files', ['user_id'])
    op.create_index('ix_files_filename', 'files', ['filename'])
    op.create_index('ix_files_file_type', 'files', ['file_type'])
    op.create_index('ix_files_hash', 'files', ['hash'])
    op.create_index('ix_files_created_at', 'files', ['created_at'])
    op.create_index('ix_files_user_type', 'files', ['user_id', 'file_type'])

    # Create ai_interactions table
    op.create_table(
        'ai_interactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('module', sa.String(length=100), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('model_used', sa.String(length=100), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for ai_interactions table
    op.create_index('ix_ai_interactions_user_id', 'ai_interactions', ['user_id'])
    op.create_index('ix_ai_interactions_module', 'ai_interactions', ['module'])
    op.create_index('ix_ai_interactions_model_used', 'ai_interactions', ['model_used'])
    op.create_index('ix_ai_interactions_created_at', 'ai_interactions', ['created_at'])
    op.create_index('ix_ai_interactions_user_module', 'ai_interactions', ['user_id', 'module'])
    op.create_index('ix_ai_interactions_model_created', 'ai_interactions', ['model_used', 'created_at'])
    op.create_index('ix_ai_interactions_user_created', 'ai_interactions', ['user_id', 'created_at'])


def downgrade() -> None:
    """Drop all tables."""

    # Drop tables in reverse order to respect foreign key constraints
    op.drop_table('ai_interactions')
    op.drop_table('files')
    op.drop_table('tasks')
    op.drop_table('chats')
    op.drop_table('projects')
    op.drop_table('emails')
    op.drop_table('documents')
    op.drop_table('users')
