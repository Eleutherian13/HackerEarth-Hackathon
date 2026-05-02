"""Integration tests for admin API endpoints with FastAPI TestClient."""

from fastapi.testclient import TestClient
import pytest

from main import create_app
from app.api.deps import get_current_user, get_db
from app.models.enums import AuditEventType, JobStatus, UserRole
from app.models.domain.models import User, AuditLog, Department, ProcessingJob
from tests.factories import make_audit_log, make_department, make_processing_job, make_user
from tests.utils import FakeSession


@pytest.fixture
def fake_session():
    department = make_department(name="Admin Department", code="ADM")
    admin_user = make_user(role=UserRole.ADMIN, department_id=department.id)
    users = [admin_user]
    audit_logs = [
        make_audit_log(action="UPLOAD", entity_type="Document", event_type=AuditEventType.DOCUMENT_UPLOADED),
    ]
    departments = [department]
    jobs = [make_processing_job(status=JobStatus.IN_PROGRESS)]
    return FakeSession({User: users, AuditLog: audit_logs, Department: departments, ProcessingJob: jobs})


@pytest.fixture
def current_admin_user():
    department = make_department(name="Admin Department", code="ADM")
    return make_user(role=UserRole.ADMIN, department_id=department.id)


@pytest.fixture
def client(fake_session, current_admin_user):
    app = create_app()

    app.dependency_overrides[get_db] = lambda: fake_session

    async def override_get_current_user():
        return current_admin_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_admin_users_endpoint_returns_users(client):
    response = client.get("/api/v1/admin/users")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["email"] == "admin@example.com"


def test_admin_audit_logs_endpoint_filters_by_action(client):
    response = client.get("/api/v1/admin/audit-logs", params={"action": "UPLOAD"})

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["action"] == "UPLOAD"
