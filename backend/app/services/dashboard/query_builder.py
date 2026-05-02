from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session

from app.core.security import UserRole, user_has_department_access
from app.models.domain.models import ActionPlanItem, Department, Document, ExtractedField
from app.models.enums import (
    ActionType,
    CompletionStatus,
    Priority,
    ProcessingStatus,
    VerificationStatus,
)
from app.models.schemas.dashboard import DashboardQueryParams


SORT_FIELDS: dict[str, Any] = {
    "title": ActionPlanItem.title,
    "case_number": Document.metadata_json["case_number"].astext,
    "court": Document.metadata_json["court_name"].astext,
    "priority": ActionPlanItem.priority,
    "due_date": ActionPlanItem.due_date,
    "department_name": Department.name,
    "status": ActionPlanItem.completion_status,
    "type": ActionPlanItem.item_type,
}


def _restrict_to_department_scope(query, db: Session, current_user, filters: DashboardQueryParams):
    if filters.department_id is not None:
        if current_user.role not in {UserRole.ADMIN, UserRole.REVIEWER, UserRole.SUPERADMIN}:
            if not user_has_department_access(db, current_user, filters.department_id):
                raise HTTPException(status_code=403, detail="department access denied")
        query = query.filter(ActionPlanItem.responsible_department_id == filters.department_id)
    elif current_user.role == UserRole.OFFICER:
        query = query.filter(ActionPlanItem.responsible_department_id == current_user.department_id)
    return query


def _apply_dashboard_filters(query, db: Session, current_user, filters: DashboardQueryParams):
    query = _restrict_to_department_scope(query, db, current_user, filters)

    if filters.priority:
        query = query.filter(ActionPlanItem.priority.in_(filters.priority))

    if filters.type:
        query = query.filter(ActionPlanItem.item_type.in_(filters.type))

    if filters.status:
        query = query.filter(ActionPlanItem.completion_status.in_(filters.status))

    if filters.due_date_from is not None:
        query = query.filter(ActionPlanItem.due_date >= filters.due_date_from)

    if filters.due_date_to is not None:
        query = query.filter(ActionPlanItem.due_date <= filters.due_date_to)

    if filters.search_query:
        search_vector = func.to_tsvector(
            "english",
            func.concat_ws(
                " ",
                func.coalesce(Document.metadata_json["case_number"].astext, ""),
                func.coalesce(Document.metadata_json["case_title"].astext, ""),
                func.coalesce(Document.metadata_json["court_name"].astext, ""),
                func.coalesce(Document.metadata_json["parties"].astext, ""),
                ActionPlanItem.title,
                ActionPlanItem.description,
            ),
        )
        query = query.filter(
            search_vector.op("@@")(func.plainto_tsquery("english", filters.search_query))
        )

    return query


def _build_base_action_query(db: Session):
    return (
        db.query(
            ActionPlanItem,
            Department.name.label("department_name"),
            Document.metadata_json["case_number"].astext.label("case_number"),
            Document.metadata_json["court_name"].astext.label("court"),
            Document.metadata_json["case_title"].astext.label("case_title"),
            Document.metadata_json["parties"].astext.label("parties"),
        )
        .join(Document, ActionPlanItem.document_id == Document.id)
        .join(ExtractedField, ActionPlanItem.extracted_field_id == ExtractedField.id)
        .outerjoin(Department, ActionPlanItem.responsible_department_id == Department.id)
        .filter(ActionPlanItem.verification_status == VerificationStatus.APPROVED)
        .filter(Document.processing_status == ProcessingStatus.VERIFIED)
        .filter(
            ExtractedField.verification_status.in_(
                [VerificationStatus.APPROVED, VerificationStatus.EDITED]
            )
        )
    )


def _sort_query(query, sort_by: str, sort_order: str):
    field = SORT_FIELDS.get(sort_by, ActionPlanItem.due_date)
    if sort_order.lower() == "desc":
        return query.order_by(desc(field))
    return query.order_by(field)


