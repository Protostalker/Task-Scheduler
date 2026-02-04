"""add push_subscriptions table

Revision ID: 0006
Revises: 0005
Create Date: 2026-01-28
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_push_subscriptions"
down_revision = "0005_task_time_and_mattermost_id"
branch_labels = None
depends_on = None

# keep the rest the same



def upgrade() -> None:
    op.create_table(
        'push_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.String(length=1000), nullable=False),
        sa.Column('p256dh', sa.String(length=500), nullable=False),
        sa.Column('auth', sa.String(length=500), nullable=False),
        sa.Column('user_agent', sa.String(length=300), nullable=False, server_default=''),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'endpoint', name='uq_push_user_endpoint'),
    )
    op.create_index('ix_push_subscriptions_user_id', 'push_subscriptions', ['user_id'], unique=False)
    op.create_index('ix_push_subscriptions_active', 'push_subscriptions', ['active'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_push_subscriptions_active', table_name='push_subscriptions')
    op.drop_index('ix_push_subscriptions_user_id', table_name='push_subscriptions')
    op.drop_table('push_subscriptions')
