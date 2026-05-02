from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.models.enums import ActionType, CompletionStatus, Priority
from .base import PaginatedResponse, StrictSchema


class DashboardQueryParams(StrictSchema):
    department_id: UUID | None = None
    priority: list[Priority] | None = None
    type: list[ActionType] | None = None
    status: list[CompletionStatus] | None = None
    due_date_from: date | None = None
    due_date_to: date | None = None
    search_query: str | None = None
    page: int = 1
    per_page: int = 25
    sort_by: str = Field(
        "due_date",
        pattern="^(title|case_number|court|department_name|priority|due_date|status|type)$",
    )
    sort_order: str = Field("asc", pattern="^(asc|desc)$")

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, value: Any) -> list[Priority] | None:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            value = [part.strip() for part in value.split(",") if part.strip()]
        if not isinstance(value, (list, tuple)):
            raise TypeError("priority must be a list of Priority values")
        return [Priority(item) if not isinstance(item, Priority) else item for item in value]

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, value: Any) -> list[ActionType] | None:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            value = [part.strip() for part in value.split(",") if part.strip()]
        if not isinstance(value, (list, tuple)):
            raise TypeError("type must be a list of ActionType values")
        return [ActionType(item) if not isinstance(item, ActionType) else item for item in value]

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: Any) -> list[CompletionStatus] | None:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            value = [part.strip() for part in value.split(",") if part.strip()]
        if not isinstance(value, (list, tuple)):
            raise TypeError("status must be a list of CompletionStatus values")
        return [CompletionStatus(item) if not isinstance(item, CompletionStatus) else item for item in value]

    @field_validator("search_query", mode="before")
    @classmethod
    def normalize_search_query(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("search_query must be a string")
        cleaned = value.strip()
        return cleaned or None


class DashboardActionItemResponse(StrictSchema):
    id: UUID
    title: str
    case_number: str | None = None
    court: str | None = None
    department_name: str | None = None
    priority_badge: str
    due_date: date | None = None
    days_remaining: int | None = None
    status_chip: str
    item_type: str
    description: str
    actual_completion_date: date | None = None
    completion_status: str
    verified_date: date | None = None
    case_title: str | None = None
    parties: str | None = None


class DashboardActionsResponse(PaginatedResponse[DashboardActionItemResponse]):
    pass


class DashboardDepartmentItemResponse(StrictSchema):
    department_id: UUID
    department_name: str
    item_count: int
    overdue_count: int


class DashboardSearchResultResponse(DashboardActionItemResponse):
    rank: float | None = None


class DashboardUrgentActionsResponse(StrictSchema):
    items: list[DashboardActionItemResponse]
