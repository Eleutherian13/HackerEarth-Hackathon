from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.api.deps import get_current_active_user, get_db
from app.api.v1.endpoints.review import build_stale_review_response
from app.models.domain.models import ActionPlanItem, Document, ExtractedField, User
from app.models.schemas.requests import HumanReviewAction
from app.models.schemas.responses import ActionPlanItemResponse, ExtractedFieldResponse
from app.services.action_plan import generate_action_plan_items
from app.services.verification.review_service import review_service

router = APIRouter(prefix="/review", tags=["review"])


class FieldReviewPayload(BaseModel):
    action: HumanReviewAction
    comments: str | None = None
    expected_version: int
    edited_value: str | None = None
    edit_reason: str | None = None


def _build_field_response(field: ExtractedField) -> dict[str, Any]:
    payload = {
        "id": field.id,
        "document_id": field.document_id,
        "field_type": field.field_type.value if hasattr(field.field_type, "value") else str(field.field_type),
        "value": field.value,
        "normalized_value": field.normalized_value,
        "confidence_score": field.confidence_score,
        "extraction_method": field.extraction_method,
        "is_inferred": field.is_inferred,
        "inference_rationale": field.inference_rationale,
        "source_page_ids": field.source_page_ids or [],
        "source_quotes": field.source_quotes or [],
        "verification_status": field.verification_status,
        "version": field.version,
        "verified_by_user_id": field.verified_by_user_id,
        "verified_at": field.verified_at,
        "edit_history": field.edit_history or [],
        "reviewer_comments": field.reviewer_comments,
        "created_at": field.created_at,
        "updated_at": field.updated_at,
        "verification_status_badge": None,
        "reviewer_info": None,
    }
    return ExtractedFieldResponse.model_validate(payload, strict=False).model_dump(mode="json")


def _build_action_item_response(item: ActionPlanItem) -> dict[str, Any]:
    payload = {
        "id": item.id,
        "document_id": item.document_id,
        "extracted_field_id": item.extracted_field_id,
        "item_type": item.item_type.value if hasattr(item.item_type, "value") else str(item.item_type),
        "title": item.title,
        "description": item.description,
        "priority": item.priority,
        "due_date": item.due_date,
        "due_date_source": item.due_date_source.value if hasattr(item.due_date_source, "value") else str(item.due_date_source),
        "responsible_department_id": item.responsible_department_id,
        "responsible_officer": item.responsible_officer,
        "risk_if_ignored": item.risk_if_ignored,
        "suggested_next_step": item.suggested_next_step,
        "source_evidence_links": item.source_evidence.get("links", []) if item.source_evidence else [],
        "source_evidence": item.source_evidence or {},
        "verification_status": item.verification_status,
        "version": item.version,
        "verified_by_user_id": item.verified_by_user_id,
        "verification_date": item.verification_date,
        "completion_status": item.completion_status,
        "actual_completion_date": item.actual_completion_date,
        "notes": item.notes,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "department_name": item.responsible_department.name if item.responsible_department else None,
        "time_until_deadline": None,
        "status_color_code": "#2563eb",
    }
    return ActionPlanItemResponse.model_validate(payload, strict=False).model_dump(mode="json")


@router.get("/documents/{document_id}/fields")
async def get_review_fields(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    try:
        doc_uuid = UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID format")

    document = db.query(Document).filter(Document.id == doc_uuid).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    fields = db.query(ExtractedField).filter(ExtractedField.document_id == doc_uuid).order_by(ExtractedField.created_at.asc()).all()
    return {
        "document_id": document_id,
        "total_fields": len(fields),
        "fields": [_build_field_response(field) for field in fields],
    }


@router.post("/fields/{field_id}/verify")
async def verify_field(
    field_id: UUID,
    payload: FieldReviewPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    field = db.query(ExtractedField).filter(ExtractedField.id == field_id).first()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

    try:
        reviewed = review_service.review_field(
            db=db,
            field_id=field.id,
            action=payload.action,
            edited_value=payload.edited_value,
            comments=payload.comments,
            expected_version=payload.expected_version,
            reviewer_id=current_user.id,
            edit_reason=payload.edit_reason,
        )
    except StaleDataError:
        db.rollback()
        return build_stale_review_response(
            current_version=field.version,
            last_modified_by=field.verified_by_user.full_name if field.verified_by_user else None,
            last_modified_at=field.verified_at.isoformat() if field.verified_at else None,
        )
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

    return {
        "status": "success",
        "field": _build_field_response(reviewed),
    }


@router.post("/documents/{document_id}/generate-action-plan")
async def generate_action_plan(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    try:
        doc_uuid = UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID format")

    document = db.query(Document).filter(Document.id == doc_uuid).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        items = generate_action_plan_items(db=db, document=document, user=current_user, force=True)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {
        "document_id": document_id,
        "generated_count": len(items),
        "action_items": [_build_action_item_response(item) for item in items],
    }