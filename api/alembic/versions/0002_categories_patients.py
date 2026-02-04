"""categories and patients

Revision ID: 0002_categories_patients
Revises: 0001_init
Create Date: 2026-01-26

"""

from alembic import op
import sqlalchemy as sa

revision = "0002_categories_patients"
down_revision = "0001_init"
branch_labels = None
depends_on = None

# keep the rest of your file the same


def upgrade() -> None:
    op.create_table(
        "task_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("company_id", "name", name="uq_category_company_name"),
    )
    op.create_index("ix_task_categories_company_id", "task_categories", ["company_id"])

    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=190), nullable=False),
        sa.Column("phone", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("address", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("maps_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_patients_company_id", "patients", ["company_id"])
    op.create_index("ix_patients_active", "patients", ["active"])

    # Tasks: add snapshot fields and optional patient reference
    op.add_column("tasks", sa.Column("patient_name", sa.String(length=190), nullable=False, server_default=""))
    op.add_column("tasks", sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_tasks_patient_id", "tasks", ["patient_id"])

    # Backfill default categories for existing companies that don't have any.
    bind = op.get_bind()
    res = bind.execute(sa.text("SELECT id FROM companies"))
    company_ids = [row[0] for row in res.fetchall()]
    for cid in company_ids:
        count = bind.execute(sa.text("SELECT COUNT(1) FROM task_categories WHERE company_id = :cid"), {"cid": cid}).scalar()
        if int(count or 0) == 0:
            for name, order in [("visits", 10), ("office", 20), ("notes", 30), ("general", 40)]:
                bind.execute(
                    sa.text(
                        "INSERT INTO task_categories (company_id, name, sort_order, active) VALUES (:cid, :name, :order, true)"
                    ),
                    {"cid": cid, "name": name, "order": order},
                )


def downgrade() -> None:
    op.drop_index("ix_tasks_patient_id", table_name="tasks")
    op.drop_column("tasks", "patient_id")
    op.drop_column("tasks", "patient_name")

    op.drop_index("ix_patients_active", table_name="patients")
    op.drop_index("ix_patients_company_id", table_name="patients")
    op.drop_table("patients")

    op.drop_index("ix_task_categories_company_id", table_name="task_categories")
    op.drop_table("task_categories")
