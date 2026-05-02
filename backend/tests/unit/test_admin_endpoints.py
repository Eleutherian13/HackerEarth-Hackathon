"""Unit tests for backend admin endpoint logic."""

import pytest

from app.api.v1.endpoints.admin import (
    get_audit_logs,
    get_queue_status,
    get_system_settings,
    list_departments,
    list_users,
    update_user,
)
from app.models.domain.models import AuditLog, Department, User, ProcessingJob
from app.models.enums import AuditEventType, JobStatus, UserRole
from tests.factories import make_audit_log, make_department, make_processing_job, make_user
from tests.utils import FakeSession


class TestAdminEndpoints:
    @pytest.fixture
    def admin_user(self):
        return make_user(role=UserRole.ADMIN)

    @pytest.mark.asyncio
    async def test_list_users_filters_role_and_department(self):
        department = make_department(name="Legal", code="LEGAL")
        admin = make_user(email="admin@org.com", role=UserRole.ADMIN, department_id=department.id)
        reviewer = make_user(email="reviewer@org.com", role=UserRole.REVIEWER, department_id=department.id)
        other_department = make_department(name="Finance", code="FIN")
        other_admin = make_user(email="other@org.com", role=UserRole.ADMIN, department_id=other_department.id)

        db = FakeSession({User: [admin, reviewer, other_admin]})

        response = await list_users(db=db, role=UserRole.ADMIN, department_id=department.id, page=1, per_page=50)

        assert response.total == 1
        assert len(response.items) == 1
        assert response.items[0].id == admin.id
        assert response.items[0].role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_update_user_changes_role_and_status(self):
        user = make_user(email="user@example.com", role=UserRole.VIEWER, is_active=False)
        db = FakeSession({User: [user]})

        updated = await update_user(
            user_id=user.id,
            update_data=type("UpdateData", (), {"role": UserRole.ADMIN, "is_active": True})(),
            db=db,
        )

        assert updated.role == UserRole.ADMIN
        assert updated.is_active is True
        assert user.role == UserRole.ADMIN
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_update_user_raises_not_found(self):
        db = FakeSession({User: []})
        with pytest.raises(Exception) as exc_info:
            await update_user(
                user_id=make_user().id,
                update_data=type("UpdateData", (), {"role": UserRole.ADMIN, "is_active": True})(),
                db=db,
            )

        assert "User not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_audit_logs_filters_by_action(self):
        log_upload = make_audit_log(action="UPLOAD", event_type=AuditEventType.DOCUMENT_UPLOADED)
        log_verify = make_audit_log(action="VERIFY", event_type=AuditEventType.FIELD_VERIFIED)
        db = FakeSession({AuditLog: [log_upload, log_verify]})

        response = await get_audit_logs(
            db=db,
            document_id=None,
            user_id=None,
            entity_type=None,
            event_type=None,
            action="UPLOAD",
            page=1,
            per_page=50,
        )

        assert response.total == 1
        assert len(response.items) == 1
        assert response.items[0].action == "UPLOAD"

    @pytest.mark.asyncio
    async def test_list_departments_counts_active_users(self):
        department = make_department(name="Audit", code="AUDIT")
        department.users = [make_user(email="a@org.com", role=UserRole.OFFICER, department_id=department.id)]
        db = FakeSession({Department: [department]})

        response = await list_departments(db=db, page=1, per_page=50)

        assert response.total == 1
        assert response.items[0].active_user_count == 1

    @pytest.mark.asyncio
    async def test_get_queue_status_counts_jobs(self):
        running = make_processing_job(status=JobStatus.IN_PROGRESS)
        failed = make_processing_job(status=JobStatus.FAILED)
        db = FakeSession({ProcessingJob: [running, failed]})

        status = await get_queue_status(db=db)

        assert status.processing == 1
        assert status.failed == 1
        assert status.pending == 0
        assert status.completed == 0

    @pytest.mark.asyncio
    async def test_get_system_settings_returns_defaults(self):
        settings = await get_system_settings()

        assert settings.app_name is not None
        assert settings.version is not None
        assert settings.audit_enabled is True
