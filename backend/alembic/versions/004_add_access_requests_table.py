"""Add access_requests table for user onboarding workflow."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "004_add_access_requests_table"
down_revision = "003_add_version_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create access_request_status enum type
    status_enum = postgresql.ENUM(
        "PENDING", "APPROVED", "REJECTED", "EXPIRED",
        name="access_request_status",
        native_enum=True
    )
    status_enum.create(op.get_bind())

    # Create access_requests table
    op.create_table(
        "access_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.func.gen_random_uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "APPROVED", "REJECTED", "EXPIRED", name="access_request_status", native_enum=True), nullable=False, server_default="PENDING"),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("reviewed_by_admin_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["reviewed_by_admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_access_requests_email"),
    )

    # Create indexes
    op.create_index("ix_access_requests_status_created_at", "access_requests", ["status", "created_at"])
    op.create_index("ix_access_requests_email", "access_requests", ["email"])
    op.create_index("ix_access_requests_reviewed_by_admin_id", "access_requests", ["reviewed_by_admin_id"])


def downgrade() -> None:
    op.drop_index("ix_access_requests_reviewed_by_admin_id", table_name="access_requests")
    op.drop_index("ix_access_requests_email", table_name="access_requests")
    op.drop_index("ix_access_requests_status_created_at", table_name="access_requests")
    op.drop_table("access_requests")
    
    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS access_request_status")
