from alembic import op
import sqlalchemy as sa

revision = "0005_task_time_and_mattermost_id"
down_revision = "0004_add_task_code"
branch_labels = None
depends_on = None

# keep the rest the same



def upgrade():
    # Users: Mattermost ID (optional)
    op.add_column(
        "users",
        sa.Column("mattermost_id", sa.String(length=190), nullable=False, server_default=""),
    )
    op.create_index("ix_users_mattermost_id", "users", ["mattermost_id"], unique=False)

    # Tasks: optional scheduled time
    op.add_column(
        "tasks",
        sa.Column("task_time", sa.Time(), nullable=True),
    )
    op.create_index("ix_tasks_task_time", "tasks", ["task_time"], unique=False)


def downgrade():
    op.drop_index("ix_tasks_task_time", table_name="tasks")
    op.drop_column("tasks", "task_time")

    op.drop_index("ix_users_mattermost_id", table_name="users")
    op.drop_column("users", "mattermost_id")
