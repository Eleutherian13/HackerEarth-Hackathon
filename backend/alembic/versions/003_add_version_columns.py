"""Add optimistic locking version columns.

Revision ID: 003_add_version_columns
"""

from alembic import op
import sqlalchemy as sa


revision = "003_add_version_columns"
down_revision = "002_add_pending_review_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "extracted_fields",
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )
    op.add_column(
        "action_plan_items",
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )
    op.alter_column("extracted_fields", "version", server_default=None)
    op.alter_column("action_plan_items", "version", server_default=None)


def downgrade() -> None:
    op.drop_column("action_plan_items", "version")
    op.drop_column("extracted_fields", "version")
