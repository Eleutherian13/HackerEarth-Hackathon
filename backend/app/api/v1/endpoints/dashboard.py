from __future__ import annotations

import csv
from datetime import date
from io import BytesIO
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.enums import UserRole
from app.models.schemas.dashboard import (
    DashboardActionItemResponse,
    DashboardActionsResponse,
    DashboardDepartmentItemResponse,
    DashboardQueryParams,
    DashboardSearchResultResponse,
)
from app.models.schemas.responses import DashboardStatsResponse
from app.services.dashboard import (
    build_actions_export_csv,
    generate_dashboard_summary_pdf,
    get_dashboard_actions,
    get_dashboard_departments,
    get_dashboard_summary,
    get_dashboard_urgent_actions,
    mark_action_complete,
    search_dashboard_actions,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/summary",
    response_model=DashboardStatsResponse,
    summary="Get dashboard summary stats",
    description="Returns verified action plan dashboard metrics and weekly trends.",
)
async def get_dashboard_summary_endpoint(
    filters: DashboardQueryParams = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> dict[str, Any]:
    return get_dashboard_summary(db=db, current_user=current_user, filters=filters)


@router.get(
    "/actions",
    response_model=DashboardActionsResponse,
    summary="Get verified dashboard actions",
    description="Return a paginated list of verified action items for the dashboard.",
)
async def get_dashboard_actions_endpoint(
    filters: DashboardQueryParams = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> dict[str, Any]:
    items, total = get_dashboard_actions(db=db, current_user=current_user, filters=filters)
    return {
        "items": items,
        "total": total,
        "page": filters.page,
        "per_page": filters.per_page,
        "pages": (total + filters.per_page - 1) // filters.per_page,
    }


@router.get(
    "/departments",
    response_model=list[DashboardDepartmentItemResponse],
    summary="List departments for dashboard filters",
    description="Returns departments with verified action counts and overdue totals.",
)
async def get_dashboard_departments_endpoint(
    filters: DashboardQueryParams = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> list[dict[str, Any]]:
    return get_dashboard_departments(db=db, current_user=current_user, filters=filters)


@router.get(
    "/urgent",
    response_model=list[DashboardActionItemResponse],
    summary="Get urgent dashboard actions",
    description="Returns verified action items that are overdue or due within 7 days.",
)
async def get_dashboard_urgent_endpoint(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> list[dict[str, Any]]:
    return get_dashboard_urgent_actions(db=db, current_user=current_user, limit=limit)


@router.get(
    "/search",
    response_model=list[DashboardSearchResultResponse],
    summary="Search verified actions",
    description="Performs full-text search over verified action plans, case numbers, titles, parties, and descriptions.",
)
async def get_dashboard_search_endpoint(
    search_query: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> list[dict[str, Any]]:
    results = search_dashboard_actions(db=db, current_user=current_user, search_query=search_query)
    return [dict(item, rank=None) for item in results]


@router.get(
    "/export/csv",
    summary="Export verified actions to CSV",
    description="Exports verified dashboard actions into a downloadable CSV.",
)
async def export_dashboard_csv_endpoint(
    filters: DashboardQueryParams = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> StreamingResponse:
    items, _ = get_dashboard_actions(db=db, current_user=current_user, filters=filters)
    payload = build_actions_export_csv(items)
    filename = f"verified_actions_export_{date.today().isoformat()}.csv"
    return StreamingResponse(
        BytesIO(payload),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
        },
    )


@router.get(
    "/export/pdf-report",
    summary="Export dashboard PDF report",
    description="Generates a PDF summary report for verified dashboard actions.",
)
async def export_dashboard_pdf_report_endpoint(
    filters: DashboardQueryParams = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> StreamingResponse:
    summary = get_dashboard_summary(db=db, current_user=current_user, filters=filters)
    departments = get_dashboard_departments(db=db, current_user=current_user, filters=filters)
    urgent_items = get_dashboard_urgent_actions(db=db, current_user=current_user, limit=20)
    payload = generate_dashboard_summary_pdf(summary=summary, department_breakdown=departments, urgent_items=urgent_items)
    filename = f"verified_actions_report_{date.today().isoformat()}.pdf"
    return StreamingResponse(
        BytesIO(payload),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
        },
    )


@router.post(
    "/actions/{action_item_id}/complete",
    response_model=DashboardActionItemResponse,
    summary="Mark an action item complete",
    description="Mark an eligible verified action item as complete with audit-friendly date stamping.",
)
async def complete_dashboard_action_endpoint(
    action_item_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> dict[str, Any]:
    try:
        action_uuid = UUID(action_item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid action item ID format")
    return mark_action_complete(db=db, action_item_id=action_uuid, current_user=current_user)