def _calculate_days_remaining(due_date: date | None) -> int | None:
    if due_date is None:
        return None
    return (due_date - date.today()).days


def _build_action_item_payload(row: tuple[ActionPlanItem, str | None, str | None, str | None, str | None, str | None]) -> dict[str, Any]:
    action_item, department_name, case_number, court, case_title, parties = row
    due_date = action_item.due_date
    return {
        "id": action_item.id,
        "title": action_item.title,
        "case_number": case_number,
        "court": court,
        "department_name": department_name,
        "priority_badge": action_item.priority.value,
        "due_date": due_date,
        "days_remaining": _calculate_days_remaining(due_date),
        "status_chip": action_item.completion_status.value,
        "item_type": action_item.item_type.value,
        "description": action_item.description,
        "actual_completion_date": action_item.actual_completion_date,
        "completion_status": action_item.completion_status.value,
        "verified_date": action_item.verification_date,
        "case_title": case_title,
        "parties": parties,
    }


def get_dashboard_actions(db: Session, current_user, filters: DashboardQueryParams) -> tuple[list[dict[str, Any]], int]:
    query = _apply_dashboard_filters(_build_base_action_query(db), db, current_user, filters)
    total = query.order_by(None).with_entities(func.count(ActionPlanItem.id)).scalar() or 0
    query = _sort_query(query, filters.sort_by, filters.sort_order)
    items = query.offset((filters.page - 1) * filters.per_page).limit(filters.per_page).all()
    return [ _build_action_item_payload(row) for row in items ], total


