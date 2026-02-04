from alembic import op
import sqlalchemy as sa

revision = "0004_add_task_code"
down_revision = "0003_admin_task_controls"
branch_labels = None
depends_on = None

# keep the rest the same

def upgrade():
    # 1) add column
    op.add_column("tasks", sa.Column("task_code", sa.String(length=16), nullable=True))

    # 2) backfill existing rows from task_num -> T000010 format (6 digits)
    op.execute("""
        UPDATE tasks
        SET task_code = 'T' || LPAD(task_num::text, 6, '0')
        WHERE task_code IS NULL
    """)

    # 3) make not null and unique
    op.alter_column("tasks", "task_code", nullable=False)
    op.create_index("ix_tasks_task_code", "tasks", ["task_code"], unique=True)

def downgrade():
    op.drop_index("ix_tasks_task_code", table_name="tasks")
    op.drop_column("tasks", "task_code")
