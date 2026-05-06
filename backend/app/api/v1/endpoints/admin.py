from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ConfigDict, field_serializer
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_role
from app.core.config import settings
from app.models.domain.models import AuditLog, Department, ProcessingJob, User
from app.models.enums import JobStatus, UserRole, AccessRequestStatus
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


# ============ Access Request Management ============

class AccessRequestEntry(StrictSchema):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    email: str
    full_name: str
    status: str
    created_at: datetime
    reviewed_at: datetime | None = None
    
    @field_serializer('status')
    def serialize_status(self, value):
        if isinstance(value, AccessRequestStatus):
            return value.value
        return value


class AccessRequestListResponse(StrictSchema):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    items: list[AccessRequestEntry]
    total: int


class AccessRequestApprovalPayload(StrictSchema):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, strict=False)

    department_id: UUID


class AccessRequestApprovalResponse(StrictSchema):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    message: str
    user_id: UUID | None = None
    temporary_password: str | None = None


class AccessRequestRejectionPayload(StrictSchema):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    reason: str = "Your access request could not be approved at this time."


@router.get(
    "/admin/access-requests",
    response_model=AccessRequestListResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def list_access_requests(
    db: Session = Depends(get_db),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
) -> AccessRequestListResponse:
    """List all access requests."""
    from app.models.domain.models import AccessRequest
    from app.models.enums import AccessRequestStatus
    from sqlalchemy import select
    
    query = select(AccessRequest)
    
    if status:
        # Convert string to enum
        try:
            status_enum = AccessRequestStatus[status.upper()]
            query = query.where(AccessRequest.status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    else:
        # Default to showing pending requests
        query = query.where(AccessRequest.status == AccessRequestStatus.PENDING)
    
    # Order by newest first
    query = query.order_by(AccessRequest.created_at.desc())
    
    # Get total count with the same filter
    count_query = select(func.count()).select_from(AccessRequest)
    if status:
        try:
            status_enum = AccessRequestStatus[status.upper()]
            count_query = count_query.where(AccessRequest.status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    else:
        count_query = count_query.where(AccessRequest.status == AccessRequestStatus.PENDING)
    
    total = db.execute(count_query).scalar()
    items = db.execute(query.limit(per_page).offset((page - 1) * per_page)).scalars().all()
    
    return AccessRequestListResponse(
        items=[AccessRequestEntry.model_validate(item) for item in items],
        total=total,
    )


@router.post(
    "/admin/access-requests/{request_id}/approve",
    response_model=AccessRequestApprovalResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def approve_access_request(
    request_id: UUID,
    payload: AccessRequestApprovalPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AccessRequestApprovalResponse:
    """Approve an access request and create a user account."""
    from app.models.domain.models import AccessRequest
    from app.models.enums import AccessRequestStatus
    from sqlalchemy import select
    from app.core.security import hash_password
    import secrets
    import string
    
    # Get the access request
    access_request = db.execute(
        select(AccessRequest).where(AccessRequest.id == request_id)
    ).scalar_one_or_none()
    
    if not access_request:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    if access_request.status != AccessRequestStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve a request with status {access_request.status}",
        )
    
    # Check if department exists
    department = db.query(Department).filter(Department.id == payload.department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Use password from request if provided, otherwise generate temporary one
    if access_request.hashed_password:
        hashed_password = access_request.hashed_password
        temporary_password = None
        must_change = False
    else:
        # Generate temporary password guaranteed to meet strength requirements
        upper = string.ascii_uppercase
        lower = string.ascii_lowercase
        digits = string.digits
        special = "!@#$%^&*"
        all_chars = upper + lower + digits + special
        
        password_chars = [
            secrets.choice(upper),
            secrets.choice(lower),
            secrets.choice(digits),
            secrets.choice(special),
        ]
        password_chars.extend(secrets.choice(all_chars) for _ in range(8))
        secrets.SystemRandom().shuffle(password_chars)
        temporary_password = "".join(password_chars)
        hashed_password = hash_password(temporary_password)
        must_change = True
    
    # Create user account
    new_user = User(
        email=access_request.email,
        full_name=access_request.full_name,
        hashed_password=hashed_password,
        department_id=payload.department_id,
        role=UserRole.OFFICER,
        is_active=True,
        must_change_password=must_change,
    )
    
    db.add(new_user)
    db.flush()
    
    # Update access request
    from datetime import datetime, timezone
    access_request.status = AccessRequestStatus.APPROVED
    access_request.reviewed_by_admin_id = current_user.id
    access_request.reviewed_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(new_user)
    
    # Send approval email (only if temp password was generated)
    if temporary_password:
        try:
            from app.core.email import send_approval_email
            await send_approval_email(
                requester_name=access_request.full_name,
                requester_email=access_request.email,
                temporary_password=temporary_password,
            )
        except Exception as e:
            print(f"Warning: Failed to send approval email: {e}")
    
    return AccessRequestApprovalResponse(
        message=f"User account created for {access_request.full_name}",
        user_id=new_user.id,
        temporary_password=temporary_password,
    )


@router.post(
    "/admin/access-requests/{request_id}/reject",
    response_model=dict,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def reject_access_request(
    request_id: UUID,
    payload: AccessRequestRejectionPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    """Reject an access request."""
    from app.models.domain.models import AccessRequest
    from app.models.enums import AccessRequestStatus
    from sqlalchemy import select
    from datetime import datetime, timezone
    
    # Get the access request
    access_request = db.execute(
        select(AccessRequest).where(AccessRequest.id == request_id)
    ).scalar_one_or_none()
    
    if not access_request:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    if access_request.status != AccessRequestStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject a request with status {access_request.status}",
        )
    
    # Update access request
    access_request.status = AccessRequestStatus.REJECTED
    access_request.decision_reason = payload.reason
    access_request.reviewed_by_admin_id = current_user.id
    access_request.reviewed_at = datetime.now(timezone.utc)
    
    db.commit()
    
    # Send rejection email
    try:
        from app.core.email import send_rejection_email
        await send_rejection_email(
            requester_name=access_request.full_name,
            requester_email=access_request.email,
            rejection_reason=payload.reason,
        )
    except Exception as e:
        print(f"Warning: Failed to send rejection email: {e}")
        # Don't fail the request if email fails
    
    return {"message": f"Access request from {access_request.full_name} has been rejected"}
