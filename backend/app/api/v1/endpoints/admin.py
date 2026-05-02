from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.core.config import settings
from app.models.domain.models import AuditLog, Department, ProcessingJob, User
from app.models.enums import JobStatus, UserRole
from app.models.schemas.base import StrictSchema
from app.models.schemas.responses import AuditLogResponse

router = APIRouter(tags=["admin"])


class UserAdminEntry(StrictSchema):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    email: str
    full_name: str
    role: UserRole
    department_id: UUID | None = None
    is_active: bool


class UserAdminUpdate(StrictSchema):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    role: UserRole | None = None
    is_active: bool | None = None


class UserAdminListResponse(StrictSchema):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    items: list[UserAdminEntry]
    total: int


class DepartmentAdminEntry(StrictSchema):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    name: str
    description: str | None = None
    active_user_count: int | None = None


class DepartmentAdminListResponse(StrictSchema):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    items: list[DepartmentAdminEntry]
    total: int


class SystemSettingsResponse(StrictSchema):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    app_name: str
    environment: str
    version: str
    audit_enabled: bool
    default_page_size: int


class QueueStatusResponse(StrictSchema):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    processing: int
    pending: int
    failed: int
    completed: int


@router.get(
    "/admin/audit-logs",
    response_model=AuditLogResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def get_audit_logs(
    db: Session = Depends(get_db),
    document_id: UUID | None = Query(None),
    user_id: UUID | None = Query(None),
    entity_type: str | None = Query(None),
    event_type: str | None = Query(None),
    action: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
) -> AuditLogResponse:
    query = db.query(AuditLog)
    if document_id is not None:
        query = query.filter(AuditLog.document_id == document_id)
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if entity_type is not None:
        query = query.filter(AuditLog.entity_type == entity_type)
    if event_type is not None:
        query = query.filter(AuditLog.event_type == event_type)
    if action is not None:
        query = query.filter(AuditLog.action == action)

    total = query.count()
    items = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return AuditLogResponse(items=items, total=total, page=page, per_page=per_page, pages=(total + per_page - 1) // per_page)


@router.get(
    "/admin/users",
    response_model=UserAdminListResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def list_users(
    db: Session = Depends(get_db),
    role: UserRole | None = Query(None),
    department_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
) -> UserAdminListResponse:
    query = db.query(User)
    if role is not None:
        query = query.filter(User.role == role)
    if department_id is not None:
        query = query.filter(User.department_id == department_id)

    total = query.count()
    users = query.order_by(User.full_name.asc()).offset((page - 1) * per_page).limit(per_page).all()
    return UserAdminListResponse(items=users, total=total)


@router.patch(
    "/admin/users/{user_id}",
    response_model=UserAdminEntry,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def update_user(
    user_id: UUID,
    update_data: UserAdminUpdate,
    db: Session = Depends(get_db),
) -> UserAdminEntry:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if update_data.role is not None:
        user.role = update_data.role
    if update_data.is_active is not None:
        user.is_active = update_data.is_active

    db.add(user)
    db.commit()
    db.refresh(user)
    return UserAdminEntry.from_orm(user)


@router.get(
    "/admin/departments",
    response_model=DepartmentAdminListResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def list_departments(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
) -> DepartmentAdminListResponse:
    query = db.query(Department)
    total = query.count()
    departments = query.order_by(Department.name.asc()).offset((page - 1) * per_page).limit(per_page).all()

    items = [
        DepartmentAdminEntry(
            id=department.id,
            name=department.name,
            description=getattr(department, "description", None),
            active_user_count=len(getattr(department, "users", [])),
        )
        for department in departments
    ]
    return DepartmentAdminListResponse(items=items, total=total)


@router.get(
    "/admin/settings",
    response_model=SystemSettingsResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def get_system_settings() -> SystemSettingsResponse:
    return SystemSettingsResponse(
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        version=settings.APP_VERSION,
        audit_enabled=True,
        default_page_size=settings.DEFAULT_PAGE_SIZE,
    )


@router.get(
    "/admin/queue-status",
    response_model=QueueStatusResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def get_queue_status(db: Session = Depends(get_db)) -> QueueStatusResponse:
    processing = db.query(ProcessingJob).filter(ProcessingJob.status == JobStatus.IN_PROGRESS).count()
    pending = db.query(ProcessingJob).filter(ProcessingJob.status == JobStatus.QUEUED).count()
    failed = db.query(ProcessingJob).filter(ProcessingJob.status == JobStatus.FAILED).count()
    completed = db.query(ProcessingJob).filter(ProcessingJob.status == JobStatus.COMPLETED).count()
    return QueueStatusResponse(processing=processing, pending=pending, failed=failed, completed=completed)
