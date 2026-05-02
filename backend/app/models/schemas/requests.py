from __future__ import annotations

import json
from datetime import date
from enum import Enum
from typing import Any, Annotated
from uuid import UUID

from fastapi import File, Form, UploadFile
from pydantic import ConfigDict, EmailStr, Field, field_validator

from app.models.enums import CompletionStatus, Priority

from .base import (
    StrictSchema,
    coerce_date,
    coerce_enum_list,
    coerce_int,
    coerce_uuid_list,
    normalize_optional_text,
    normalize_required_text,
    parse_optional_json_dict,
)


class HumanReviewAction(str, Enum):
    APPROVE = "APPROVE"
    EDIT = "EDIT"
    REJECT = "REJECT"


class ActionPlanDecision(str, Enum):
    APPROVE = "APPROVE"
    MODIFY = "MODIFY"
    REJECT = "REJECT"


class DocumentUploadRequest(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "file": "court_judgment.pdf",
                    "metadata_json": {
                        "court": "High Court",
                        "case_number": "WP(C) 123/2025",
                    },
                }
            ]
        },
    )

    file: Annotated[UploadFile, File(description="Court judgment PDF to upload")]
    metadata_json: Annotated[dict[str, Any] | None, Form(default=None)] = None

    @field_validator("file")
    @classmethod
    def validate_file(cls, value: UploadFile) -> UploadFile:
        if not getattr(value, "filename", None):
            raise ValueError("file must include a filename")
        return value

    @field_validator("metadata_json", mode="before")
    @classmethod
    def validate_metadata_json(cls, value: Any) -> dict[str, Any] | None:
        return parse_optional_json_dict(value)


class FieldReviewRequest(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "field_id": "6d6a5f29-5f19-449a-8f3e-0ff2ca6ca3a0",
                    "action": "EDIT",
                    "edited_value": "01 January 2026",
                    "comments": "Corrected the date from OCR output.",
                    "edit_reason": "OCR typo in year format.",
                }
            ]
        },
    )

    field_id: UUID
    action: HumanReviewAction
    edited_value: str | None = None
    comments: str | None = None
    edit_reason: str | None = None
    expected_version: int

    @field_validator("action", mode="before")
    @classmethod
    def normalize_action(cls, value: Any) -> HumanReviewAction:
        if isinstance(value, HumanReviewAction):
            return value
        return HumanReviewAction(str(value))

    @field_validator("field_id", mode="before")
    @classmethod
    def normalize_field_id(cls, value: Any) -> UUID:
        if isinstance(value, UUID):
            return value
        return UUID(str(value))

    @field_validator("edited_value", "comments", "edit_reason", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: Any) -> str | None:
        return normalize_optional_text(value)

    @field_validator("edited_value")
    @classmethod
    def validate_edited_value(cls, value: str | None, info):
        action = info.data.get("action")
        if action == HumanReviewAction.EDIT and value is None:
            raise ValueError("edited_value is required when action is EDIT")
        if action != HumanReviewAction.EDIT and value is not None:
            raise ValueError("edited_value is only allowed when action is EDIT")
        return value


HumanReviewSubmitRequest = FieldReviewRequest


class ActionPlanFinalizeRequest(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "plan_item_id": "c6b83875-c5a8-4f18-91f4-01898036bf06",
                    "action": "MODIFY",
                    "modifications": {"title": "Update compliance deadline"},
                    "rationale": "The original title is too vague for downstream assignment.",
                }
            ]
        },
    )

    plan_item_id: UUID
    action: ActionPlanDecision
    modifications: dict[str, Any] | None = None
    rationale: str | None = None

    @field_validator("modifications", mode="before")
    @classmethod
    def normalize_modifications(cls, value: Any) -> dict[str, Any] | None:
        return parse_optional_json_dict(value)

    @field_validator("plan_item_id", mode="before")
    @classmethod
    def normalize_plan_item_id(cls, value: Any) -> UUID:
        if isinstance(value, UUID):
            return value
        return UUID(str(value))

    @field_validator("modifications")
    @classmethod
    def validate_modifications(cls, value: dict[str, Any] | None, info):
        action = info.data.get("action")
        if action == ActionPlanDecision.MODIFY:
            if not value:
                raise ValueError("modifications are required when action is MODIFY")
        elif value is not None:
            raise ValueError("modifications are only allowed when action is MODIFY")
        return value

    @field_validator("rationale", mode="before")
    @classmethod
    def normalize_rationale(cls, value: Any) -> str | None:
        return normalize_optional_text(value)

    @field_validator("rationale")
    @classmethod
    def validate_rationale(cls, value: str | None, info):
        action = info.data.get("action")
        if action in {ActionPlanDecision.MODIFY, ActionPlanDecision.REJECT} and value is None:
            raise ValueError("rationale is required when action is MODIFY or REJECT")
        if action == ActionPlanDecision.APPROVE and value is not None:
            raise ValueError("rationale is only allowed when action is MODIFY or REJECT")
        return value


