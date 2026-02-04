"""admin task controls

Revision ID: 0003_admin_task_controls
Revises: 0002_categories_patients
Create Date: 2026-01-26

"""

from alembic import op
import sqlalchemy as sa

revision = "0003_admin_task_controls"
down_revision = "0002_categories_patients"
branch_labels = None
depends_on = None

# keep the rest the same


def upgrade() -> None:
    op.add_column("tasks", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.add_column("tasks", sa.Column("deleted_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.add_column("tasks", sa.Column("forced_done_at", sa.DateTime(), nullable=True))
    op.add_column("tasks", sa.Column("forced_done_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))

    op.create_index("ix_tasks_deleted_at", "tasks", ["deleted_at"])
    op.create_index("ix_tasks_deleted_by_user_id", "tasks", ["deleted_by_user_id"])
    op.create_index("ix_tasks_forced_done_by_user_id", "tasks", ["forced_done_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_tasks_forced_done_by_user_id", table_name="tasks")
    op.drop_index("ix_tasks_deleted_by_user_id", table_name="tasks")
    op.drop_index("ix_tasks_deleted_at", table_name="tasks")
    op.drop_column("tasks", "forced_done_by_user_id")
    op.drop_column("tasks", "forced_done_at")
    op.drop_column("tasks", "deleted_by_user_id")
    op.drop_column("tasks", "deleted_at")
