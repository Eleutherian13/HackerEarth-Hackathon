from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from app.models.domain.models import ExtractedField, FieldType
from app.models.enums import ActionType, DueDateSource, Priority

ACTION_KEYWORDS = {
    ActionType.COMPLIANCE: ["comply", "follow", "implement", "file", "submit", "pay", "serve"],
    ActionType.APPEAL_CONSIDERATION: ["appeal", "review petition", "slp", "special leave petition"],
    ActionType.INTERNAL_REVIEW: ["examine", "verify", "check", "audit", "review"],
    ActionType.ESCALATION: ["report", "escalate", "refer", "notify"],
    ActionType.MONITORING: ["monitor", "track", "oversee", "supervise"],
}

DEPARTMENT_KEYWORDS = {
    "Legal Department": ["legal", "law", "advocate", "counsel", "litigation"],
    "Compliance Department": ["compliance", "regulatory", "statutory", "obligation"],
    "Audit": ["audit", "examine", "verify", "inspect"],
    "Finance": ["finance", "payment", "cost", "penalty", "fee"],
    "Operations": ["operations", "operational", "implement", "execute"],
    "Administration": ["administration", "admin", "secretariat", "office"],
}

DUE_DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")
WITHIN_DAYS_PATTERN = re.compile(r"within\s+(\d+)\s+days", re.IGNORECASE)
LATIN_DDMMYY = re.compile(r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})")


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().split())


