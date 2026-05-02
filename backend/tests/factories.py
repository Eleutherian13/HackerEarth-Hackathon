from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.models.domain.models import AuditLog, Department, ProcessingJob, User
from app.models.enums import AuditEventType, JobStatus, JobType, ProcessingStatus, UserRole


def make_department(
    name: str = "Test Department",
    code: str = "TEST",
    parent_department_id: uuid.UUID | None = None,
    is_active: bool = True,
    id: uuid.UUID | None = None,
) -> Department:
    department = Department()
    department.id = id or uuid.uuid4()
    department.name = name
    department.code = code
    department.parent_department_id = parent_department_id
    department.is_active = is_active
    department.users = []
    return department


def make_user(
    email: str = "admin@example.com",
    full_name: str = "Admin User",
    role: UserRole = UserRole.ADMIN,
    department_id: uuid.UUID | None = None,
    is_active: bool = True,
    id: uuid.UUID | None = None,
    hashed_password: str = "hashed-password",
    last_login: datetime | None = None,
    must_change_password: bool = False,
    password_changed_at: datetime | None = None,
) -> User:
    user = User()
    user.id = id or uuid.uuid4()
    user.email = email
    user.full_name = full_name
    user.hashed_password = hashed_password
    user.department_id = department_id or uuid.uuid4()
    user.role = role
    user.is_active = is_active
    user.last_login = last_login
    user.must_change_password = must_change_password
    user.password_changed_at = password_changed_at
    user.department = None
    user.uploaded_documents = []
    user.verified_fields = []
    user.verified_action_plan_items = []
    user.review_sessions = []
    user.audit_events = []
    user.refresh_tokens = []
    return user


def make_audit_log(
    event_type: AuditEventType = AuditEventType.USER_ACTION,
    action: str = "TEST_ACTION",
    entity_type: str = "User",
    user_id: uuid.UUID | None = None,
    document_id: uuid.UUID | None = None,
    entity_id: uuid.UUID | None = None,
    changes: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    created_at: datetime | None = None,
    id: uuid.UUID | None = None,
) -> AuditLog:
    audit_log = AuditLog()
    audit_log.id = id or uuid.uuid4()
    audit_log.event_type = event_type
    audit_log.user_id = user_id
    audit_log.document_id = document_id
    audit_log.entity_type = entity_type
    audit_log.entity_id = entity_id
    audit_log.action = action
    audit_log.changes = changes or {}
    audit_log.ip_address = ip_address
    audit_log.user_agent = user_agent
    audit_log.created_at = created_at or datetime.now(timezone.utc)
    return audit_log


def make_processing_job(
    document_id: uuid.UUID | None = None,
    job_type: JobType = JobType.INGESTION,
    status: JobStatus = JobStatus.QUEUED,
    id: uuid.UUID | None = None,
    created_at: datetime | None = None,
) -> ProcessingJob:
    job = ProcessingJob()
    job.id = id or uuid.uuid4()
    job.document_id = document_id or uuid.uuid4()
    job.job_type = job_type
    job.status = status
    job.created_at = created_at or datetime.now(timezone.utc)
    return job