def get_dashboard_summary(db: Session, current_user, filters: DashboardQueryParams) -> dict[str, Any]:
    base_query = _apply_dashboard_filters(_build_base_action_query(db), db, current_user, filters)
    total_verified_items = base_query.order_by(None).with_entities(func.count(ActionPlanItem.id)).scalar() or 0
    actions_by_priority = {
        priority.value: count
        for priority, count in db.query(ActionPlanItem.priority, func.count(ActionPlanItem.id))
        .select_from(ActionPlanItem)
        .join(Document, ActionPlanItem.document_id == Document.id)
        .join(ExtractedField, ActionPlanItem.extracted_field_id == ExtractedField.id)
        .filter(ActionPlanItem.verification_status == VerificationStatus.APPROVED)
        .filter(Document.processing_status == ProcessingStatus.VERIFIED)
        .filter(
            ExtractedField.verification_status.in_(
                [VerificationStatus.APPROVED, VerificationStatus.EDITED]
            )
        )
        .group_by(ActionPlanItem.priority)
        .all()
    }
    actions_by_type = {
        action_type.value: count
        for action_type, count in db.query(ActionPlanItem.item_type, func.count(ActionPlanItem.id))
        .select_from(ActionPlanItem)
        .join(Document, ActionPlanItem.document_id == Document.id)
        .join(ExtractedField, ActionPlanItem.extracted_field_id == ExtractedField.id)
        .filter(ActionPlanItem.verification_status == VerificationStatus.APPROVED)
        .filter(Document.processing_status == ProcessingStatus.VERIFIED)
        .filter(
            ExtractedField.verification_status.in_(
                [VerificationStatus.APPROVED, VerificationStatus.EDITED]
            )
        )
        .group_by(ActionPlanItem.item_type)
        .all()
    }
    overdue_items_count = base_query.filter(ActionPlanItem.due_date < date.today()).order_by(None).with_entities(func.count(ActionPlanItem.id)).scalar() or 0
    urgent_deadlines_within_7_days = base_query.filter(
        ActionPlanItem.due_date >= date.today(),
        ActionPlanItem.due_date <= date.today() + timedelta(days=7),
    ).order_by(None).with_entities(func.count(ActionPlanItem.id)).scalar() or 0
    deadlines_within_30_days = base_query.filter(
        ActionPlanItem.due_date >= date.today(),
        ActionPlanItem.due_date <= date.today() + timedelta(days=30),
    ).order_by(None).with_entities(func.count(ActionPlanItem.id)).scalar() or 0
    department_breakdown = [
        {
            "department_id": department_id,
            "department_name": department_name,
            "item_count": item_count,
        }
        for department_id, department_name, item_count in db.query(
            Department.id,
            Department.name,
            func.count(ActionPlanItem.id),
        )
        .select_from(Department)
        .join(ActionPlanItem, ActionPlanItem.responsible_department_id == Department.id)
        .join(Document, ActionPlanItem.document_id == Document.id)
        .join(ExtractedField, ActionPlanItem.extracted_field_id == ExtractedField.id)
        .filter(ActionPlanItem.verification_status == VerificationStatus.APPROVED)
        .filter(Document.processing_status == ProcessingStatus.VERIFIED)
        .filter(
            ExtractedField.verification_status.in_(
                [VerificationStatus.APPROVED, VerificationStatus.EDITED]
            )
        )
        .group_by(Department.id, Department.name)
        .order_by(Department.name)
        .all()
    ]

    four_weeks_ago = date.today() - timedelta(weeks=4)
    weekly_rows = (
        db.query(
            func.date_trunc("week", ActionPlanItem.verification_date).cast(date).label("week_start"),
            func.count(ActionPlanItem.id).label("verified_count"),
            func.sum(
                case(
                    (
                        ActionPlanItem.completion_status.in_(
                            [
                                CompletionStatus.NOT_STARTED,
                                CompletionStatus.IN_PROGRESS,
                                CompletionStatus.OVERDUE,
                            ]
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("pending_count"),
            func.sum(
                case(
                    (ActionPlanItem.verification_status == VerificationStatus.REJECTED, 1),
                    else_=0,
                )
            ).label("rejected_count"),
        )
        .select_from(ActionPlanItem)
        .join(Document, ActionPlanItem.document_id == Document.id)
        .join(ExtractedField, ActionPlanItem.extracted_field_id == ExtractedField.id)
        .filter(ActionPlanItem.verification_status == VerificationStatus.APPROVED)
        .filter(Document.processing_status == ProcessingStatus.VERIFIED)
        .filter(
            ExtractedField.verification_status.in_(
                [VerificationStatus.APPROVED, VerificationStatus.EDITED]
            )
        )
        .filter(ActionPlanItem.verification_date >= four_weeks_ago)
        .group_by("week_start")
        .order_by("week_start")
        .all()
    )

    weekly_trend = [
        {
            "week_start": row.week_start,
            "verified_count": row.verified_count or 0,
            "pending_count": row.pending_count or 0,
            "rejected_count": row.rejected_count or 0,
        }
        for row in weekly_rows
    ]

    return {
        "total_verified_items": total_verified_items,
        "actions_by_priority": actions_by_priority,
        "actions_by_type": actions_by_type,
        "overdue_items_count": overdue_items_count,
        "due_within_7_days": urgent_deadlines_within_7_days,
        "due_within_30_days": deadlines_within_30_days,
        "department_breakdown": department_breakdown,
        "weekly_trend": weekly_trend,
    }


def get_dashboard_departments(db: Session, current_user, filters: DashboardQueryParams | None = None) -> list[dict[str, Any]]:
    query = (
        db.query(
            Department.id,
            Department.name,
            func.count(ActionPlanItem.id).label("item_count"),
            func.sum(
                case((ActionPlanItem.due_date < date.today(), 1), else_=0)
            ).label("overdue_count"),
        )
        .select_from(Department)
        .join(ActionPlanItem, ActionPlanItem.responsible_department_id == Department.id)
        .join(Document, ActionPlanItem.document_id == Document.id)
        .join(ExtractedField, ActionPlanItem.extracted_field_id == ExtractedField.id)
        .filter(ActionPlanItem.verification_status == VerificationStatus.APPROVED)
        .filter(Document.processing_status == ProcessingStatus.VERIFIED)
        .filter(
            ExtractedField.verification_status.in_(
                [VerificationStatus.APPROVED, VerificationStatus.EDITED]
            )
        )
    )
    if filters is not None:
        query = _apply_dashboard_filters(query, db, current_user, filters)
    if current_user.role == UserRole.OFFICER:
        query = query.filter(ActionPlanItem.responsible_department_id == current_user.department_id)
    departments = query.group_by(Department.id, Department.name).order_by(Department.name).all()
    return [
        {
            "department_id": department_id,
            "department_name": department_name,
            "item_count": item_count,
            "overdue_count": int(overdue_count or 0),
        }
        for department_id, department_name, item_count, overdue_count in departments
    ]


def get_dashboard_urgent_actions(db: Session, current_user, limit: int = 20) -> list[dict[str, Any]]:
    filters = DashboardQueryParams()
    base_query = _apply_dashboard_filters(_build_base_action_query(db), db, current_user, filters)
    urgent_query = base_query.filter(
        ActionPlanItem.due_date.isnot(None),
        ActionPlanItem.due_date <= date.today() + timedelta(days=7),
    ).order_by(ActionPlanItem.due_date.asc()).limit(limit)
    items = urgent_query.all()
    return [ _build_action_item_payload(row) for row in items ]


def search_dashboard_actions(db: Session, current_user, search_query: str, limit: int = 50) -> list[dict[str, Any]]:
    if not search_query:
        return []

    filters = DashboardQueryParams(search_query=search_query, page=1, per_page=limit, sort_by="relevance")
    query = _build_base_action_query(db)
    query = _restrict_to_department_scope(query, db, current_user, filters)
    search_vector = func.to_tsvector(
        "english",
        func.concat_ws(
            " ",
            func.coalesce(Document.metadata_json["case_number"].astext, ""),
            func.coalesce(Document.metadata_json["case_title"].astext, ""),
            func.coalesce(Document.metadata_json["court_name"].astext, ""),
            func.coalesce(Document.metadata_json["parties"].astext, ""),
            ActionPlanItem.title,
            ActionPlanItem.description,
        ),
    )
    ts_query = func.plainto_tsquery("english", search_query)
    query = query.filter(search_vector.op("@@")(ts_query))
    query = query.order_by(desc(func.ts_rank_cd(search_vector, ts_query))).limit(limit)
    items = query.all()
    return [ _build_action_item_payload(row) for row in items ]


def mark_action_complete(db: Session, action_item_id: UUID, current_user) -> dict[str, Any]:
    item = db.get(ActionPlanItem, action_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    if current_user.role == UserRole.OFFICER and item.responsible_department_id != current_user.department_id:
        raise HTTPException(status_code=403, detail="department access denied")
    item.completion_status = CompletionStatus.COMPLETED
    item.actual_completion_date = date.today()
    db.commit()
    db.refresh(item)

    department_name = item.responsible_department.name if item.responsible_department else None
    case_number = item.document.metadata_json.get("case_number") if item.document.metadata_json else None
    court = item.document.metadata_json.get("court_name") if item.document.metadata_json else None
    return {
        "id": item.id,
        "title": item.title,
        "case_number": case_number,
        "court": court,
        "department_name": department_name,
        "priority_badge": item.priority.value,
        "due_date": item.due_date,
        "days_remaining": _calculate_days_remaining(item.due_date),
        "status_chip": item.completion_status.value,
        "item_type": item.item_type.value,
        "description": item.description,
        "actual_completion_date": item.actual_completion_date,
        "completion_status": item.completion_status.value,
        "verified_date": item.verification_date,
        "case_title": item.document.metadata_json.get("case_title") if item.document.metadata_json else None,
        "parties": item.document.metadata_json.get("parties") if item.document.metadata_json else None,
    }
