from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.domain.models import ActionPlanItem, Department, Document, ExtractedField
from app.models.enums import VerificationStatus
from app.services.action_plan.appeal_handler import extract_appeal_items
from app.services.action_plan.quality_checks import validate_action_plan_items
from app.services.action_plan.rule_engine import derive_action_plan_items


def _resolve_department_id(db: Session, item_data: dict[str, Any]) -> str | None:
    department_name = item_data.get("responsible_department_name")
    if not department_name:
        return None

    candidates = (
        db.query(Department)
        .filter(Department.name.ilike(f"%{department_name}%"))
        .all()
    )
    if len(candidates) == 1:
        return candidates[0].id

    source_evidence = item_data.setdefault("source_evidence", {})
    if len(candidates) > 1:
        source_evidence.setdefault("department_matches", [])
        source_evidence["department_matches"].extend([candidate.name for candidate in candidates])
    return None


def _enhance_with_llm(items: list[dict[str, Any]], fields: list[ExtractedField]) -> list[dict[str, Any]]:
    for item in items:
        metadata = item.setdefault("source_evidence", {}).setdefault("generation_metadata", {})
        metadata["method"] = metadata.get("method", "rule_based")
        metadata["model"] = metadata.get("model", "LLM-STUB")
        metadata["review_notes"] = metadata.get(
            "review_notes",
            "LLM enhancement placeholder: no additional inferred items were added."
        )
    return items


def _build_plan_items(db: Session, document: Document, fields: list[ExtractedField]) -> list[ActionPlanItem]:
    evidence_items = derive_action_plan_items(fields)
    evidence_items.extend(extract_appeal_items(fields))
    evidence_items = _enhance_with_llm(evidence_items, fields)
    warnings = validate_action_plan_items(evidence_items)
    if warnings:
        for item in evidence_items:
            item.setdefault("source_evidence", {}).setdefault("validation_warnings", [])
        # In production, log or persist warnings into an audit trail.

    plan_items: list[ActionPlanItem] = []
    for item_data in evidence_items:
        responsible_department_id = _resolve_department_id(db, item_data)
        plan_items.append(
            ActionPlanItem(
                document_id=document.id,
                extracted_field_id=item_data.get("extracted_field_id"),
                item_type=item_data["item_type"],
                title=item_data["title"],
                description=item_data["description"],
                priority=item_data.get("priority"),
                due_date=item_data.get("due_date"),
                due_date_source=item_data.get("due_date_source"),
                responsible_department_id=responsible_department_id,
                responsible_officer=item_data.get("responsible_officer"),
                risk_if_ignored=item_data["risk_if_ignored"],
                suggested_next_step=item_data["suggested_next_step"],
                source_evidence=item_data.get("source_evidence", {}),
            )
        )
    return plan_items


def generate_action_plan_items(db: Session, document: Document, user: Any, force: bool = False) -> list[ActionPlanItem]:
    """Generate structured action plan items from verified extracted fields."""
    verified_fields = (
        db.query(ExtractedField)
        .filter(
            ExtractedField.document_id == document.id,
            ExtractedField.verification_status.in_([VerificationStatus.APPROVED, VerificationStatus.EDITED]),
        )
        .all()
    )
    if not verified_fields:
        raise ValueError("No verified extracted fields available to generate an action plan")

    existing_items = db.query(ActionPlanItem).filter(ActionPlanItem.document_id == document.id).all()
    if existing_items and not force:
        return existing_items

    if existing_items:
        for item in existing_items:
            db.delete(item)
        db.flush()

    plan_items = _build_plan_items(db, document, verified_fields)
    for item in plan_items:
        db.add(item)

    db.commit()
    for item in plan_items:
        db.refresh(item)

    return plan_items


def finalize_action_plan_review(db: Session, document: Document) -> dict[str, Any]:
    """Finalize the action plan review after all plan items have been reviewed."""
    action_items = db.query(ActionPlanItem).filter(ActionPlanItem.document_id == document.id).all()
    if not action_items:
        raise ValueError("No action plan items are available to finalize")

    pending_items = [item for item in action_items if item.verification_status == VerificationStatus.PENDING]
    if pending_items:
        raise ValueError("All action plan items must be reviewed before finalization")

    db.commit()

    summary = {
        "document_id": str(document.id),
        "total_action_items": len(action_items),
        "reviewed_action_items": len(action_items) - len(pending_items),
        "verified_action_items": sum(1 for item in action_items if item.verification_status == VerificationStatus.APPROVED),
    }
    return summary
