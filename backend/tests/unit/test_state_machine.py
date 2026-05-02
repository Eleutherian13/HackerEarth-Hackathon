from __future__ import annotations

import threading
import uuid

import pytest

from app.models.enums import ProcessingStatus, AuditEventType
from app.services.ingestion import state_machine
from sqlalchemy.orm import object_session as _object_session


def test_valid_transitions():
    # A few valid transitions should not raise
    state_machine.transition_validator(ProcessingStatus.UPLOADED, ProcessingStatus.CLASSIFYING)
    state_machine.transition_validator(ProcessingStatus.CLASSIFYING, ProcessingStatus.EXTRACTING)
    state_machine.transition_validator(ProcessingStatus.EXTRACTING, ProcessingStatus.EXTRACTION_COMPLETE)
    state_machine.transition_validator(ProcessingStatus.EXTRACTION_COMPLETE, ProcessingStatus.PENDING_REVIEW)
    state_machine.transition_validator(ProcessingStatus.PENDING_REVIEW, ProcessingStatus.UNDER_REVIEW)
    state_machine.transition_validator(ProcessingStatus.UNDER_REVIEW, ProcessingStatus.VERIFIED)
    state_machine.transition_validator(ProcessingStatus.FAILED, ProcessingStatus.CLASSIFYING)


def test_invalid_transition_uploaded_to_verified():
    with pytest.raises(state_machine.InvalidStatusTransition):
        state_machine.transition_validator(ProcessingStatus.UPLOADED, ProcessingStatus.VERIFIED)


def test_invalid_transition_extracting_to_verified():
    with pytest.raises(state_machine.InvalidStatusTransition):
        state_machine.transition_validator(ProcessingStatus.EXTRACTING, ProcessingStatus.VERIFIED)


def test_transition_with_none_status_raises_error():
    with pytest.raises(state_machine.InvalidStatusTransition):
        state_machine.transition_validator(None, ProcessingStatus.CLASSIFYING)


def test_transition_creates_audit_log(monkeypatch):
    # Create a fake document-like object
    class DummyDoc:
        def __init__(self):
            self.id = uuid.uuid4()
            self.processing_status = ProcessingStatus.UPLOADED
            self.updated_at = None

    created = []

    class FakeSession:
        def begin(self):
            class Ctx:
                def __enter__(self_):
                    return None

                def __exit__(self_, exc_type, exc, tb):
                    return False

            return Ctx()

        def add(self, obj):
            created.append(obj)

    dummy = DummyDoc()

    # Monkeypatch object_session to return our fake session
    monkeypatch.setattr("sqlalchemy.orm.object_session", lambda obj: FakeSession())

    # Call transition
    from app.models.domain.models import Document

    # Use the same attributes as Document.transition_to expects
    # We can't instantiate full Document easily here; we use the DummyDoc with same attr
    # Call the method by binding the function implementation
    Document.transition_to(dummy, ProcessingStatus.CLASSIFYING, updated_by=None, reason="test")

    # An AuditLog object should have been added to fake session
    assert any(getattr(obj, "action", None) == "status_transition" for obj in created)


def test_concurrent_transition_handling(monkeypatch):
    # Simulate two threads attempting conflicting transitions
    class DummyDoc:
        def __init__(self):
            self.id = uuid.uuid4()
            self.processing_status = ProcessingStatus.UPLOADED
            self.updated_at = None

    class FakeSession:
        lock = threading.Lock()

        def begin(self):
            class Ctx:
                def __enter__(_self):
                    FakeSession.lock.acquire()

                def __exit__(_self, exc_type, exc, tb):
                    FakeSession.lock.release()
                    return False

            return Ctx()

        def add(self, obj):
            pass

    dummy = DummyDoc()
    monkeypatch.setattr("sqlalchemy.orm.object_session", lambda obj: FakeSession())

    results = []

    def try_transition(target):
        try:
            from app.models.domain.models import Document

            Document.transition_to(dummy, target, updated_by=None, reason="concurrent")
            results.append((target, "ok"))
        except Exception as e:
            results.append((target, type(e)))

    t1 = threading.Thread(target=try_transition, args=(ProcessingStatus.CLASSIFYING,))
    t2 = threading.Thread(target=try_transition, args=(ProcessingStatus.VERIFIED,))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # One of the transitions should have failed due to invalid transition path
    assert any(r[1] == "ok" for r in results)
    assert any(r[1] != "ok" for r in results)
