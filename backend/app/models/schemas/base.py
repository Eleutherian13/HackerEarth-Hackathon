from __future__ import annotations

import json
import re
from datetime import date
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


T = TypeVar("T")


class StrictSchema(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=False,
    )


class PaginationMeta(StrictSchema):
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=100)
    pages: int = Field(ge=0)


class PaginatedResponse(StrictSchema, Generic[T]):
    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=100)
    pages: int = Field(ge=0)


class StatusBadge(StrictSchema):
    label: str
    color_code: str


class ReviewerInfo(StrictSchema):
    user_id: UUID
    full_name: str
    email: str


class DocumentReviewStats(StrictSchema):
    approved_count: int = Field(ge=0)
    edited_count: int = Field(ge=0)
    rejected_count: int = Field(ge=0)


class HighlightQuote(StrictSchema):
    text: str
    page: int = Field(ge=1)
    bbox: list[float]

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, value: list[float]) -> list[float]:
        if len(value) != 4:
            raise ValueError("bbox must contain exactly four coordinates")
        if any(coordinate < 0 for coordinate in value):
            raise ValueError("bbox coordinates must be non-negative")
        return value


class SourceEvidenceLink(StrictSchema):
    field_id: UUID | None = None
    quote: str | None = None
    page: int | None = Field(default=None, ge=1)
    note: str | None = None

    @field_validator("quote", "note", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("text value must be a string or None")
        cleaned = re.sub(r"\s+", " ", value).strip()
        return cleaned or None


class DepartmentBreakdownItem(StrictSchema):
    department_id: UUID
    department_name: str
    item_count: int = Field(ge=0)


class WeeklyTrendPoint(StrictSchema):
    week_start: date
    verified_count: int = Field(ge=0)
    pending_count: int = Field(ge=0)
    rejected_count: int = Field(ge=0)


def parse_optional_json_dict(value: Any) -> dict[str, Any] | None:
    if value is None or value == "":
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            raise ValueError("expected a JSON object")
        return parsed
    raise TypeError("expected a dict, JSON string, or None")


def normalize_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("text value must be a string or None")
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned or None


def normalize_required_text(value: Any, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required")
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    cleaned = re.sub(r"\s+", " ", value).strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")
    return cleaned


def coerce_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be an integer")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"{field_name} cannot be blank")
        return int(cleaned)
    raise TypeError(f"{field_name} must be an integer")


def coerce_uuid_list(value: Any) -> list[UUID] | None:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        value = [part.strip() for part in value.split(",") if part.strip()]
    if not isinstance(value, (list, tuple)):
        raise TypeError("expected a list of UUIDs")
    return [UUID(str(item)) if not isinstance(item, UUID) else item for item in value]


def coerce_enum_list(enum_type: type[Any], value: Any) -> list[Any] | None:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        value = [part.strip() for part in value.split(",") if part.strip()]
    if not isinstance(value, (list, tuple)):
        raise TypeError("expected a list of enum values")
    normalized = []
    for item in value:
        normalized.append(item if isinstance(item, enum_type) else enum_type(str(item)))
    return normalized


def coerce_date(value: Any, field_name: str) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, str):
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        return date.fromisoformat(cleaned)
    raise TypeError(f"{field_name} must be a date")