def _contains_keyword(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _parse_explicit_date(text: str | None) -> date | None:
    if not text:
        return None
    match = DUE_DATE_PATTERN.search(text)
    if match:
        try:
            return date.fromisoformat(match.group(1))
        except ValueError:
            pass

    match = LATIN_DDMMYY.search(text)
    if match:
        day, month, year = match.groups()
        year = year if len(year) == 4 else f"20{year}"
        try:
            return date(int(year), int(month), int(day))
        except ValueError:
            return None

    return None


def _parse_relative_due_date(text: str, judgment_date: date) -> tuple[date | None, DueDateSource]:
    lowered = text.lower()
    match = WITHIN_DAYS_PATTERN.search(lowered)
    if match:
        days = int(match.group(1))
        return judgment_date + timedelta(days=days), DueDateSource.INFERRED

    if "forthwith" in lowered or "immediately" in lowered:
        return judgment_date + timedelta(days=7), DueDateSource.INFERRED

    return None, DueDateSource.INFERRED


def _extract_judgment_date(fields: list[ExtractedField]) -> date | None:
    for field in fields:
        if field.field_type == FieldType.JUDGMENT_DATE:
            explicit = _parse_explicit_date(field.normalized_value or field.value)
            if explicit:
                return explicit
    return None


def _summarize_title(text: str) -> str:
    text = _normalize_text(text)
    if not text:
        return "Review judgment direction"
    if "." in text:
        first = text.split(".")[0]
        if len(first) <= 200:
            return first
    return text[:200].rstrip() + ("..." if len(text) > 200 else "")


def _determine_action_type(text: str) -> ActionType:
    for action_type, keywords in ACTION_KEYWORDS.items():
        if _contains_keyword(text, keywords):
            return action_type
    return ActionType.COMPLIANCE


def _determine_priority(text: str, due_date: date | None, penalty_risk: str | None, contempt_risk: str | None) -> Priority:
    lowered = text.lower()
    if "urgent" in lowered or "immediately" in lowered:
        return Priority.CRITICAL

    if penalty_risk and "high" in penalty_risk.lower():
        return Priority.CRITICAL
    if contempt_risk and "high" in contempt_risk.lower():
        return Priority.CRITICAL

    if due_date:
        delta = (due_date - date.today()).days
        if delta <= 7:
            return Priority.CRITICAL
        if delta <= 30:
            return Priority.HIGH
        if delta <= 90:
            return Priority.MEDIUM

    return Priority.MEDIUM


def _extract_department_from_text(text: str) -> str | None:
    lowered = text.lower()
    matches: list[str] = []
    for department, keywords in DEPARTMENT_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            matches.append(department)
    if len(matches) == 1:
        return matches[0]
    return None


def _build_cost_action(field: ExtractedField, judgment_date: date | None) -> dict[str, Any]:
    text = _normalize_text(field.value)
    explicit = _parse_explicit_date(text)
    due_date = explicit
    due_date_source = DueDateSource.EXPLICIT_IN_JUDGMENT if explicit else DueDateSource.INFERRED
    penalty_risk = None
    contempt_risk = None
    amount = None

    if "amount" in text.lower():
        match = re.search(r"amount[:\s]*([\d,\.]+)", text, re.IGNORECASE)
        if match:
            amount = match.group(1)
    if "penalty" in text.lower():
        match = re.search(r"penalty.*?(high|medium|low)", text, re.IGNORECASE)
        if match:
            penalty_risk = match.group(1)
    if "contempt" in text.lower():
        match = re.search(r"contempt.*?(high|medium|low)", text, re.IGNORECASE)
        if match:
            contempt_risk = match.group(1)

    if not due_date and judgment_date is not None:
        due_date = judgment_date + timedelta(days=30)

    priority = _determine_priority(text, due_date, penalty_risk, contempt_risk)
    if amount and ("high" in (contumpt_risk or "") or "high" in (penalty_risk or "")):
        priority = Priority.CRITICAL

    return {
        "extracted_field_id": field.id,
        "item_type": ActionType.COMPLIANCE,
        "title": _summarize_title(text or "Pay awarded costs and penalties"),
        "description": text or "Pay costs and penalties as ordered by the judgment.",
        "priority": priority,
        "due_date": due_date,
        "due_date_source": due_date_source,
        "responsible_department_name": _extract_department_from_text(text) or None,
        "responsible_department_id": None,
        "responsible_officer": None,
        "risk_if_ignored": (
            "Failure to pay awarded costs or meet penalty requirements may expose the organization to contempt proceedings."
        ),
        "suggested_next_step": (
            "Review the cost order, confirm the amount, and prepare payment instructions."
        ),
        "source_evidence": {
            "field_type": field.field_type.value,
            "quotes": field.source_quotes,
            "source_page_ids": field.source_page_ids,
            "field_ids": [str(field.id)],
        },
    }


def derive_action_plan_items(fields: list[ExtractedField]) -> list[dict[str, Any]]:
    """Derive initial action plan items from verified extracted fields."""
    items: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    judgment_date = _extract_judgment_date(fields) or date.today()
    penalty_field = next((field for field in fields if field.field_type == FieldType.PENALTY_RISK), None)
    contempt_field = next((field for field in fields if field.field_type == FieldType.CONTEMPT_RISK), None)
    responsible_field = next((field for field in fields if field.field_type == FieldType.RESPONSIBLE_DEPARTMENT), None)
    penalty_risk = _normalize_text(penalty_field.value) if penalty_field else None
    contempt_risk = _normalize_text(contempt_field.value) if contempt_field else None

    for field in fields:
        field_text = _normalize_text(field.value)
        if not field_text:
            continue

        if field.field_type == FieldType.COST_ORDER:
            plan_item = _build_cost_action(field, judgment_date)
        else:
            item_type = _determine_action_type(field_text)
            default_due_date, default_source = _parse_relative_due_date(field_text, judgment_date)
            explicit_due_date = _parse_explicit_date(field_text)
            due_date = explicit_due_date or default_due_date or (judgment_date + timedelta(days=30))
            due_date_source = (
                DueDateSource.EXPLICIT_IN_JUDGMENT if explicit_due_date else default_source
            )
            if field.field_type == FieldType.DEADLINE:
                due_date_source = DueDateSource.EXPLICIT_IN_JUDGMENT if explicit_due_date else DueDateSource.INFERRED

            department_name = None
            if responsible_field:
                department_name = _normalize_text(responsible_field.value)
            if not department_name:
                department_name = _extract_department_from_text(field_text)

            plan_item = {
                "extracted_field_id": field.id,
                "item_type": item_type,
                "title": _summarize_title(field_text),
                "description": field_text,
                "priority": _determine_priority(field_text, due_date, penalty_risk, contempt_risk),
                "due_date": due_date,
                "due_date_source": due_date_source,
                "responsible_department_name": department_name,
                "responsible_department_id": None,
                "responsible_officer": None,
                "risk_if_ignored": (
                    "Non-compliance may be treated as contempt of court." if "contempt" in field_text.lower() or (contempt_risk and "high" in contempt_risk.lower())
                    else "Non-compliance may result in financial or operational penalties."
                ),
                "suggested_next_step": (
                    "Assign this item to the appropriate operational or legal team and confirm the deadline." if item_type == ActionType.COMPLIANCE
                    else "Review the direction and update the plan with the right team assignments."
                ),
                "source_evidence": {
                    "field_type": field.field_type.value,
                    "quotes": field.source_quotes,
                    "source_page_ids": field.source_page_ids,
                    "field_ids": [str(field.id)],
                },
            }

        if plan_item["title"] not in seen_titles:
            items.append(plan_item)
            seen_titles.add(plan_item["title"])

    return items


__all__ = ["derive_action_plan_items", "_extract_judgment_date"]
