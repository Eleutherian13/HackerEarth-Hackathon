"""
Audit logging for compliance tracking and immutable audit trails.

Provides functions to log user actions, system events, and data changes
to the AuditLog table for compliance and forensic analysis.

Features:
- Immutable append-only audit log
- Captures who, what, when, old values, new values, IP address
- Integration with user sessions and request context
- Structured JSON storage of complex changes
- Correlation with documents and entities
"""

from __future__ import annotations

import asyncio
import inspect
import json
from collections.abc import Callable
from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.domain.models import AuditLog, User
from app.models.enums import AuditEventType

logger = get_logger(__name__)


def _serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    try:
        return str(value)
    except Exception:
        return None


def _recursive_diff(old: Any, new: Any) -> Any:
    if old == new:
        return None
    if isinstance(old, dict) and isinstance(new, dict):
        changes: dict[str, Any] = {}
        for key in sorted(set(old.keys()) | set(new.keys())):
            diff = _recursive_diff(old.get(key), new.get(key))
            if diff is not None:
                changes[key] = diff
        return changes or None
    if isinstance(old, list) and isinstance(new, list):
        if old == new:
            return None
        return {"old": _serialize_value(old), "new": _serialize_value(new)}
    return {"old": _serialize_value(old), "new": _serialize_value(new)}


def _build_model_changes(instance: Any, excluded_fields: list[str] | None = None) -> dict[str, Any]:
    excluded_fields = set(excluded_fields or [])
    changes: dict[str, Any] = {}

    try:
        state = sa_inspect(instance)
    except Exception:
        return {}

    for attr in getattr(state, "attrs", []):
        if attr.key in excluded_fields or attr.key == "changes":
            continue
        if not attr.history.has_changes():
            continue

        old_value = attr.history.deleted[0] if attr.history.deleted else None
        new_value = attr.history.added[0] if attr.history.added else getattr(instance, attr.key, None)
        diff = _recursive_diff(_serialize_value(old_value), _serialize_value(new_value))
        if diff is not None:
            changes[attr.key] = diff

    return changes


def _get_user_id_from_args(args: tuple[Any, ...], kwargs: dict[str, Any]) -> UUID | None:
    for candidate in ("user", "current_user", "user_id"):
        if candidate in kwargs and isinstance(kwargs[candidate], UUID):
            return kwargs[candidate]
        if candidate in kwargs and hasattr(kwargs[candidate], "id"):
            return getattr(kwargs[candidate], "id")
    for arg in args:
        if isinstance(arg, UUID):
            return arg
        if hasattr(arg, "id") and getattr(arg, "id") is not None:
            return getattr(arg, "id")
    return None


def _get_entity_info(result: Any, extract_entity: bool) -> tuple[str | None, UUID | None]:
    if not extract_entity or result is None:
        return None, None
    if hasattr(result, "__tablename__"):
        entity_type = type(result).__name__
        entity_id = getattr(result, "id", None)
        return entity_type, entity_id
    if isinstance(result, dict):
        return result.get("entity_type"), result.get("entity_id")
    return type(result).__name__, getattr(result, "id", None)


def _get_document_id(result: Any, kwargs: dict[str, Any]) -> UUID | None:
    if "document_id" in kwargs and isinstance(kwargs["document_id"], UUID):
        return kwargs["document_id"]
    if hasattr(result, "document_id"):
        return getattr(result, "document_id")
    if isinstance(result, dict):
        return result.get("document_id")
    return None


