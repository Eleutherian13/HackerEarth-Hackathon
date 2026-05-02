from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm.exc import StaleDataError

from main import create_app
from app.api.deps import get_current_active_user, get_db
from app.api.v1.endpoints import documents as documents_endpoint
from app.api.v1.endpoints import action_plan as action_plan_endpoint
from app.models.domain.models import ActionPlanItem, Department, Document, ExtractedField, User
from app.models.enums import (
    ActionType,
    CompletionStatus,
    DueDateSource,
    ExtractionMethod,
    FieldType,
    Priority,
    ProcessingStatus,
    UserRole,
    VerificationStatus,
)
from app.models.schemas.requests import ActionPlanDecision, HumanReviewAction
from tests.factories import make_department, make_user
from tests.utils import FakeSession


def _make_document(reviewer: User) -> Document:
    document = Document()
    document.id = uuid.uuid4()
    document.file_hash = "a" * 64
    document.original_filename = "judgment.pdf"
    document.storage_path = "documents/judgment.pdf"
    document.mime_type = "application/pdf"
    document.file_size_bytes = 1024
    document.page_count = 1
    document.is_text_based = True
    document.processing_status = ProcessingStatus.PENDING_REVIEW
    document.error_message = None
    document.uploaded_by_user_id = reviewer.id
    document.uploaded_by_user = reviewer
    document.metadata_json = {}
    document.created_at = datetime.now(timezone.utc)
    document.updated_at = datetime.now(timezone.utc)
    document.extracted_fields = []
    document.action_plan_items = []
    return document


def _make_extracted_field(document: Document, reviewer: User | None = None) -> ExtractedField:
    field = ExtractedField()
    field.id = uuid.uuid4()
    field.document_id = document.id
    field.field_type = FieldType.CASE_NUMBER
    field.value = "WP(C) 123/2025"
    field.normalized_value = "WPC1232025"
    field.confidence_score = 0.99
    field.extraction_method = ExtractionMethod.DIRECT_EXTRACT
    field.is_inferred = False
    field.inference_rationale = None
    field.source_page_ids = [1]
    field.source_quotes = []
    field.verification_status = VerificationStatus.UNVERIFIED
    field.version = 1
    field.verified_by_user_id = reviewer.id if reviewer else None
    field.verified_by_user = reviewer
    field.verified_at = None
    field.edit_history = []
    field.reviewer_comments = None
    field.created_at = datetime.now(timezone.utc)
    field.updated_at = datetime.now(timezone.utc)
    return field


def _make_action_item(document: Document, reviewer: User | None = None) -> ActionPlanItem:
    item = ActionPlanItem()
    item.id = uuid.uuid4()
    item.document_id = document.id
    item.extracted_field_id = None
    item.item_type = ActionType.COMPLIANCE
    item.title = "File compliance affidavit"
    item.description = "Prepare and file the compliance affidavit."
    item.priority = Priority.HIGH
    item.due_date = None
    item.due_date_source = DueDateSource.INFERRED
    item.responsible_department_id = None
    item.responsible_officer = None
    item.risk_if_ignored = "Potential contempt exposure."
    item.suggested_next_step = "Assign to legal cell."
    item.source_evidence = {"links": []}
    item.verification_status = VerificationStatus.PENDING
    item.version = 1
    item.verified_by_user_id = reviewer.id if reviewer else None
    item.verified_by_user = reviewer
    item.verification_date = None
    item.completion_status = CompletionStatus.NOT_STARTED
    item.actual_completion_date = None
    item.notes = None
    item.created_at = datetime.now(timezone.utc)
    item.updated_at = datetime.now(timezone.utc)
    item.document = document
    item.responsible_department = None
    return item


@pytest.fixture
def reviewer_user():
    department = make_department(name="Legal Department", code="LEG")
    return make_user(full_name="Reviewer A", role=UserRole.REVIEWER, department_id=department.id)


@pytest.fixture
def concurrency_session(reviewer_user):
    document = _make_document(reviewer_user)
    field = _make_extracted_field(document)
    item = _make_action_item(document)
    document.extracted_fields = [field]
    document.action_plan_items = [item]
    return FakeSession({
        User: [reviewer_user],
        Department: [reviewer_user.department] if reviewer_user.department else [],
        Document: [document],
        ExtractedField: [field],
        ActionPlanItem: [item],
    })


@pytest.fixture
def client(concurrency_session, reviewer_user, monkeypatch):
    app = create_app()

    app.dependency_overrides[get_db] = lambda: concurrency_session
    app.dependency_overrides[get_current_active_user] = lambda: reviewer_user

    def fake_transition_to(self, new_status, updated_by, reason=None):
        self.processing_status = new_status
        self.updated_at = datetime.now(timezone.utc)

    monkeypatch.setattr(Document, "transition_to", fake_transition_to, raising=False)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def _install_field_review_service(monkeypatch, concurrency_session, reviewer_user):
    def fake_review_field(db, field_id, action, edited_value, comments, expected_version, reviewer_id, edit_reason=None):
        field = db.query(ExtractedField).filter(ExtractedField.id == field_id).first()
        if field.version != expected_version:
            raise StaleDataError(
                f"Field was modified by another reviewer. Expected version {expected_version}, current version {field.version}. Reload to see latest changes."
            )

        field.verified_by_user = reviewer_user
        field.verified_by_user_id = reviewer_id
        field.verified_at = datetime.now(timezone.utc)
        field.reviewer_comments = comments
        field.version += 1

        if action == HumanReviewAction.APPROVE:
            field.verification_status = VerificationStatus.APPROVED
        elif action == HumanReviewAction.EDIT:
            field.verification_status = VerificationStatus.EDITED
            field.value = edited_value or field.value
            field.normalized_value = edited_value or field.normalized_value
            field.edit_history.append(
                {
                    "edited_at": datetime.now(timezone.utc).isoformat(),
                    "edited_by": str(reviewer_id),
                    "previous_value": field.value,
                    "edited_value": edited_value,
                    "edit_reason": edit_reason,
                }
            )
        elif action == HumanReviewAction.REJECT:
            field.verification_status = VerificationStatus.REJECTED
        return field

    monkeypatch.setattr(documents_endpoint.review_service, "review_field", fake_review_field)


