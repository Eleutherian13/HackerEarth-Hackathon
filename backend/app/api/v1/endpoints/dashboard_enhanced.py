"""
Enhanced dashboard endpoints with real data metrics.
"""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.domain.models import ActionPlanItem, Document, Department, User
from app.models.enums import ProcessingStatus, Priority, CompletionStatus, VerificationStatus

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary(
    department_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Return dashboard metrics using verified action plans.
    
    Returns:
    - Total action items count
    - Breakdown by priority
    - Overdue items
    - Due this week
    - Completion statistics
    - Department breakdown
    """
    # Base query - only verified documents with approved action plans
    base_query = db.query(ActionPlanItem).join(Document).filter(
        Document.processing_status == ProcessingStatus.VERIFIED,
        ActionPlanItem.verification_status == VerificationStatus.APPROVED
    )
    
    # Filter by department if provided
    if department_id:
        base_query = base_query.filter(ActionPlanItem.responsible_department_id == department_id)
    
    # Calculate metrics
    total = base_query.count()
    critical = base_query.filter(ActionPlanItem.priority == Priority.CRITICAL).count()
    high = base_query.filter(ActionPlanItem.priority == Priority.HIGH).count()
    medium = base_query.filter(ActionPlanItem.priority == Priority.MEDIUM).count()
    low = base_query.filter(ActionPlanItem.priority == Priority.LOW).count()
    
    today = date.today()
    overdue = base_query.filter(
        ActionPlanItem.due_date < today,
        ActionPlanItem.completion_status != CompletionStatus.COMPLETED
    ).count()
    
    due_this_week = base_query.filter(
        ActionPlanItem.due_date.between(today, today + timedelta(days=7)),
        ActionPlanItem.completion_status != CompletionStatus.COMPLETED
    ).count()
    
    completed = base_query.filter(
        ActionPlanItem.completion_status == CompletionStatus.COMPLETED
    ).count()
    
    # Department breakdown
    dept_counts = db.query(
        Department.name,
        func.count(ActionPlanItem.id)
    ).join(ActionPlanItem).filter(
        ActionPlanItem.verification_status == VerificationStatus.APPROVED
    ).group_by(Department.name).all()
    
    completion_rate = round(completed / total * 100, 1) if total > 0 else 0
    
    return {
        "status": "success",
        "timestamp": date.today().isoformat(),
        "metrics": {
            "total_actions": total,
            "by_priority": {
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low
            },
            "status": {
                "overdue": overdue,
                "due_this_week": due_this_week,
                "completed": completed,
                "in_progress": total - completed - overdue
            },
            "completion_rate_percent": completion_rate
        },
        "departments": [
            {"name": name, "count": count} for name, count in dept_counts
        ]
    }


@router.get("/actions")
async def dashboard_actions(
    department_id: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    due_date_from: Optional[str] = None,
    due_date_to: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get paginated, filtered action plan items for dashboard.
    
    Filters:
    - department_id: Filter by responsible department
    - priority: Filter by priority (CRITICAL, HIGH, MEDIUM, LOW)
    - status: Filter by completion status
    - due_date_from/to: Filter by due date range
    - search: Search in title and description
    """
    query = db.query(ActionPlanItem).join(Document).filter(
        Document.processing_status == ProcessingStatus.VERIFIED,
        ActionPlanItem.verification_status == VerificationStatus.APPROVED
    )
    
    # Apply filters
    if department_id:
        query = query.filter(ActionPlanItem.responsible_department_id == department_id)
    if priority:
        try:
            priority_enum = Priority[priority]
            query = query.filter(ActionPlanItem.priority == priority_enum)
        except KeyError:
            pass
    if status:
        try:
            status_enum = CompletionStatus[status]
            query = query.filter(ActionPlanItem.completion_status == status_enum)
        except KeyError:
            pass
    if due_date_from:
        try:
            due_from = date.fromisoformat(due_date_from)
            query = query.filter(ActionPlanItem.due_date >= due_from)
        except ValueError:
            pass
    if due_date_to:
        try:
            due_to = date.fromisoformat(due_date_to)
            query = query.filter(ActionPlanItem.due_date <= due_to)
        except ValueError:
            pass
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                ActionPlanItem.title.ilike(search_term),
                ActionPlanItem.description.ilike(search_term),
                Document.original_filename.ilike(search_term)
            )
        )
    
    total = query.count()
    items = query.order_by(
        ActionPlanItem.priority.asc(),
        ActionPlanItem.due_date.asc()
    ).offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        "status": "success",
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        },
        "items": [
            {
                "id": str(item.id),
                "document_id": str(item.document_id),
                "item_type": item.item_type.value,
                "title": item.title,
                "description": item.description[:200],
                "priority": item.priority.value,
                "due_date": item.due_date.isoformat() if item.due_date else None,
                "responsible_department": item.responsible_department.name if item.responsible_department else None,
                "completion_status": item.completion_status.value,
                "days_remaining": (item.due_date - date.today()).days if item.due_date else None,
                "is_overdue": item.due_date < date.today() if item.due_date else False
            }
            for item in items
        ]
    }


