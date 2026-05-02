from __future__ import annotations

from typing import Any

from app.models.enums import ActionType, Priority


def validate_action_plan_items(items: list[dict[str, Any]]) -> list[str]:
    """Run lightweight quality checks against generated action plan items."""
    warnings: list[str] = []
    seen_signatures: set[tuple[str, str]] = set()

    for item in items:
        title = item.get("title", "").strip()
        description = item.get("description", "").strip()
        if not title:
            warnings.append("Generated action item is missing a title.")
        if not description:
            warnings.append("Generated action item is missing a description.")

        signature = (title.lower(), item.get("item_type", "").value if hasattr(item.get("item_type"), "value") else str(item.get("item_type")))
        if signature in seen_signatures:
            warnings.append(f"Duplicate action item detected: {title}")
        else:
            seen_signatures.add(signature)

        if item.get("item_type") == ActionType.COMPLIANCE and item.get("priority") == Priority.LOW:
            warnings.append("Compliance item generated with low priority; verify urgency.")

    return warnings
