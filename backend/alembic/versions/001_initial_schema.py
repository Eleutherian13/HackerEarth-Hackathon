"""Initial schema for the compliance system."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


user_role = postgresql.ENUM(
    "SUPERADMIN",
    "ADMIN",
    "REVIEWER",
    "OFFICER",
    "VIEWER",
    name="user_role",
)
processing_status = postgresql.ENUM(
    "UPLOADED",
    "CLASSIFYING",
    "EXTRACTING",
    "EXTRACTION_COMPLETE",
    "PENDING_REVIEW",
    "UNDER_REVIEW",
    "VERIFIED",
    "REJECTED",
    "FAILED",
    name="processing_status",
)
field_type = postgresql.ENUM(
    "CASE_NUMBER",
    "CASE_TITLE",
    "COURT_NAME",
    "JUDGMENT_DATE",
    "PARTIES",
    "PETITIONER",
    "RESPONDENT",
    "BENCH_INFO",
    "FACTS_SUMMARY",
    "OPERATIVE_DIRECTION",
    "DEADLINE",
    "APPEAL_CLUE",
    "COMPLIANCE_OBLIGATION",
    "RESPONSIBLE_DEPARTMENT",
    "COST_ORDER",
    "PENALTY_RISK",
    "CONTEMPT_RISK",
    "FOLLOW_UP_REQUIRED",
    "ACTION_ITEM",
    name="field_type",
)
extraction_method = postgresql.ENUM(
    "DIRECT_EXTRACT",
    "OCR_PIPELINE",
    "LLM_INFERRED",
    "HYBRID",
    name="extraction_method",
)
verification_status = postgresql.ENUM(
    "UNVERIFIED",
    "APPROVED",
    "EDITED",
    "REJECTED",
    "FLAGGED_FOR_REVIEW",
    "PENDING",
    "MODIFIED",
    name="verification_status",
)
action_type = postgresql.ENUM(
    "COMPLIANCE",
    "APPEAL_CONSIDERATION",
    "INTERNAL_REVIEW",
    "ESCALATION",
    "MONITORING",
    name="action_type",
)
priority = postgresql.ENUM("CRITICAL", "HIGH", "MEDIUM", "LOW", name="priority")
due_date_source = postgresql.ENUM(
    "EXPLICIT_IN_JUDGMENT",
    "INFERRED",
    "ESTIMATED",
    name="due_date_source",
)
completion_status = postgresql.ENUM(
    "NOT_STARTED",
    "IN_PROGRESS",
    "COMPLETED",
    "OVERDUE",
    "CANCELLED",
    name="completion_status",
)
session_status = postgresql.ENUM(
    "IN_PROGRESS",
    "COMPLETED",
    "ABANDONED",
    name="session_status",
)
audit_event_type = postgresql.ENUM(
    "DOCUMENT_UPLOADED",
    "FIELD_EXTRACTED",
    "FIELD_VERIFIED",
    "FIELD_EDITED",
    "FIELD_REJECTED",
    "ACTION_PLAN_GENERATED",
    "ACTION_PLAN_VERIFIED",
    "USER_LOGIN",
    "USER_ACTION",
    "SYSTEM_ERROR",
    name="audit_event_type",
)
job_type = postgresql.ENUM(
    "INGESTION",
    "CLASSIFICATION",
    "EXTRACTION",
    "ACTION_PLAN_GENERATION",
    name="job_type",
)
job_status = postgresql.ENUM(
    "QUEUED",
    "IN_PROGRESS",
    "COMPLETED",
    "FAILED",
    "RETRYING",
    name="job_status",
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    bind = op.get_bind()
    for enum_type in [
        user_role,
        processing_status,
        field_type,
        extraction_method,
        verification_status,
        action_type,
        priority,
        due_date_source,
        completion_status,
        session_status,
        audit_event_type,
        job_type,
        job_status,
    ]:
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("code", sa.String(length=10), nullable=False, unique=True),
        sa.Column(
            "parent_department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_departments_parent_department_id", "departments", ["parent_department_id"])

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_department_id", "users", ["department_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("jti", sa.String(length=255), nullable=False, unique=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_jti", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])
    op.create_index("ix_refresh_tokens_revoked_at", "refresh_tokens", ["revoked_at"])

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("file_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("storage_path", sa.String(length=1000), nullable=False),
        sa.Column("mime_type", sa.String(length=50), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("is_text_based", sa.Boolean(), nullable=True),
        sa.Column("processing_status", processing_status, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "uploaded_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_documents_uploaded_by_user_id", "documents", ["uploaded_by_user_id"])
    op.create_index("ix_documents_processing_status_created_at", "documents", ["processing_status", "created_at"])
    op.create_index("ix_documents_metadata_json_gin", "documents", ["metadata_json"], postgresql_using="gin")

    op.create_table(
        "document_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("page_image_path", sa.String(length=1000), nullable=True),
        sa.Column("extraction_confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("document_id", "page_number", name="uq_document_pages_document_id_page_number"),
    )
    op.create_index("ix_document_pages_document_id", "document_pages", ["document_id"])
    op.create_index("ix_document_pages_document_id_page_number", "document_pages", ["document_id", "page_number"])

    op.create_table(
        "extracted_fields",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("field_type", field_type, nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("normalized_value", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("extraction_method", extraction_method, nullable=False),
        sa.Column("is_inferred", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("inference_rationale", sa.Text(), nullable=True),
        sa.Column("source_page_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("source_quotes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("verification_status", verification_status, nullable=False),
        sa.Column(
            "verified_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("edit_history", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("reviewer_comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="confidence_score_range"),
    )
    op.create_index("ix_extracted_fields_document_id", "extracted_fields", ["document_id"])
    op.create_index("ix_extracted_fields_document_id_field_type", "extracted_fields", ["document_id", "field_type"])
    op.create_index("ix_extracted_fields_document_id_verification_status", "extracted_fields", ["document_id", "verification_status"])
    op.create_index("ix_extracted_fields_source_page_ids_gin", "extracted_fields", ["source_page_ids"], postgresql_using="gin")
    op.create_index("ix_extracted_fields_source_quotes_gin", "extracted_fields", ["source_quotes"], postgresql_using="gin")
    op.create_index("ix_extracted_fields_edit_history_gin", "extracted_fields", ["edit_history"], postgresql_using="gin")

    op.create_table(
        "action_plan_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "extracted_field_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("extracted_fields.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("item_type", action_type, nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", priority, nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("due_date_source", due_date_source, nullable=False),
        sa.Column(
            "responsible_department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("responsible_officer", sa.String(length=200), nullable=True),
        sa.Column("risk_if_ignored", sa.Text(), nullable=False),
        sa.Column("suggested_next_step", sa.Text(), nullable=False),
        sa.Column("source_evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("verification_status", verification_status, nullable=False),
        sa.Column(
            "verified_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verification_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completion_status", completion_status, nullable=False),
        sa.Column("actual_completion_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_action_plan_items_document_id", "action_plan_items", ["document_id"])
    op.create_index("ix_action_plan_items_extracted_field_id", "action_plan_items", ["extracted_field_id"])
    op.create_index("ix_action_plan_items_document_id_completion_status", "action_plan_items", ["document_id", "completion_status"])
    op.create_index("ix_action_plan_items_responsible_department_id_completion_status", "action_plan_items", ["responsible_department_id", "completion_status"])
    op.create_index("ix_action_plan_items_source_evidence_gin", "action_plan_items", ["source_evidence"], postgresql_using="gin")

    op.create_table(
        "review_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("session_status", session_status, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_fields_reviewed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("fields_approved", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("fields_edited", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("fields_rejected", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_review_sessions_document_id", "review_sessions", ["document_id"])
    op.create_index("ix_review_sessions_reviewer_user_id", "review_sessions", ["reviewer_user_id"])
    op.create_index("ix_review_sessions_document_id_session_status", "review_sessions", ["document_id", "session_status"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", audit_event_type, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("changes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_document_id_created_at", "audit_logs", ["document_id", "created_at"])
    op.create_index("ix_audit_logs_changes_gin", "audit_logs", ["changes"], postgresql_using="gin")

    op.create_table(
        "processing_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("job_type", job_type, nullable=False),
        sa.Column("celery_task_id", sa.String(length=100), nullable=True),
        sa.Column("status", job_status, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("input_params", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_processing_jobs_document_id", "processing_jobs", ["document_id"])
    op.create_index("ix_processing_jobs_document_id_job_type", "processing_jobs", ["document_id", "job_type"])
    op.create_index("ix_processing_jobs_status_created_at", "processing_jobs", ["status", "created_at"])
    op.create_index("ix_processing_jobs_input_params_gin", "processing_jobs", ["input_params"], postgresql_using="gin")
    op.create_index("ix_processing_jobs_output_summary_gin", "processing_jobs", ["output_summary"], postgresql_using="gin")


def downgrade() -> None:
    op.drop_table("processing_jobs")
    op.drop_table("audit_logs")
    op.drop_table("review_sessions")
    op.drop_table("action_plan_items")
    op.drop_table("extracted_fields")
    op.drop_table("document_pages")
    op.drop_table("documents")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    op.drop_table("departments")

    bind = op.get_bind()
    for enum_type in reversed(
        [
            user_role,
            processing_status,
            field_type,
            extraction_method,
            verification_status,
            action_type,
            priority,
            due_date_source,
            completion_status,
            session_status,
            audit_event_type,
            job_type,
            job_status,
        ]
    ):
        enum_type.drop(bind, checkfirst=True)