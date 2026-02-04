"""init

Revision ID: 0001
Revises:
Create Date: 2026-01-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute(sa.text("CREATE SEQUENCE IF NOT EXISTS task_num_seq START WITH 10 INCREMENT BY 1"))
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=190), nullable=False),
        sa.Column("display_name", sa.String(length=190), nullable=False, server_default=""),
        sa.Column("role", sa.Enum("employee", "admin", "super_admin", name="role"), nullable=False, server_default="employee"),
        sa.Column("password_hash", sa.String(length=500), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("disabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=190), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_companies_slug", "companies", ["slug"], unique=True)

    op.create_table(
        "user_companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("user_id", "company_id", name="uq_user_company"),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_num", sa.Integer(), nullable=False, server_default=sa.text("nextval('task_num_seq')")),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("assigned_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=False, server_default="general"),
        sa.Column("task_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("maps_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("patient_address", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("patient_phone", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("bonus_details", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.Enum("todo", "done", name="taskstatus"), nullable=False, server_default="todo"),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_tasks_task_num", "tasks", ["task_num"], unique=True)
    op.create_index("ix_tasks_company_id", "tasks", ["company_id"])
    op.create_index("ix_tasks_assigned_user_id", "tasks", ["assigned_user_id"])
    op.create_index("ix_tasks_task_date", "tasks", ["task_date"])
    op.create_index("ix_tasks_category", "tasks", ["category"])
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_company_user_date", "tasks", ["company_id", "assigned_user_id", "task_date"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.Enum(
            "LOGIN","LOGOUT","CREATE_USER","RESET_PASSWORD","CHANGE_PASSWORD","DISABLE_USER","SET_ROLE","ASSIGN_COMPANY",
            "CREATE_TASK","COMPLETE_TASK","UNCOMPLETE_TASK",
            name="auditaction"
        ), nullable=False),
        sa.Column("target_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ip", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("user_agent", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("meta", sa.Text(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_target_user_id", "audit_logs", ["target_user_id"])
    op.create_index("ix_audit_logs_company_id", "audit_logs", ["company_id"])
    op.create_index("ix_audit_logs_task_id", "audit_logs", ["task_id"])

def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("tasks")
    op.drop_table("user_companies")
    op.drop_table("companies")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
    op.execute(sa.text("DROP SEQUENCE IF EXISTS task_num_seq"))