def _install_action_plan_review_service(monkeypatch, concurrency_session, reviewer_user):
    def fake_review_action_plan_item(db, item_id, action, modifications, comments, expected_version, reviewer_id):
        item = db.query(ActionPlanItem).filter(ActionPlanItem.id == item_id).first()
        if item.version != expected_version:
            raise StaleDataError(
                f"Field was modified by another reviewer. Expected version {expected_version}, current version {item.version}. Reload to see latest changes."
            )

        item.verified_by_user = reviewer_user
        item.verified_by_user_id = reviewer_id
        item.verification_date = datetime.now(timezone.utc)
        item.version += 1

        if action == ActionPlanDecision.APPROVE:
            item.verification_status = VerificationStatus.APPROVED
        elif action == ActionPlanDecision.MODIFY:
            item.verification_status = VerificationStatus.MODIFIED
            modifications = modifications or {}
            if "title" in modifications:
                item.title = modifications["title"]
            if "notes" in modifications:
                item.notes = modifications["notes"]
        elif action == ActionPlanDecision.REJECT:
            item.verification_status = VerificationStatus.REJECTED
        return item

    monkeypatch.setattr(action_plan_endpoint.review_service, "review_action_plan_item", fake_review_action_plan_item)


def test_concurrent_review_same_field(client, concurrency_session, reviewer_user, monkeypatch):
    _install_field_review_service(monkeypatch, concurrency_session, reviewer_user)
    document = concurrency_session.query(Document).first()
    field = concurrency_session.query(ExtractedField).first()

    payload = {
        "field_id": str(field.id),
        "action": "APPROVE",
        "comments": "Looks good",
        "expected_version": 1,
    }

    first = client.post(f"/api/v1/documents/{document.id}/fields/{field.id}/review", json=payload)
    assert first.status_code == 200
    assert first.json()["version"] == 2

    stale = client.post(f"/api/v1/documents/{document.id}/fields/{field.id}/review", json=payload)
    assert stale.status_code == 409
    assert stale.json()["error"] == "STALE_DATA"
    assert stale.json()["current_version"] == 2

    status_response = client.get(f"/api/v1/documents/{document.id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["extracted_fields"][0]["version"] == 2

    resubmitted = client.post(
        f"/api/v1/documents/{document.id}/fields/{field.id}/review",
        json={**payload, "expected_version": 2},
    )
    assert resubmitted.status_code == 200
    assert resubmitted.json()["version"] == 3


def test_sequential_reviews_version_increment(client, concurrency_session, reviewer_user, monkeypatch):
    _install_field_review_service(monkeypatch, concurrency_session, reviewer_user)
    document = concurrency_session.query(Document).first()
    field = concurrency_session.query(ExtractedField).first()

    first = client.post(
        f"/api/v1/documents/{document.id}/fields/{field.id}/review",
        json={"field_id": str(field.id), "action": "APPROVE", "expected_version": 1},
    )
    second = client.post(
        f"/api/v1/documents/{document.id}/fields/{field.id}/review",
        json={"field_id": str(field.id), "action": "APPROVE", "expected_version": 2},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["version"] == 2
    assert second.json()["version"] == 3


def test_stale_version_error_response(client, concurrency_session, reviewer_user, monkeypatch):
    _install_field_review_service(monkeypatch, concurrency_session, reviewer_user)
    document = concurrency_session.query(Document).first()
    field = concurrency_session.query(ExtractedField).first()

    response = client.post(
        f"/api/v1/documents/{document.id}/fields/{field.id}/review",
        json={"field_id": str(field.id), "action": "APPROVE", "expected_version": 99},
    )

    assert response.status_code == 409
    body = response.json()
    assert body["error"] == "STALE_DATA"
    assert body["message"] == "Field was modified by another reviewer"
    assert body["current_version"] == 1
    assert "details" in body


def test_concurrent_action_plan_review(client, concurrency_session, reviewer_user, monkeypatch):
    _install_action_plan_review_service(monkeypatch, concurrency_session, reviewer_user)
    document = concurrency_session.query(Document).first()
    item = concurrency_session.query(ActionPlanItem).first()

    payload = {
        "action": "APPROVE",
        "expected_version": 1,
    }

    first = client.post(f"/api/v1/action-items/{item.id}/review", json=payload)
    assert first.status_code == 200
    assert first.json()["version"] == 2

    stale = client.post(f"/api/v1/action-items/{item.id}/review", json=payload)
    assert stale.status_code == 409
    assert stale.json()["error"] == "STALE_DATA"

    resubmitted = client.post(
        f"/api/v1/action-items/{item.id}/review",
        json={"action": "APPROVE", "expected_version": 2},
    )
    assert resubmitted.status_code == 200
    assert resubmitted.json()["version"] == 3
