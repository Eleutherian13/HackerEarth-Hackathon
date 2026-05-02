"""Add PENDING_REVIEW to processing_status enum.

Revision ID: 002_add_pending_review_status
"""

from alembic import op


revision = "002_add_pending_review_status"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add the enum value; note: this will fail if the value already exists
    op.execute("ALTER TYPE processing_status ADD VALUE IF NOT EXISTS 'PENDING_REVIEW' AFTER 'EXTRACTION_COMPLETE'")


def downgrade() -> None:
    # Downgrade is non-trivial: PostgreSQL cannot remove enum values safely if used.
    # Documented: manual intervention required if rollback is attempted and values exist.
    raise NotImplementedError("Downgrade not supported for enum value removal. Manual intervention required.")
