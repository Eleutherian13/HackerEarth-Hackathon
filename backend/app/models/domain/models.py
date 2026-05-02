"""SQLAlchemy ORM models for the compliance system."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.enums import (
    ActionType,
    AuditEventType,
    CompletionStatus,
    DueDateSource,
    ExtractionMethod,
    FieldType,
    JobStatus,
    JobType,
    Priority,
    ProcessingStatus,
    SessionStatus,
    UserRole,
    VerificationStatus,
)

from .base import Base, CreatedAtMixin, TimestampMixin


UUID_TYPE = UUID(as_uuid=True)


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID_TYPE, primary_key=True, server_default=text("gen_random_uuid()"))


class Department(TimestampMixin, Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    parent_department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_TYPE,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    parent_department = relationship("Department", remote_side="Department.id", back_populates="child_departments")
    child_departments = relationship("Department", back_populates="parent_department")
    users = relationship("User", back_populates="department")

    __table_args__ = (Index("ix_departments_parent_department_id", "parent_department_id"),)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role", native_enum=True), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    department = relationship("Department", back_populates="users")
    uploaded_documents = relationship("Document", back_populates="uploaded_by_user")
    verified_fields = relationship("ExtractedField", back_populates="verified_by_user")
    verified_action_plan_items = relationship("ActionPlanItem", back_populates="verified_by_user")
    review_sessions = relationship("ReviewSession", back_populates="reviewer_user")
    audit_events = relationship("AuditLog", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_text_based: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        SQLEnum(ProcessingStatus, name="processing_status", native_enum=True),
        nullable=False,
        default=ProcessingStatus.UPLOADED,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    uploaded_by_user = relationship("User", back_populates="uploaded_documents")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan", passive_deletes=True)
    extracted_fields = relationship("ExtractedField", back_populates="document", cascade="all, delete-orphan", passive_deletes=True)
    action_plan_items = relationship("ActionPlanItem", back_populates="document", cascade="all, delete-orphan", passive_deletes=True)
    review_sessions = relationship("ReviewSession", back_populates="document", cascade="all, delete-orphan", passive_deletes=True)
    audit_logs = relationship("AuditLog", back_populates="document")
    processing_jobs = relationship("ProcessingJob", back_populates="document", cascade="all, delete-orphan", passive_deletes=True)

    __table_args__ = (
        Index("ix_documents_processing_status_created_at", "processing_status", "created_at"),
        Index("ix_documents_metadata_json_gin", "metadata_json", postgresql_using="gin"),
    )


class DocumentPage(CreatedAtMixin, Base):
    __tablename__ = "document_pages"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_image_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    document = relationship("Document", back_populates="pages")

    __table_args__ = (
        UniqueConstraint("document_id", "page_number", name="uq_document_pages_document_id_page_number"),
        Index("ix_document_pages_document_id_page_number", "document_id", "page_number"),
    )


class ExtractedField(TimestampMixin, Base):
    __tablename__ = "extracted_fields"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_type: Mapped[FieldType] = mapped_column(
        SQLEnum(FieldType, name="field_type", native_enum=True), nullable=False
    )
    value: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    extraction_method: Mapped[ExtractionMethod] = mapped_column(
        SQLEnum(ExtractionMethod, name="extraction_method", native_enum=True),
        nullable=False,
    )
    is_inferred: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    inference_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_page_ids: Mapped[list[int]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    source_quotes: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SQLEnum(VerificationStatus, name="verification_status", native_enum=True),
        nullable=False,
        default=VerificationStatus.UNVERIFIED,
    )
    verified_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_TYPE,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    edit_history: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    reviewer_comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    document = relationship("Document", back_populates="extracted_fields")
    verified_by_user = relationship("User", back_populates="verified_fields")

    __table_args__ = (
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="confidence_score_range"),
        Index("ix_extracted_fields_document_id_field_type", "document_id", "field_type"),
        Index("ix_extracted_fields_document_id_verification_status", "document_id", "verification_status"),
        Index("ix_extracted_fields_source_page_ids_gin", "source_page_ids", postgresql_using="gin"),
        Index("ix_extracted_fields_source_quotes_gin", "source_quotes", postgresql_using="gin"),
        Index("ix_extracted_fields_edit_history_gin", "edit_history", postgresql_using="gin"),
    )


class ActionPlanItem(TimestampMixin, Base):
    __tablename__ = "action_plan_items"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    extracted_field_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_TYPE,
        ForeignKey("extracted_fields.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    item_type: Mapped[ActionType] = mapped_column(
        SQLEnum(ActionType, name="action_type", native_enum=True), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[Priority] = mapped_column(
        SQLEnum(Priority, name="priority", native_enum=True), nullable=False
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date_source: Mapped[DueDateSource] = mapped_column(
        SQLEnum(DueDateSource, name="due_date_source", native_enum=True),
        nullable=False,
    )
    responsible_department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_TYPE,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    responsible_officer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    risk_if_ignored: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_next_step: Mapped[str] = mapped_column(Text, nullable=False)
    source_evidence: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SQLEnum(VerificationStatus, name="verification_status", native_enum=True),
        nullable=False,
        default=VerificationStatus.PENDING,
    )
    verified_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_TYPE,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verification_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completion_status: Mapped[CompletionStatus] = mapped_column(
        SQLEnum(CompletionStatus, name="completion_status", native_enum=True),
        nullable=False,
        default=CompletionStatus.NOT_STARTED,
    )
    actual_completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    document = relationship("Document", back_populates="action_plan_items")
    extracted_field = relationship("ExtractedField")
    responsible_department = relationship("Department")
    verified_by_user = relationship("User", back_populates="verified_action_plan_items")

    __table_args__ = (
        Index("ix_action_plan_items_document_id_completion_status", "document_id", "completion_status"),
        Index("ix_action_plan_items_document_id_verification_status", "document_id", "verification_status"),
        Index("ix_action_plan_items_due_date", "due_date"),
        Index("ix_action_plan_items_responsible_department_id_completion_status", "responsible_department_id", "completion_status"),
        Index("ix_action_plan_items_source_evidence_gin", "source_evidence", postgresql_using="gin"),
    )


class ReviewSession(CreatedAtMixin, Base):
    __tablename__ = "review_sessions"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    session_status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus, name="session_status", native_enum=True), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_fields_reviewed: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"), default=0)
    fields_approved: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"), default=0)
    fields_edited: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"), default=0)
    fields_rejected: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"), default=0)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    document = relationship("Document", back_populates="review_sessions")
    reviewer_user = relationship("User", back_populates="review_sessions")

    __table_args__ = (Index("ix_review_sessions_document_id_session_status", "document_id", "session_status"),)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = uuid_pk()
    event_type: Mapped[AuditEventType] = mapped_column(
        SQLEnum(AuditEventType, name="audit_event_type", native_enum=True),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_TYPE,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_TYPE,
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID_TYPE, nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    changes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="audit_events")
    document = relationship("Document", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_document_id_created_at", "document_id", "created_at"),
        Index("ix_audit_logs_request_id", "request_id"),
        Index("ix_audit_logs_changes_gin", "changes", postgresql_using="gin"),
    )


class ProcessingJob(CreatedAtMixin, Base):
    __tablename__ = "processing_jobs"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_type: Mapped[JobType] = mapped_column(
        SQLEnum(JobType, name="job_type", native_enum=True), nullable=False
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus, name="job_status", native_enum=True),
        nullable=False,
        default=JobStatus.QUEUED,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"), default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("3"), default=3)
    input_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    document = relationship("Document", back_populates="processing_jobs")

    __table_args__ = (
        Index("ix_processing_jobs_document_id_job_type", "document_id", "job_type"),
        Index("ix_processing_jobs_status_created_at", "status", "created_at"),
        Index("ix_processing_jobs_input_params_gin", "input_params", postgresql_using="gin"),
        Index("ix_processing_jobs_output_summary_gin", "output_summary", postgresql_using="gin"),
    )


class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by_jti: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_tokens_user_id_expires_at", "user_id", "expires_at"),
        Index("ix_refresh_tokens_jti", "jti"),
    )