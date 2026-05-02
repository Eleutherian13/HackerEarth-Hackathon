from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from app.api.deps import get_current_active_user, get_db, require_verified_document
from app.core.security import UserRole
from app.models.domain.models import ActionPlanItem, AuditLog, Document, ExtractedField
from app.models.enums import VerificationStatus
from app.services.dashboard.export_service import generate_case_report_pdf

router = APIRouter(prefix="/cases", tags=["cases"])


def _build_document_payload(document: Document) -> dict[str, Any]:
    metadata = document.metadata_json or {}
    return {
        "id": str(document.id),
        "case_number": metadata.get("case_number"),
        "case_title": metadata.get("case_title"),
        "court": metadata.get("court_name"),
        "judgment_date": metadata.get("judgment_date"),
        "parties": metadata.get("parties"),
        "bench": metadata.get("bench_info"),
        "filename": document.original_filename,
        "processing_status": document.processing_status.value,
        "uploaded_at": document.created_at.isoformat(),
    }


def _build_extracted_field_payload(field: ExtractedField) -> dict[str, Any]:
    return {
        "id": str(field.id),
        "field_type": field.field_type.value,
        "value": field.value,
        "confidence_score": field.confidence_score,
        "verification_status": field.verification_status.value,
        "verified_by_user_id": str(field.verified_by_user_id) if field.verified_by_user_id else None,
        "verified_at": field.verified_at.isoformat() if field.verified_at else None,
        "source_quotes": field.source_quotes,
        "is_inferred": field.is_inferred,
        "inference_rationale": field.inference_rationale,
    }


def _build_action_item_payload(item: ActionPlanItem) -> dict[str, Any]:
    return {
        "id": str(item.id),
        "title": item.title,
        "description": item.description,
        "item_type": item.item_type.value,
        "priority": item.priority.value,
        "due_date": item.due_date.isoformat() if item.due_date else None,
        "due_date_source": item.due_date_source.value,
        "responsible_department_id": str(item.responsible_department_id) if item.responsible_department_id else None,
        "responsible_department_name": item.responsible_department.name if item.responsible_department else None,
        "responsible_officer": item.responsible_officer,
        "risk_if_ignored": item.risk_if_ignored,
        "suggested_next_step": item.suggested_next_step,
        "verification_status": item.verification_status.value,
        "completion_status": item.completion_status.value,
        "actual_completion_date": item.actual_completion_date.isoformat() if item.actual_completion_date else None,
        "notes": item.notes,
        "source_evidence": item.source_evidence,
    }


def _build_history_entry(entry: AuditLog) -> dict[str, Any]:
    return {
        "id": str(entry.id),
        "event_type": entry.event_type.value,
        "action": entry.action,
        "changes": entry.changes,
        "user_id": str(entry.user_id) if entry.user_id else None,
        "timestamp": entry.created_at.isoformat(),
    }


def _assert_case_access(db: Session, document: Document, current_user):
    if current_user.role == UserRole.OFFICER:
        owned_action = (
            db.query(ActionPlanItem)
            .filter(ActionPlanItem.document_id == document.id)
            .filter(ActionPlanItem.responsible_department_id == current_user.department_id)
            .first()
        )
        if not owned_action:
            raise HTTPException(status_code=403, detail="department access denied")


@router.get("/{document_id}", summary="Get case detail", description="Retrieve case detail with verified extractions and action plan.")
async def get_case_detail(
    document: Document = Depends(require_verified_document()),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> dict[str, Any]:
    _assert_case_access(db, document, current_user)
    extracted_fields = (
        db.query(ExtractedField)
        .filter(ExtractedField.document_id == document.id)
        .filter(ExtractedField.verification_status.in_([VerificationStatus.APPROVED, VerificationStatus.EDITED]))
        .order_by(ExtractedField.field_type)
        .all()
    )
    action_items = (
        db.query(ActionPlanItem)
        .filter(ActionPlanItem.document_id == document.id)
        .filter(ActionPlanItem.verification_status == VerificationStatus.APPROVED)
        .order_by(ActionPlanItem.priority.desc(), ActionPlanItem.due_date.asc())
        .all()
    )
    completed_count = sum(1 for item in action_items if item.completion_status.value == "COMPLETED")
    pending_count = sum(1 for item in action_items if item.completion_status.value != "COMPLETED")
    return {
        "document": _build_document_payload(document),
        "overview": {
            "total_verified_extractions": len(extracted_fields),
            "verified_action_items": len(action_items),
            "completed_actions": completed_count,
            "pending_actions": pending_count,
        },
        "extractions": [_build_extracted_field_payload(field) for field in extracted_fields],
        "action_plan": [_build_action_item_payload(item) for item in action_items],
        "history": [],
    }


@router.get("/{document_id}/history", summary="Get case history", description="Retrieve full audit history for a case.")
async def get_case_history(
    document: Document = Depends(require_verified_document()),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> list[dict[str, Any]]:
    _assert_case_access(db, document, current_user)
    history_entries = (
        db.query(AuditLog)
        .filter(AuditLog.document_id == document.id)
        .order_by(AuditLog.created_at.desc())
        .limit(200)
        .all()
    )
    return [_build_history_entry(entry) for entry in history_entries]


@router.get("/{document_id}/report", summary="Get case report PDF", description="Generate a PDF report for a case.")
async def get_case_report(
    document: Document = Depends(require_verified_document()),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> StreamingResponse:
    _assert_case_access(db, document, current_user)
    action_items = (
        db.query(ActionPlanItem)
        .filter(ActionPlanItem.document_id == document.id)
        .filter(ActionPlanItem.verification_status == VerificationStatus.APPROVED)
        .order_by(ActionPlanItem.priority.desc(), ActionPlanItem.due_date.asc())
        .all()
    )
    case_data = {
        "case_number": document.metadata_json.get("case_number"),
        "case_title": document.metadata_json.get("case_title"),
        "court": document.metadata_json.get("court_name"),
        "judgment_date": document.metadata_json.get("judgment_date"),
        "parties": document.metadata_json.get("parties"),
    }
    payload = generate_case_report_pdf(case_data=case_data, action_items=[_build_action_item_payload(item) for item in action_items])
    filename = f"case_report_{document.id}.pdf"
    return StreamingResponse(
        BytesIO(payload),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )
