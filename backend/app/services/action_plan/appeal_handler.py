from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from app.models.enums import ActionType, DueDateSource, Priority
from app.models.domain.models import ExtractedField, FieldType
from app.services.action_plan.rule_engine import _extract_judgment_date


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().split())


def _is_appealable(text: str) -> bool:
    lowered = text.lower()
    if "not appealable" in lowered:
        return False
    return any(keyword in lowered for keyword in ["appealable", "appeal", "review petition", "slp"])


def _parse_limitation_period(text: str) -> int | None:
    match = re.search(r"limitation period\s*(?:of\s*)?(\d+)\s*days", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _parse_appeal_forum(text: str) -> str | None:
    match = re.search(r"via\s+([A-Za-z0-9 ()/,&]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def extract_appeal_items(fields: list[ExtractedField]) -> list[dict[str, Any]]:
    """Create action plan items for potential appeal or review pathways."""
    appeal_items: list[dict[str, Any]] = []
    judgment_date = _extract_judgment_date(fields) or date.today()

    for field in fields:
        if field.field_type != FieldType.APPEAL_CLUE:
            continue
        clue_text = _normalize_text(field.value)
        if not _is_appealable(clue_text):
            continue

        limitation_days = _parse_limitation_period(clue_text)
        appeal_forum = _parse_appeal_forum(clue_text) or "the appropriate appellate forum"
        buffer_days = 7
        if limitation_days and limitation_days > buffer_days:
            due_date = judgment_date + timedelta(days=limitation_days - buffer_days)
        elif limitation_days:
            due_date = judgment_date + timedelta(days=1)
        else:
            due_date = judgment_date + timedelta(days=30)

        appeal_items.append(
            {
                "extracted_field_id": field.id,
                "item_type": ActionType.APPEAL_CONSIDERATION,
                "title": f"Consider filing appeal in {appeal_forum}",
                "description": (
                    f"Consider filing appeal against the judgment order in {appeal_forum}."
                ),
                "priority": Priority.HIGH,
                "due_date": due_date,
                "due_date_source": DueDateSource.ESTIMATED,
                "responsible_department_id": None,
                "responsible_officer": None,
                "risk_if_ignored": (
                    "Right of appeal may be lost if not filed within limitation period."
                ),
                "suggested_next_step": (
                    f"Consider filing appeal against the judgment dated {judgment_date.isoformat()} in {appeal_forum}."
                ),
                "source_evidence": {
                    "field_type": field.field_type.value,
                    "quotes": field.source_quotes,
                    "source_page_ids": field.source_page_ids,
                    "field_ids": [str(field.id)],
                },
            }
        )

    return appeal_items
