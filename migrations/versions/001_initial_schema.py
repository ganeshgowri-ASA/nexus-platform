"""Initial database schema for A/B testing module.

Revision ID: 001
Revises:
Create Date: 2025-01-15 10:00:00.000000

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
    """Upgrade database schema."""
    # Create experiments table
    op.create_table(
        'experiments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('hypothesis', sa.Text(), nullable=True),
        sa.Column('type', sa.Enum('AB', 'MULTIVARIATE', 'MULTI_ARMED_BANDIT', name='experimenttype'), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'RUNNING', 'PAUSED', 'COMPLETED', 'ARCHIVED', name='experimentstatus'), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('target_sample_size', sa.Integer(), nullable=False),
        sa.Column('confidence_level', sa.Float(), nullable=False),
        sa.Column('traffic_allocation', sa.Float(), nullable=False),
        sa.Column('auto_winner_enabled', sa.Boolean(), nullable=False),
        sa.Column('winner_variant_id', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_experiments'))
    )
    op.create_index(op.f('ix_experiments_name'), 'experiments', ['name'], unique=False)
    op.create_index(op.f('ix_experiments_status'), 'experiments', ['status'], unique=False)

    # Create variants table
    op.create_table(
        'variants',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_control', sa.Boolean(), nullable=False),
        sa.Column('traffic_weight', sa.Float(), nullable=False),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], name=op.f('fk_variants_experiment_id_experiments'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_variants'))
    )
    op.create_index(op.f('ix_variants_experiment_id'), 'variants', ['experiment_id'], unique=False)

    # Add foreign key for winner_variant_id
    op.create_foreign_key(
        op.f('fk_experiments_winner_variant_id_variants'),
        'experiments', 'variants',
        ['winner_variant_id'], ['id'],
        ondelete='SET NULL'
    )

    # Create segments table
    op.create_table(
        'segments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_segments'))
    )
    op.create_index(op.f('ix_segments_name'), 'segments', ['name'], unique=True)

    # Create segment_conditions table
    op.create_table(
        'segment_conditions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('segment_id', sa.Integer(), nullable=False),
        sa.Column('property_name', sa.String(length=255), nullable=False),
        sa.Column('operator', sa.Enum('EQUALS', 'NOT_EQUALS', 'GREATER_THAN', 'LESS_THAN', 'GREATER_THAN_OR_EQUAL', 'LESS_THAN_OR_EQUAL', 'CONTAINS', 'NOT_CONTAINS', 'IN', 'NOT_IN', 'REGEX', name='segmentoperator'), nullable=False),
        sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['segment_id'], ['segments.id'], name=op.f('fk_segment_conditions_segment_id_segments'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_segment_conditions'))
    )
    op.create_index(op.f('ix_segment_conditions_segment_id'), 'segment_conditions', ['segment_id'], unique=False)

    # Create experiment_segments association table
    op.create_table(
        'experiment_segments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('segment_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], name=op.f('fk_experiment_segments_experiment_id_experiments'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['segment_id'], ['segments.id'], name=op.f('fk_experiment_segments_segment_id_segments'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_experiment_segments'))
    )

    # Create participants table
    op.create_table(
        'participants',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('participant_id', sa.String(length=255), nullable=False),
        sa.Column('properties', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_participants'))
    )
    op.create_index(op.f('ix_participants_participant_id'), 'participants', ['participant_id'], unique=True)

    # Create participant_variants table
    op.create_table(
        'participant_variants',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('participant_id', sa.String(length=255), nullable=False),
        sa.Column('variant_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], name=op.f('fk_participant_variants_experiment_id_experiments'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], name=op.f('fk_participant_variants_variant_id_variants'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_participant_variants'))
    )
    op.create_index(op.f('ix_participant_variants_experiment_id'), 'participant_variants', ['experiment_id'], unique=False)
    op.create_index(op.f('ix_participant_variants_participant_id'), 'participant_variants', ['participant_id'], unique=False)
    op.create_index(op.f('ix_participant_variants_variant_id'), 'participant_variants', ['variant_id'], unique=False)

    # Create metrics table
    op.create_table(
        'metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.Enum('CONVERSION', 'REVENUE', 'ENGAGEMENT', 'CUSTOM', name='metrictype'), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False),
        sa.Column('goal_value', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], name=op.f('fk_metrics_experiment_id_experiments'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_metrics'))
    )
    op.create_index(op.f('ix_metrics_experiment_id'), 'metrics', ['experiment_id'], unique=False)

    # Create metric_events table
    op.create_table(
        'metric_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metric_id', sa.Integer(), nullable=False),
        sa.Column('participant_id', sa.String(length=255), nullable=False),
        sa.Column('variant_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('properties', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['metric_id'], ['metrics.id'], name=op.f('fk_metric_events_metric_id_metrics'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], name=op.f('fk_metric_events_variant_id_variants'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_metric_events'))
    )
    op.create_index(op.f('ix_metric_events_metric_id'), 'metric_events', ['metric_id'], unique=False)
    op.create_index(op.f('ix_metric_events_participant_id'), 'metric_events', ['participant_id'], unique=False)
    op.create_index(op.f('ix_metric_events_timestamp'), 'metric_events', ['timestamp'], unique=False)
    op.create_index(op.f('ix_metric_events_variant_id'), 'metric_events', ['variant_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index(op.f('ix_metric_events_variant_id'), table_name='metric_events')
    op.drop_index(op.f('ix_metric_events_timestamp'), table_name='metric_events')
    op.drop_index(op.f('ix_metric_events_participant_id'), table_name='metric_events')
    op.drop_index(op.f('ix_metric_events_metric_id'), table_name='metric_events')
    op.drop_table('metric_events')

    op.drop_index(op.f('ix_metrics_experiment_id'), table_name='metrics')
    op.drop_table('metrics')

    op.drop_index(op.f('ix_participant_variants_variant_id'), table_name='participant_variants')
    op.drop_index(op.f('ix_participant_variants_participant_id'), table_name='participant_variants')
    op.drop_index(op.f('ix_participant_variants_experiment_id'), table_name='participant_variants')
    op.drop_table('participant_variants')

    op.drop_index(op.f('ix_participants_participant_id'), table_name='participants')
    op.drop_table('participants')

    op.drop_table('experiment_segments')

    op.drop_index(op.f('ix_segment_conditions_segment_id'), table_name='segment_conditions')
    op.drop_table('segment_conditions')

    op.drop_index(op.f('ix_segments_name'), table_name='segments')
    op.drop_table('segments')

    op.drop_constraint(op.f('fk_experiments_winner_variant_id_variants'), 'experiments', type_='foreignkey')

    op.drop_index(op.f('ix_variants_experiment_id'), table_name='variants')
    op.drop_table('variants')

    op.drop_index(op.f('ix_experiments_status'), table_name='experiments')
    op.drop_index(op.f('ix_experiments_name'), table_name='experiments')
    op.drop_table('experiments')

    # Drop enums
    sa.Enum(name='metrictype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='segmentoperator').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='experimentstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='experimenttype').drop(op.get_bind(), checkfirst=True)
