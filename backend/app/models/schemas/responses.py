from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import ConfigDict, Field, computed_field, field_validator

from app.models.enums import (
    CompletionStatus,
    ProcessingStatus,
    VerificationStatus,
)

from .base import (
    DepartmentBreakdownItem,
    DocumentReviewStats,
    HighlightQuote,
    PaginatedResponse,
    ReviewerInfo,
    SourceEvidenceLink,
    StatusBadge,
    StrictSchema,
    WeeklyTrendPoint,
    normalize_optional_text,
    normalize_required_text,
)


def _status_badge(value: VerificationStatus) -> StatusBadge:
    mapping = {
        VerificationStatus.UNVERIFIED: StatusBadge(label="Unverified", color_code="#6b7280"),
        VerificationStatus.APPROVED: StatusBadge(label="Approved", color_code="#16a34a"),
        VerificationStatus.EDITED: StatusBadge(label="Edited", color_code="#2563eb"),
        VerificationStatus.REJECTED: StatusBadge(label="Rejected", color_code="#dc2626"),
        VerificationStatus.FLAGGED_FOR_REVIEW: StatusBadge(label="Flagged for review", color_code="#7c3aed"),
        VerificationStatus.PENDING: StatusBadge(label="Pending", color_code="#f59e0b"),
        VerificationStatus.MODIFIED: StatusBadge(label="Modified", color_code="#0ea5e9"),
    }
    return mapping[value]


def _completion_color(status: CompletionStatus) -> str:
    mapping = {
        CompletionStatus.NOT_STARTED: "#6b7280",
        CompletionStatus.IN_PROGRESS: "#2563eb",
        CompletionStatus.COMPLETED: "#16a34a",
        CompletionStatus.OVERDUE: "#dc2626",
        CompletionStatus.CANCELLED: "#64748b",
    }
    return mapping[status]


def _processing_status_label(status: ProcessingStatus) -> str:
    return {
        ProcessingStatus.UPLOADED: "Uploaded",
        ProcessingStatus.CLASSIFYING: "Classifying",
        ProcessingStatus.EXTRACTING: "Extracting",
        ProcessingStatus.EXTRACTION_COMPLETE: "Extraction complete",
        ProcessingStatus.PENDING_REVIEW: "Pending review",
        ProcessingStatus.UNDER_REVIEW: "Under review",
        ProcessingStatus.VERIFIED: "Verified",
        ProcessingStatus.REJECTED: "Rejected",
        ProcessingStatus.FAILED: "Failed",
    }[status]


class DocumentResponse(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "id": "3d1ab1a2-b5a6-4ae6-b0b0-ef1a3f03ad85",
                    "file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    "original_filename": "judgment.pdf",
                    "storage_path": "documents/2026/01/judgment.pdf",
                    "mime_type": "application/pdf",
                    "file_size_bytes": 102400,
                    "page_count": 24,
                    "is_text_based": True,
                    "processing_status": "VERIFIED",
                    "error_message": None,
                    "uploaded_by_user_id": "9c5f4d76-7d29-4b9d-8d7a-0f47b2a8d8ca",
                    "metadata_json": {"court": "High Court"},
                    "created_at": "2026-01-12T10:00:00Z",
                    "updated_at": "2026-01-12T10:05:00Z",
                    "processing_status_label": "Verified",
                    "uploader_name": "Asha Rao",
                    "review_stats": {
                        "approved_count": 12,
                        "edited_count": 2,
                        "rejected_count": 1,
                    },
                }
            ]
        },
    )

    id: UUID
    file_hash: str
    original_filename: str
    storage_path: str
    mime_type: str
    file_size_bytes: int
    page_count: int | None = None
    is_text_based: bool | None = None
    processing_status: ProcessingStatus
    error_message: str | None = None
    uploaded_by_user_id: UUID
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    processing_status_label: str
    uploader_name: str
    review_stats: DocumentReviewStats

    @field_validator("file_hash", "original_filename", "storage_path", "mime_type", mode="before")
    @classmethod
    def normalize_required_text(cls, value: Any, info):
        return normalize_required_text(value, info.field_name)

    @field_validator("error_message", mode="before")
    @classmethod
    def normalize_optional_error(cls, value: Any) -> str | None:
        return normalize_optional_text(value)

    @field_validator("processing_status_label")
    @classmethod
    def validate_processing_status_label(cls, value: str) -> str:
        if not value:
            raise ValueError("processing_status_label cannot be empty")
        return value


