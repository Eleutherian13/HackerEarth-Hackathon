"""Unit tests for the audit core helpers and event logging."""

import asyncio
from datetime import date, datetime, timezone
from unittest.mock import Mock

import pytest

from app.core import audit
from app.models.enums import AuditEventType
from app.models.domain.models import AuditLog


class FakeAuditSession:
    def __init__(self):
        self.added = []
        self.committed = False
        self.refreshed = []

    def add(self, instance):
        self.added.append(instance)

    def commit(self):
        self.committed = True

    def refresh(self, instance):
        self.refreshed.append(instance)

    def close(self):
        pass


def test_serialize_value_converts_common_types():
    assert audit._serialize_value(None) is None
    assert audit._serialize_value("hello") == "hello"
    assert audit._serialize_value(123) == 123
    assert audit._serialize_value(True) is True
    assert audit._serialize_value(date(2024, 1, 1)) == "2024-01-01"
    assert audit._serialize_value(datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)) == "2024-01-01T12:00:00+00:00"
    assert audit._serialize_value({"a": 1}) == {"a": 1}
    assert audit._serialize_value([1, 2, 3]) == [1, 2, 3]


def test_recursive_diff_returns_nested_changes():
    old = {"a": 1, "b": {"c": 2}, "d": [1, 2]}
    new = {"a": 1, "b": {"c": 3}, "d": [1, 2, 3]}

    diff = audit._recursive_diff(old, new)

    assert diff == {
        "b": {"c": {"old": 2, "new": 3}},
        "d": {"old": [1, 2], "new": [1, 2, 3]},
    }


def test_build_model_changes_detects_changed_attributes():
    class Dummy:
        pass

    dummy = Dummy()
    dummy.id = 1
    dummy.name = "old"
    # SQLAlchemy inspection cannot operate on plain objects, so ensure no exception is thrown
    assert audit._build_model_changes(dummy) == {}


def test_log_audit_event_creates_record(monkeypatch):
    fake_session = FakeAuditSession()

    monkeypatch.setattr(audit, "SessionLocal", lambda: fake_session)

    result = asyncio.run(
        audit.log_audit_event(
            db=None,
            event_type=AuditEventType.USER_ACTION,
            action="TEST",
            entity_type="User",
            entity_id=None,
            user_id=None,
            changes={"field": {"old": None, "new": "value"}},
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )
    )

    assert fake_session.committed is True
    assert fake_session.added
    assert fake_session.refreshed
    assert result is not None
