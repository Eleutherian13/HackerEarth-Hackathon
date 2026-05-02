"""
Action plan endpoints.

Handles retrieval, approval, modification, editing, and finalization of generated action plan items.
"""

from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.audit import log_action_plan_generated, log_action_plan_verified
from app.models.domain.models import ActionPlanItem, Department, Document, ExtractedField
from app.models.enums import CompletionStatus, ProcessingStatus, VerificationStatus
from app.models.schemas.requests import (
    ActionPlanDecision,
    ActionPlanEditRequest,
    ActionPlanReviewRequest,
)
from app.models.schemas.responses import ActionPlanItemResponse
from app.services.action_plan import generate_action_plan_items, finalize_action_plan_review

router = APIRouter(tags=["action-plan"])


def _format_time_until_deadline(due_date: date | None) -> str | None:
    if due_date is None:
        return None

    delta_days = (due_date - datetime.utcnow().date()).days
    if delta_days < 0:
        return f"{abs(delta_days)} days overdue"
    if delta_days == 0:
        return "Due today"
    if delta_days == 1:
        return "1 day"
    return f"{delta_days} days"


def _status_color_code(completion_status: str) -> str:
    return {
        "COMPLETED": "#16a34a",
        "IN_PROGRESS": "#f97316",
        "OVERDUE": "#dc2626",
        "CANCELLED": "#6b7280",
    }.get(completion_status, "#2563eb")


def _build_action_plan_item_response(item: ActionPlanItem) -> dict[str, Any]:
    return {
        "id": str(item.id),
        "document_id": str(item.document_id),
        "extracted_field_id": str(item.extracted_field_id) if item.extracted_field_id else None,
        "item_type": item.item_type.value,
        "title": item.title,
        "description": item.description,
        "priority": item.priority.value,
        "due_date": item.due_date.isoformat() if item.due_date else None,
        "due_date_source": item.due_date_source.value,
        "responsible_department_id": str(item.responsible_department_id) if item.responsible_department_id else None,
        "responsible_officer": item.responsible_officer,
        "risk_if_ignored": item.risk_if_ignored,
        "suggested_next_step": item.suggested_next_step,
        "source_evidence_links": item.source_evidence.get("links", []),
        "source_evidence": item.source_evidence,
        "verification_status": item.verification_status.value,
        "verified_by_user_id": str(item.verified_by_user_id) if item.verified_by_user_id else None,
        "verification_date": item.verification_date.isoformat() if item.verification_date else None,
        "completion_status": item.completion_status.value,
        "actual_completion_date": item.actual_completion_date.isoformat() if item.actual_completion_date else None,
        "notes": item.notes,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
        "department_name": item.responsible_department.name if item.responsible_department else None,
        "time_until_deadline": _format_time_until_deadline(item.due_date),
        "status_color_code": _status_color_code(item.completion_status.value),
    }