class ExtractedFieldResponse(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "id": "8d2f51c1-bf6c-4f6b-8f74-0a8b5e9b2c0a",
                    "document_id": "3d1ab1a2-b5a6-4ae6-b0b0-ef1a3f03ad85",
                    "field_type": "CASE_NUMBER",
                    "value": "WP(C) 123/2025",
                    "normalized_value": "WPC1232025",
                    "confidence_score": 0.98,
                    "extraction_method": "DIRECT_EXTRACT",
                    "is_inferred": False,
                    "inference_rationale": None,
                    "source_page_ids": [1],
                    "source_quotes": [
                        {"text": "WP(C) 123/2025", "page": 1, "bbox": [12.0, 18.0, 200.0, 40.0]}
                    ],
                    "verification_status": "APPROVED",
                    "verified_by_user_id": "9c5f4d76-7d29-4b9d-8d7a-0f47b2a8d8ca",
                    "verified_at": "2026-01-12T10:06:00Z",
                    "edit_history": [],
                    "reviewer_comments": "Verified against the header section.",
                    "created_at": "2026-01-12T10:01:00Z",
                    "updated_at": "2026-01-12T10:06:00Z",
                }
            ]
        },
    )

    id: UUID
    document_id: UUID
    field_type: str
    value: str
    normalized_value: str | None = None
    confidence_score: float = Field(ge=0, le=1)
    extraction_method: str
    is_inferred: bool
    inference_rationale: str | None = None
    source_page_ids: list[int]
    source_quotes: list[HighlightQuote]
    verification_status: VerificationStatus
    verified_by_user_id: UUID | None = None
    verified_at: datetime | None = None
    edit_history: list[dict[str, Any]]
    reviewer_comments: str | None = None
    created_at: datetime
    updated_at: datetime
    verification_status_badge: StatusBadge
    reviewer_info: ReviewerInfo | None = None

    @field_validator("value", "field_type", "extraction_method", mode="before")
    @classmethod
    def normalize_required_text(cls, value: Any, info):
        return normalize_required_text(value, info.field_name)

    @field_validator("normalized_value", "inference_rationale", "reviewer_comments", mode="before")
    @classmethod
    def normalize_optional_texts(cls, value: Any) -> str | None:
        return normalize_optional_text(value)

    @field_validator("verification_status_badge", mode="before")
    @classmethod
    def derive_badge(cls, value: Any, info):
        badge = value or _status_badge(info.data["verification_status"])
        return badge


class ActionPlanItemResponse(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "id": "0bb4fdb1-2f74-4d4b-a34e-2d6edb85f8f7",
                    "document_id": "3d1ab1a2-b5a6-4ae6-b0b0-ef1a3f03ad85",
                    "extracted_field_id": "8d2f51c1-bf6c-4f6b-8f74-0a8b5e9b2c0a",
                    "item_type": "COMPLIANCE",
                    "title": "File compliance affidavit",
                    "description": "Prepare and file the compliance affidavit before the deadline.",
                    "priority": "HIGH",
                    "due_date": "2026-01-20",
                    "due_date_source": "EXPLICIT_IN_JUDGMENT",
                    "responsible_department_id": "3a1d640c-b50a-4fd0-bcbb-ec16f2ac0f47",
                    "responsible_officer": "District Officer",
                    "risk_if_ignored": "Potential contempt exposure.",
                    "suggested_next_step": "Assign to legal cell.",
                    "source_evidence_links": [],
                    "verification_status": "APPROVED",
                    "verified_by_user_id": "9c5f4d76-7d29-4b9d-8d7a-0f47b2a8d8ca",
                    "verification_date": "2026-01-12T10:06:00Z",
                    "completion_status": "NOT_STARTED",
                    "actual_completion_date": None,
                    "notes": None,
                    "created_at": "2026-01-12T10:01:00Z",
                    "updated_at": "2026-01-12T10:06:00Z",
                    "department_name": "Legal Department",
                    "time_until_deadline": "8 days",
                    "status_color_code": "#2563eb",
                }
            ]
        },
    )

    id: UUID
    document_id: UUID
    extracted_field_id: UUID | None = None
    item_type: str
    title: str
    description: str
    priority: Priority
    due_date: date | None = None
    due_date_source: str
    responsible_department_id: UUID | None = None
    responsible_officer: str | None = None
    risk_if_ignored: str
    suggested_next_step: str
    source_evidence_links: list[SourceEvidenceLink]
    source_evidence: dict[str, Any]
    verification_status: VerificationStatus
    verified_by_user_id: UUID | None = None
    verification_date: datetime | None = None
    completion_status: CompletionStatus
    actual_completion_date: date | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    department_name: str | None = None
    time_until_deadline: str | None = None
    status_color_code: str

    @field_validator("item_type", "due_date_source", mode="before")
    @classmethod
    def normalize_required_text(cls, value: Any, info):
        return normalize_required_text(value, info.field_name)

    @field_validator("title", "description", "risk_if_ignored", "suggested_next_step", mode="before")
    @classmethod
    def normalize_required_body_text(cls, value: Any, info):
        return normalize_required_text(value, info.field_name)

    @field_validator("responsible_officer", "notes", "department_name", "time_until_deadline", mode="before")
    @classmethod
    def normalize_optional_texts(cls, value: Any) -> str | None:
        return normalize_optional_text(value)

    @field_validator("status_color_code")
    @classmethod
    def validate_status_color_code(cls, value: str) -> str:
        if not value:
            raise ValueError("status_color_code cannot be empty")
        return value