def _run_log_task(
    event_type: AuditEventType,
    action: str,
    entity_type: str,
    entity_id: UUID | None,
    document_id: UUID | None,
    user_id: UUID | None,
    changes: dict[str, Any] | None,
    ip_address: str | None,
    user_agent: str | None,
) -> None:
    with SessionLocal() as audit_db:
        audit_log = AuditLog(
            event_type=event_type,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            document_id=document_id,
            user_id=user_id,
            changes=changes or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        audit_db.add(audit_log)
        audit_db.commit()
        audit_db.refresh(audit_log)


def audit_event(
    event_type: AuditEventType,
    action: str | None = None,
    extract_entity: bool = False,
    excluded_fields: list[str] | None = None,
) -> Callable[[Callable], Callable]:
    def decorator(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                result = await func(*args, **kwargs)
                audit_action = action or func.__name__
                user_id = _get_user_id_from_args(args, kwargs)
                entity_type, entity_id = _get_entity_info(result, extract_entity)
                document_id = _get_document_id(result, kwargs)
                changes = None
                if hasattr(result, "__tablename__"):
                    changes = _build_model_changes(result, excluded_fields=excluded_fields)
                elif "changes" in kwargs:
                    changes = kwargs.get("changes")

                asyncio.create_task(
                    asyncio.to_thread(
                        _run_log_task,
                        event_type,
                        audit_action,
                        entity_type or "Unknown",
                        entity_id,
                        document_id,
                        user_id,
                        changes,
                        kwargs.get("ip_address"),
                        kwargs.get("user_agent"),
                    )
                )
                return result

            return async_wrapper

        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            audit_action = action or func.__name__
            user_id = _get_user_id_from_args(args, kwargs)
            entity_type, entity_id = _get_entity_info(result, extract_entity)
            document_id = _get_document_id(result, kwargs)
            changes = None
            if hasattr(result, "__tablename__"):
                changes = _build_model_changes(result, excluded_fields=excluded_fields)
            elif "changes" in kwargs:
                changes = kwargs.get("changes")

            if user_id is not None:
                _run_log_task(
                    event_type,
                    audit_action,
                    entity_type or "Unknown",
                    entity_id,
                    document_id,
                    user_id,
                    changes,
                    kwargs.get("ip_address"),
                    kwargs.get("user_agent"),
                )
            return result

        return sync_wrapper

    return decorator


async def log_audit_event(
    db: Session | None,
    event_type: AuditEventType,
    action: str,
    entity_type: str,
    entity_id: UUID | None = None,
    document_id: UUID | None = None,
    user_id: UUID | None = None,
    changes: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog | None:
    """
    Log an audit event to the database.

    Args:
        db: Optional database session. If None, a dedicated audit session is created.
        event_type: Type of audit event
        action: Specific action taken (e.g., "CREATE", "UPDATE", "DELETE", "VERIFY")
        entity_type: Type of entity being audited (e.g., "User", "Document", "ExtractedField")
        entity_id: UUID of the entity
        document_id: UUID of related document (if applicable)
        user_id: UUID of user performing action
        changes: Dictionary of field changes {field: {old: value, new: value}}
        ip_address: IP address of requester
        user_agent: User agent string

    Returns:
        Created AuditLog record or None on error
    """
    def _persist() -> AuditLog | None:
        session = db if db is not None else SessionLocal()
        should_close = db is None
        try:
            audit_log = AuditLog(
                event_type=event_type,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                document_id=document_id,
                user_id=user_id,
                changes=changes or {},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            session.add(audit_log)
            session.commit()
            session.refresh(audit_log)
            logger.info_context(
                f"Audit event logged: {event_type.value}/{action}",
                event_type=event_type.value,
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id else None,
                document_id=str(document_id) if document_id else None,
                user_id=str(user_id) if user_id else None,
            )
            return audit_log
        except Exception:
            logger.error_context(
                f"Failed to log audit event: {event_type.value}",
                event_type=event_type.value,
                action=action,
                entity_type=entity_type,
                exc_info=True,
            )
            return None
        finally:
            if should_close:
                session.close()

    return await asyncio.to_thread(_persist)


async def log_user_login(
    db: Session,
    user_id: UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog | None:
    """Log user login event."""
    return await log_audit_event(
        db,
        event_type=AuditEventType.USER_LOGIN,
        action="LOGIN",
        entity_type="User",
        entity_id=user_id,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_user_logout(
    db: Session,
    user_id: UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog | None:
    """Log user logout event."""
    return await log_audit_event(
        db,
        event_type=AuditEventType.USER_ACTION,
        action="LOGOUT",
        entity_type="User",
        entity_id=user_id,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_document_upload(
    db: Session,
    document_id: UUID,
    user_id: UUID,
    changes: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog | None:
    """Log document upload event."""
    return await log_audit_event(
        db,
        event_type=AuditEventType.DOCUMENT_UPLOADED,
        action="UPLOAD",
        entity_type="Document",
        entity_id=document_id,
        document_id=document_id,
        user_id=user_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_field_extracted(
    db: Session,
    field_id: UUID,
    document_id: UUID,
    changes: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog | None:
    """Log field extraction event."""
    return await log_audit_event(
        db,
        event_type=AuditEventType.FIELD_EXTRACTED,
        action="EXTRACT",
        entity_type="ExtractedField",
        entity_id=field_id,
        document_id=document_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_field_verified(
    db: Session,
    field_id: UUID,
    document_id: UUID,
    user_id: UUID,
    changes: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog | None:
    """Log field verification event."""
    return await log_audit_event(
        db,
        event_type=AuditEventType.FIELD_VERIFIED,
        action="VERIFY",
        entity_type="ExtractedField",
        entity_id=field_id,
        document_id=document_id,
        user_id=user_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_field_edited(
    db: Session,
    field_id: UUID,
    document_id: UUID,
    user_id: UUID,
    old_value: str | None = None,
    new_value: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog | None:
    """Log field edit event."""
    changes = None
    if old_value is not None or new_value is not None:
        changes = {
            "value": {"old": old_value, "new": new_value}
        }

    return await log_audit_event(
        db,
        event_type=AuditEventType.FIELD_EDITED,
        action="EDIT",
        entity_type="ExtractedField",
        entity_id=field_id,
        document_id=document_id,
        user_id=user_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_field_rejected(
    db: Session,
    field_id: UUID,
    document_id: UUID,
    user_id: UUID,
    reason: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog | None:
    """Log field rejection event."""
    changes = None
    if reason:
        changes = {"rejection_reason": reason}

    return await log_audit_event(
        db,
        event_type=AuditEventType.FIELD_REJECTED,
        action="REJECT",
        entity_type="ExtractedField",
        entity_id=field_id,
        document_id=document_id,
        user_id=user_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_action_plan_generated(
    db: Session,
    document_id: UUID,
    item_count: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog | None:
    """Log action plan generation event."""
    changes = None
    if item_count is not None:
        changes = {"item_count": item_count}

    return await log_audit_event(
        db,
        event_type=AuditEventType.ACTION_PLAN_GENERATED,
        action="GENERATE",
        entity_type="ActionPlan",
        document_id=document_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_action_plan_verified(
    db: Session,
    document_id: UUID,
    user_id: UUID,
    verified_count: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog | None:
    """Log action plan verification event."""
    changes = None
    if verified_count is not None:
        changes = {"verified_items": verified_count}

    return await log_audit_event(
        db,
        event_type=AuditEventType.ACTION_PLAN_VERIFIED,
        action="VERIFY",
        entity_type="ActionPlan",
        document_id=document_id,
        user_id=user_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_system_error(
    db: Session,
    error_type: str,
    error_message: str,
    document_id: UUID | None = None,
    user_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog | None:
    """Log system error event."""
    changes = {
        "error_type": error_type,
        "error_message": error_message,
    }

    return await log_audit_event(
        db,
        event_type=AuditEventType.SYSTEM_ERROR,
        action="ERROR",
        entity_type="System",
        document_id=document_id,
        user_id=user_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def get_audit_trail(
    db: Session,
    document_id: UUID | None = None,
    user_id: UUID | None = None,
    entity_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """
    Query audit trail with optional filters.

    Args:
        db: Database session
        document_id: Filter by document
        user_id: Filter by user
        entity_type: Filter by entity type
        limit: Maximum records to return
        offset: Pagination offset

    Returns:
        List of AuditLog records
    """
    query = db.query(AuditLog)

    if document_id:
        query = query.filter(AuditLog.document_id == document_id)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