@router.get(
    "/documents/{document_id}/action-plan",
    response_model=list[ActionPlanItemResponse],
    summary="Get generated action plan items",
    description="Retrieve generated action plan items for a document, including computed metadata.",
)
async def get_action_plan(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> list[dict[str, Any]]:
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    document = db.query(Document).filter(Document.id == doc_uuid).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    action_items = db.query(ActionPlanItem).filter(ActionPlanItem.document_id == doc_uuid).all()
    if not action_items:
        try:
            action_items = generate_action_plan_items(db=db, document=document, user=current_user)
            await log_action_plan_generated(db, document_id=document.id, item_count=len(action_items))
        except ValueError:
            return []
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    return [_build_action_plan_item_response(item) for item in action_items]


@router.post(
    "/documents/{document_id}/action-plan/{plan_item_id}/review",
    response_model=ActionPlanItemResponse,
    summary="Review an action plan item",
    description="Approve, modify, or reject a generated action plan item.",
)
@router.post(
    "/action-items/{plan_item_id}/review",
    response_model=ActionPlanItemResponse,
    summary="Review an action plan item",
    description="Approve, modify, or reject a generated action plan item.",
)
async def review_action_plan_item(
    plan_item_id: str,
    review_request: ActionPlanReviewRequest,
    document_id: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> dict[str, Any]:
    if document_id is not None:
        try:
            uuid.UUID(document_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid document ID format")

    try:
        plan_uuid = uuid.UUID(plan_item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan item ID format")

    plan_item = db.query(ActionPlanItem).filter(ActionPlanItem.id == plan_uuid).first()
    if not plan_item:
        raise HTTPException(status_code=404, detail="Action plan item not found")

    if document_id is not None:
        doc_uuid = uuid.UUID(document_id)
        if plan_item.document_id != doc_uuid:
            raise HTTPException(status_code=404, detail="Action plan item not found for the document")

    if review_request.action == ActionPlanDecision.APPROVE:
        plan_item.verification_status = VerificationStatus.APPROVED
    elif review_request.action == ActionPlanDecision.MODIFY:
        modifications = review_request.modifications or {}
        if "title" in modifications:
            plan_item.title = modifications["title"]
        if "description" in modifications:
            plan_item.description = modifications["description"]
        if "priority" in modifications:
            plan_item.priority = modifications["priority"]
        if "due_date" in modifications:
            try:
                plan_item.due_date = date.fromisoformat(modifications["due_date"])
            except Exception:
                plan_item.due_date = None
        if "responsible_officer" in modifications:
            plan_item.responsible_officer = modifications["responsible_officer"]
        if "risk_if_ignored" in modifications:
            plan_item.risk_if_ignored = modifications["risk_if_ignored"]
        if "suggested_next_step" in modifications:
            plan_item.suggested_next_step = modifications["suggested_next_step"]
        if "notes" in modifications:
            plan_item.notes = modifications["notes"]
        plan_item.verification_status = VerificationStatus.MODIFIED
    elif review_request.action == ActionPlanDecision.REJECT:
        plan_item.verification_status = VerificationStatus.REJECTED
    else:
        raise HTTPException(status_code=400, detail="Invalid review action")

    plan_item.verified_by_user_id = current_user.id
    plan_item.verification_date = datetime.utcnow()
    db.commit()
    db.refresh(plan_item)

    return _build_action_plan_item_response(plan_item)


@router.put(
    "/action-items/{plan_item_id}/edit",
    response_model=ActionPlanItemResponse,
    summary="Edit an action plan item",
    description="Update fields of an action plan item without finalizing review.",
)
async def edit_action_plan_item(
    plan_item_id: str,
    edit_request: ActionPlanEditRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> dict[str, Any]:
    try:
        plan_uuid = uuid.UUID(plan_item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan item ID format")

    plan_item = db.query(ActionPlanItem).filter(ActionPlanItem.id == plan_uuid).first()
    if not plan_item:
        raise HTTPException(status_code=404, detail="Action plan item not found")

    if edit_request.title is not None:
        plan_item.title = edit_request.title
    if edit_request.description is not None:
        plan_item.description = edit_request.description
    if edit_request.priority is not None:
        plan_item.priority = edit_request.priority
    if edit_request.due_date is not None:
        plan_item.due_date = edit_request.due_date
    if edit_request.responsible_officer is not None:
        plan_item.responsible_officer = edit_request.responsible_officer
    if edit_request.responsible_department_id is not None:
        plan_item.responsible_department_id = edit_request.responsible_department_id
    if edit_request.responsible_department_name is not None:
        department = (
            db.query(Department)
            .filter(Department.name.ilike(f"%{edit_request.responsible_department_name}%"))
            .first()
        )
        if department:
            plan_item.responsible_department_id = department.id
    if edit_request.risk_if_ignored is not None:
        plan_item.risk_if_ignored = edit_request.risk_if_ignored
    if edit_request.suggested_next_step is not None:
        plan_item.suggested_next_step = edit_request.suggested_next_step
    if edit_request.notes is not None:
        plan_item.notes = edit_request.notes

    db.commit()
    db.refresh(plan_item)

    return _build_action_plan_item_response(plan_item)


@router.post(
    "/documents/{document_id}/finalize-plan",
    summary="Finalize action plan review",
    description="Finalize the action plan after human review.",
)
async def finalize_action_plan(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> dict[str, Any]:
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    document = db.query(Document).filter(Document.id == doc_uuid).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    action_items = db.query(ActionPlanItem).filter(ActionPlanItem.document_id == doc_uuid).all()
    if not action_items:
        raise HTTPException(status_code=400, detail="No action plan items available to finalize")

    pending_items = [item for item in action_items if item.verification_status == VerificationStatus.PENDING]
    if pending_items:
        raise HTTPException(status_code=400, detail="All action plan items must be reviewed before finalization")

    if all(field.verification_status in {VerificationStatus.APPROVED, VerificationStatus.EDITED} for field in document.extracted_fields):
        document.processing_status = ProcessingStatus.VERIFIED
    document.updated_at = datetime.utcnow()
    db.commit()

    await log_action_plan_verified(db, document_id=document.id, user_id=current_user.id, verified_count=len(action_items))

    return {
        "document_id": str(document.id),
        "total_action_items": len(action_items),
        "reviewed_action_items": len(action_items) - len(pending_items),
        "verified_action_items": sum(1 for item in action_items if item.verification_status == VerificationStatus.APPROVED),
        "finalized": True,
    }
