"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00

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
    """Create initial analytics tables."""

    # Events table
    op.create_table(
        'analytics_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('properties', postgresql.JSON, default={}),
        sa.Column('user_id', sa.String(36)),
        sa.Column('session_id', sa.String(36)),
        sa.Column('module', sa.String(100)),
        sa.Column('page_url', sa.String(2048)),
        sa.Column('page_title', sa.String(255)),
        sa.Column('referrer', sa.String(2048)),
        sa.Column('user_agent', sa.String(512)),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('country', sa.String(2)),
        sa.Column('city', sa.String(100)),
        sa.Column('device_type', sa.String(50)),
        sa.Column('browser', sa.String(50)),
        sa.Column('os', sa.String(50)),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('processed', sa.Boolean, default=False),
        sa.Column('processed_at', sa.DateTime),
    )

    # Create indexes
    op.create_index('ix_events_name', 'analytics_events', ['name'])
    op.create_index('ix_events_event_type', 'analytics_events', ['event_type'])
    op.create_index('ix_events_user_id', 'analytics_events', ['user_id'])
    op.create_index('ix_events_session_id', 'analytics_events', ['session_id'])
    op.create_index('ix_events_timestamp', 'analytics_events', ['timestamp'])

    # Users table
    op.create_table(
        'analytics_users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('external_id', sa.String(255), unique=True),
        sa.Column('email', sa.String(255)),
        sa.Column('name', sa.String(255)),
        sa.Column('properties', postgresql.JSON, default={}),
        sa.Column('first_seen_at', sa.DateTime, nullable=False),
        sa.Column('last_seen_at', sa.DateTime, nullable=False),
        sa.Column('total_sessions', sa.Integer, default=0),
        sa.Column('total_events', sa.Integer, default=0),
        sa.Column('total_conversions', sa.Integer, default=0),
        sa.Column('lifetime_value', sa.Float, default=0.0),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )

    # Additional tables would be created here...
    # (Metrics, Sessions, Funnels, Cohorts, Goals, AB Tests, etc.)


def downgrade() -> None:
    """Drop all analytics tables."""
    op.drop_table('analytics_users')
    op.drop_table('analytics_events')