class ReviewQueueItemResponse(DocumentResponse):
    priority_indicator: str
    age_since_upload: str

    @field_validator("priority_indicator", "age_since_upload")
    @classmethod
    def validate_display_fields(cls, value: str) -> str:
        if not value:
            raise ValueError("display fields cannot be empty")
        return value


class ReviewQueueResponse(PaginatedResponse[ReviewQueueItemResponse]):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "items": [],
                    "total": 0,
                    "page": 1,
                    "per_page": 50,
                    "pages": 0,
                }
            ]
        },
    )


class DashboardStatsResponse(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "total_verified_items": 214,
                    "actions_by_priority": {
                        "CRITICAL": 8,
                        "HIGH": 52,
                        "MEDIUM": 112,
                        "LOW": 42,
                    },
                    "actions_by_type": {
                        "COMPLIANCE": 128,
                        "APPEAL_CONSIDERATION": 24,
                        "INTERNAL_REVIEW": 32,
                        "ESCALATION": 30,
                    },
                    "overdue_items_count": 3,
                    "due_within_7_days": 6,
                    "due_within_30_days": 18,
                    "department_breakdown": [
                        {
                            "department_id": "3a1d640c-b50a-4fd0-bcbb-ec16f2ac0f47",
                            "department_name": "Legal Department",
                            "item_count": 12,
                        }
                    ],
                    "weekly_trend": [],
                }
            ]
        },
    )

    total_verified_items: int = Field(ge=0)
    actions_by_priority: dict[str, int]
    actions_by_type: dict[str, int]
    overdue_items_count: int = Field(ge=0)
    due_within_7_days: int = Field(ge=0)
    due_within_30_days: int = Field(ge=0)
    department_breakdown: list[DepartmentBreakdownItem]
    weekly_trend: list[WeeklyTrendPoint]


class AuditLogEntryResponse(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "id": "9f61b5a8-f38a-4fc7-82be-829f9b8b5d0c",
                    "event_type": "FIELD_VERIFIED",
                    "user_id": "9c5f4d76-7d29-4b9d-8d7a-0f47b2a8d8ca",
                    "document_id": "3d1ab1a2-b5a6-4ae6-b0b0-ef1a3f03ad85",
                    "entity_type": "ExtractedField",
                    "entity_id": "8d2f51c1-bf6c-4f6b-8f74-0a8b5e9b2c0a",
                    "action": "approve_field",
                    "changes": {"before": "draft", "after": "approved"},
                    "ip_address": "10.0.0.1",
                    "user_agent": "Mozilla/5.0",
                    "request_id": "5d6b3c1a-22c5-4e3b-bf11-4aef2b8c9c01",
                    "created_at": "2026-01-12T10:06:00Z",
                }
            ]
        },
    )

    id: UUID
    event_type: str
    user_id: UUID | None = None
    document_id: UUID | None = None
    entity_type: str
    entity_id: UUID | None = None
    action: str
    changes: dict[str, Any]
    ip_address: str | None = None
    request_id: str | None = None
    user_agent: str | None = None
    created_at: datetime

    @field_validator("event_type", "entity_type", "action", mode="before")
    @classmethod
    def normalize_required_text(cls, value: Any, info):
        return normalize_required_text(value, info.field_name)

    @field_validator("ip_address", "user_agent", mode="before")
    @classmethod
    def normalize_optional_texts(cls, value: Any) -> str | None:
        return normalize_optional_text(value)


class AuditLogResponse(PaginatedResponse[AuditLogEntryResponse]):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "items": [],
                    "total": 0,
                    "page": 1,
                    "per_page": 50,
                    "pages": 0,
                }
            ]
        },
    )


class ErrorResponse(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "error_code": "VALIDATION_ERROR",
                    "message": "One or more fields failed validation.",
                    "details": {"field": "date_to"},
                }
            ]
        },
    )

    error_code: str
    message: str
    details: dict[str, Any] | None = None

    @field_validator("error_code", "message", mode="before")
    @classmethod
    def normalize_required_text(cls, value: Any, info):
        return normalize_required_text(value, info.field_name)

    @field_validator("details", mode="before")
    @classmethod
    def normalize_details(cls, value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        if isinstance(value, dict):
            return value
        raise TypeError("details must be a dict or None")
