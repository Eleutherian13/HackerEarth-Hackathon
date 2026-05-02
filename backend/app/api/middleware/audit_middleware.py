from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import FastAPI
from sqlalchemy import event, inspect as sa_inspect
from sqlalchemy.orm import Session

from app.core.audit import _build_model_changes, _serialize_value
from app.core.logging import request_id_var, user_id_var
from app.models.domain.models import AuditLog
from app.models.enums import AuditEventType
from app.db.session import SessionLocal

EXCLUDED_AUDIT_MODELS = {AuditLog}
EXCLUDED_FIELDS = {"hashed_password", "password", "secret", "token", "refresh_token"}


def _resolve_user_id() -> UUID | None:
    raw_user_id = user_id_var.get()
    if raw_user_id is None:
        return None
    try:
        return UUID(raw_user_id)
    except Exception:
        return None


def _build_audit_row(instance: Any, action: str) -> AuditLog | None:
    if type(instance) in EXCLUDED_AUDIT_MODELS:
        return None

    entity_type = type(instance).__name__
    entity_id = getattr(instance, "id", None)
    document_id = getattr(instance, "document_id", None)
    user_id = _resolve_user_id()
    request_id = request_id_var.get()
    changes = _build_model_changes(instance, excluded_fields=list(EXCLUDED_FIELDS))

    return AuditLog(
        event_type=AuditEventType.USER_ACTION,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        document_id=document_id,
        user_id=user_id,
        changes=changes or {},
        ip_address=None,
        user_agent=None,
        request_id=request_id,
    )


def _before_flush(session: Session, flush_context: Any, instances: Any) -> None:
    audit_entries: list[AuditLog] = []

    for instance in list(session.new):
        if type(instance) in EXCLUDED_AUDIT_MODELS:
            continue
        entry = _build_audit_row(instance, action="INSERT")
        if entry is not None:
            audit_entries.append(entry)

    for instance in list(session.dirty):
        if type(instance) in EXCLUDED_AUDIT_MODELS:
            continue
        state = sa_inspect(instance)
        if state.modified:
            entry = _build_audit_row(instance, action="UPDATE")
            if entry is not None and entry.changes:
                audit_entries.append(entry)

    for instance in list(session.deleted):
        if type(instance) in EXCLUDED_AUDIT_MODELS:
            continue
        entry = _build_audit_row(instance, action="DELETE")
        if entry is not None:
            audit_entries.append(entry)

    for audit_log in audit_entries:
        session.add(audit_log)


def _prevent_audit_modification(mapper: Any, connection: Any, target: Any) -> None:
    raise ValueError("Audit logs are immutable and cannot be updated or deleted.")


def configure_audit_middleware(app: FastAPI) -> None:
    event.listen(Session, "before_flush", _before_flush)
    event.listen(AuditLog, "before_update", _prevent_audit_modification)
    event.listen(AuditLog, "before_delete", _prevent_audit_modification)
