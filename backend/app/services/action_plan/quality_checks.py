from __future__ import annotations

from datetime import date
from typing import Any

from app.models.enums import ActionType, DueDateSource, Priority


def validate_action_plan_items(items: list[dict[str, Any]]) -> list[str]:
    """Run quality checks on generated action plan items."""
    warnings: list[str] = []

    for item in items:
        title = (item.get("title") or "").strip() or "Unnamed action item"
        source_evidence = item.setdefault("source_evidence", {})
        field_ids = source_evidence.get("field_ids") or []

        if not field_ids:
            warning = f"Action item '{title}' does not reference any source extracted fields."
            warnings.append(warning)
            source_evidence.setdefault("validation_warnings", []).append(warning)

        due_date = item.get("due_date")
        if isinstance(due_date, date) and due_date < date.today():
            warning = f"Action item '{title}' has a past due date."
            warnings.append(warning)
            source_evidence.setdefault("validation_warnings", []).append(warning)

        if item.get("item_type") == ActionType.COMPLIANCE and item.get("priority") == Priority.CRITICAL and not due_date:
            warning = f"Critical compliance item '{title}' has no deadline."
            warnings.append(warning)
            source_evidence.setdefault("validation_warnings", []).append(warning)

        due_date_source = item.get("due_date_source")
        if due_date_source == DueDateSource.INFERRED:
            source_evidence.setdefault("validation_warnings", []).append(
                f"Action item '{title}' relies on an inferred due date."
            )

        if item.get("responsible_department_id") is None and item.get("responsible_department_name"):
            warning = f"Responsible department for '{title}' could not be matched to an active department."
            warnings.append(warning)
            source_evidence.setdefault("validation_warnings", []).append(warning)

        if item.get("item_type") == ActionType.APPEAL_CONSIDERATION and item.get("priority") != Priority.HIGH:
            warning = f"Appeal consideration item '{title}' should typically be HIGH priority."
            warnings.append(warning)
            source_evidence.setdefault("validation_warnings", []).append(warning)

    return warnings