class ActionPlanReviewRequest(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "action": "MODIFY",
                    "modifications": {
                        "title": "Update compliance deadline",
                        "responsible_officer": "District Officer",
                    },
                    "rationale": "The original title is too vague for downstream assignment.",
                }
            ]
        },
    )

    action: ActionPlanDecision
    modifications: dict[str, Any] | None = None
    rationale: str | None = None
    expected_version: int

    @field_validator("action", mode="before")
    @classmethod
    def normalize_action(cls, value: Any) -> ActionPlanDecision:
        if isinstance(value, ActionPlanDecision):
            return value
        return ActionPlanDecision(str(value))

    @field_validator("modifications", mode="before")
    @classmethod
    def normalize_modifications(cls, value: Any) -> dict[str, Any] | None:
        return parse_optional_json_dict(value)

    @field_validator("modifications")
    @classmethod
    def validate_modifications(cls, value: dict[str, Any] | None, info):
        action = info.data.get("action")
        if action == ActionPlanDecision.MODIFY:
            if not value:
                raise ValueError("modifications are required when action is MODIFY")
        elif value is not None:
            raise ValueError("modifications are only allowed when action is MODIFY")
        return value

    @field_validator("rationale", mode="before")
    @classmethod
    def normalize_rationale(cls, value: Any) -> str | None:
        return normalize_optional_text(value)

    @field_validator("rationale")
    @classmethod
    def validate_rationale(cls, value: str | None, info):
        action = info.data.get("action")
        if action in {ActionPlanDecision.MODIFY, ActionPlanDecision.REJECT} and value is None:
            raise ValueError("rationale is required when action is MODIFY or REJECT")
        if action == ActionPlanDecision.APPROVE and value is not None:
            raise ValueError("rationale is only allowed when action is MODIFY or REJECT")
        return value


class ActionPlanEditRequest(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "title": "Update compliance deadline",
                    "description": "File the compliance statement with the new deadline.",
                    "priority": "HIGH",
                    "due_date": "2026-01-20",
                    "responsible_department_name": "Legal Department",
                    "responsible_officer": "District Officer",
                    "risk_if_ignored": "Delay may result in contempt proceedings.",
                    "suggested_next_step": "Reassign to the legal team and confirm dates.",
                    "notes": "Updated by reviewer to capture department assignment.",
                }
            ]
        },
    )

    title: str | None = None
    description: str | None = None
    priority: Priority | None = None
    due_date: date | None = None
    responsible_department_id: UUID | None = None
    responsible_department_name: str | None = None
    responsible_officer: str | None = None
    risk_if_ignored: str | None = None
    suggested_next_step: str | None = None
    notes: str | None = None

    @field_validator(
        "title",
        "description",
        "responsible_department_name",
        "responsible_officer",
        "risk_if_ignored",
        "suggested_next_step",
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_optional_texts(cls, value: Any) -> str | None:
        return normalize_optional_text(value)


class UserLoginRequest(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "email": "reviewer@example.gov",
                    "password": "Str0ngPass!",
                }
            ]
        },
    )

    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: Any) -> Any:
        if isinstance(value, str):
            cleaned = value.strip().lower()
            if not cleaned:
                raise ValueError("email cannot be empty")
            return cleaned
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not isinstance(value, str):
            raise TypeError("password must be a string")
        if not value or value.isspace():
            raise ValueError("password cannot be empty")
        if len(value) < 8:
            raise ValueError("password must be at least 8 characters long")
        return value


class QueryFilters(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "department_ids": ["3a1d640c-b50a-4fd0-bcbb-ec16f2ac0f47"],
                    "date_from": "2026-01-01",
                    "date_to": "2026-01-31",
                    "priority": ["HIGH", "CRITICAL"],
                    "status": ["IN_PROGRESS", "OVERDUE"],
                    "search_query": "water supply",
                    "page": 1,
                    "per_page": 50,
                }
            ]
        },
    )

    department_ids: list[UUID] | None = None
    date_from: date | None = None
    date_to: date | None = None
    priority: list[Priority] | None = None
    status: list[CompletionStatus] | None = None
    search_query: str | None = None
    page: int = 1
    per_page: int = 50

    @field_validator("department_ids", mode="before")
    @classmethod
    def normalize_department_ids(cls, value: Any) -> list[UUID] | None:
        return coerce_uuid_list(value)

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, value: Any) -> list[Priority] | None:
        return coerce_enum_list(Priority, value)

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: Any) -> list[CompletionStatus] | None:
        return coerce_enum_list(CompletionStatus, value)

    @field_validator("date_from", "date_to", mode="before")
    @classmethod
    def normalize_dates(cls, value: Any, info):
        return coerce_date(value, info.field_name)

    @field_validator("search_query", mode="before")
    @classmethod
    def normalize_search_query(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("search_query must be a string or None")
        cleaned = normalize_optional_text(value)
        return cleaned

    @field_validator("page", "per_page", mode="before")
    @classmethod
    def normalize_ints(cls, value: Any, info):
        return coerce_int(value, info.field_name)

    @field_validator("per_page")
    @classmethod
    def validate_per_page(cls, value: int) -> int:
        if value > 100:
            raise ValueError("per_page cannot exceed 100")
        return value

    @field_validator("date_to")
    @classmethod
    def validate_date_range(cls, value: date | None, info):
        date_from = info.data.get("date_from")
        if date_from is not None and value is not None and value < date_from:
            raise ValueError("date_to must be greater than or equal to date_from")
        return value