@router.get("/critical-items")
async def get_critical_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all critical priority items that are not yet completed."""
    today = date.today()
    
    critical_items = db.query(ActionPlanItem).join(Document).filter(
        Document.processing_status == ProcessingStatus.VERIFIED,
        ActionPlanItem.verification_status == VerificationStatus.APPROVED,
        ActionPlanItem.priority == Priority.CRITICAL,
        ActionPlanItem.completion_status != CompletionStatus.COMPLETED
    ).order_by(
        ActionPlanItem.due_date.asc()
    ).all()
    
    return {
        "status": "success",
        "count": len(critical_items),
        "items": [
            {
                "id": str(item.id),
                "title": item.title,
                "due_date": item.due_date.isoformat() if item.due_date else None,
                "days_remaining": (item.due_date - today).days if item.due_date else None,
                "responsible_department": item.responsible_department.name if item.responsible_department else None,
                "risk_if_ignored": item.risk_if_ignored
            }
            for item in critical_items[:10]  # Top 10 critical items
        ]
    }


@router.get("/overdue-items")
async def get_overdue_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all overdue items that haven't been completed."""
    today = date.today()
    
    overdue_items = db.query(ActionPlanItem).join(Document).filter(
        Document.processing_status == ProcessingStatus.VERIFIED,
        ActionPlanItem.verification_status == VerificationStatus.APPROVED,
        ActionPlanItem.due_date < today,
        ActionPlanItem.completion_status != CompletionStatus.COMPLETED
    ).order_by(
        ActionPlanItem.due_date.asc()
    ).all()
    
    return {
        "status": "success",
        "count": len(overdue_items),
        "items": [
            {
                "id": str(item.id),
                "title": item.title,
                "due_date": item.due_date.isoformat() if item.due_date else None,
                "days_overdue": (today - item.due_date).days,
                "responsible_department": item.responsible_department.name if item.responsible_department else None
            }
            for item in overdue_items
        ]
    }


@router.get("/completion-trends")
async def get_completion_trends(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get action completion trends for the specified number of days."""
    start_date = date.today() - timedelta(days=days)
    
    completions_by_date = db.query(
        func.date(ActionPlanItem.actual_completion_date),
        func.count(ActionPlanItem.id)
    ).filter(
        ActionPlanItem.actual_completion_date >= start_date,
        ActionPlanItem.completion_status == CompletionStatus.COMPLETED
    ).group_by(
        func.date(ActionPlanItem.actual_completion_date)
    ).order_by(
        func.date(ActionPlanItem.actual_completion_date)
    ).all()
    
    return {
        "status": "success",
        "period_days": days,
        "data": [
            {
                "date": completion_date.isoformat(),
                "count": count
            }
            for completion_date, count in completions_by_date
        ]
    }


@router.post("/actions/{action_id}/mark-complete")
async def mark_action_complete(
    action_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark an action plan item as completed."""
    import uuid
    try:
        action_uuid = uuid.UUID(action_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid action ID format")
    
    item = db.query(ActionPlanItem).filter(ActionPlanItem.id == action_uuid).first()
    if not item:
        raise HTTPException(status_code=404, detail="Action not found")
    
    if item.completion_status == CompletionStatus.COMPLETED:
        return {"status": "already_complete", "message": "Action already marked as completed"}
    
    item.completion_status = CompletionStatus.COMPLETED
    item.actual_completion_date = date.today()
    db.commit()
    
    return {
        "status": "success",
        "action_id": action_id,
        "completion_status": item.completion_status.value,
        "completed_on": item.actual_completion_date.isoformat()
    }
