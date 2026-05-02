from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.core.logging import get_logger, request_id_var
from app.models.domain.models import ActionPlanItem, AuditLog, ExtractedField
from app.models.enums import AuditEventType, VerificationStatus
from app.models.schemas.requests import ActionPlanDecision, HumanReviewAction

logger = get_logger(__name__)


class ReviewService:
    def review_field(
        self,
        db: Session,
        field_id: uuid.UUID,
        action: HumanReviewAction,
        edited_value: str | None,
        comments: str | None,
        expected_version: int,
        reviewer_id: uuid.UUID,
        edit_reason: str | None = None,
    ) -> ExtractedField:
        field = db.query(ExtractedField).filter(ExtractedField.id == field_id).first()
        if not field:
            raise LookupError("Extracted field not found")

        logger.info_context(
            "Review field attempt",
            field_id=str(field_id),
            current_version=field.version,
            expected_version=expected_version,
            request_id=request_id_var.get(),
        )

        if field.version != expected_version:
            raise StaleDataError(
                f"Field was modified by another reviewer. Expected version {expected_version}, current version {field.version}. Reload to see latest changes."
            )

        before = {
            "verification_status": field.verification_status.value if field.verification_status else None,
            "value": field.value,
            "normalized_value": field.normalized_value,
            "reviewer_comments": field.reviewer_comments,
            "verified_by_user_id": str(field.verified_by_user_id) if field.verified_by_user_id else None,
            "verified_at": field.verified_at.isoformat() if field.verified_at else None,
            "version": field.version,
        }

        after_value = field.value
        after_normalized_value = field.normalized_value
        after_status = field.verification_status
        if action == HumanReviewAction.APPROVE:
            after_status = VerificationStatus.APPROVED
        elif action == HumanReviewAction.EDIT:
            after_status = VerificationStatus.EDITED
            after_value = edited_value or field.value
            after_normalized_value = edited_value or field.normalized_value
        elif action == HumanReviewAction.REJECT:
            after_status = VerificationStatus.REJECTED
        else:
            raise ValueError("Invalid review action")

        after = {
            "verification_status": after_status.value,
            "value": after_value,
            "normalized_value": after_normalized_value,
            "reviewer_comments": comments,
            "verified_by_user_id": str(reviewer_id),
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "version": expected_version + 1,
        }

        edit_history = list(field.edit_history or [])
        if action == HumanReviewAction.EDIT:
            edit_history.append(
                {
                    "edited_at": datetime.now(timezone.utc).isoformat(),
                    "edited_by": str(reviewer_id),
                    "previous_value": field.value,
                    "edited_value": edited_value,
                    "edit_reason": edit_reason,
                }
            )

        update_stmt = text(
            """
            UPDATE extracted_fields
            SET verification_status = :verification_status,
                value = :value,
                normalized_value = :normalized_value,
                version = version + 1,
                verified_by_user_id = :verified_by_user_id,
                verified_at = :verified_at,
                reviewer_comments = :reviewer_comments,
                edit_history = :edit_history,
                updated_at = :updated_at
            WHERE id = :id AND version = :expected_version
            """
        )

        try:
            result = db.execute(
                update_stmt,
                {
                    "id": field.id,
                    "verification_status": after_status.value,
                    "value": after_value,
                    "normalized_value": after_normalized_value,
                    "verified_by_user_id": reviewer_id,
                    "verified_at": datetime.now(timezone.utc),
                    "reviewer_comments": comments,
                    "edit_history": edit_history,
                    "updated_at": datetime.now(timezone.utc),
                    "expected_version": expected_version,
                },
            )
            if result.rowcount == 0:
                raise StaleDataError(
                    f"Field was modified by another reviewer. Expected version {expected_version}, current version {field.version}. Reload to see latest changes."
                )

            audit_event = {
                "before": before,
                "after": after,
                "reason": edit_reason or comments,
            }
            db.add(
                AuditLog(
                    id=uuid.uuid4(),
                    event_type={
                        HumanReviewAction.APPROVE: AuditEventType.FIELD_VERIFIED,
                        HumanReviewAction.EDIT: AuditEventType.FIELD_EDITED,
                        HumanReviewAction.REJECT: AuditEventType.FIELD_REJECTED,
                    }[action],
                    user_id=reviewer_id,
                    document_id=field.document_id,
                    entity_type="ExtractedField",
                    entity_id=field.id,
                    action=f"review_field:{action.value.lower()}",
                    changes=audit_event,
                    request_id=request_id_var.get(),
                )
            )
            db.commit()
            db.refresh(field)
            return field
        except Exception:
            db.rollback()
            raise

    def review_action_plan_item(
        self,
        db: Session,
        item_id: uuid.UUID,
        action: ActionPlanDecision,
        modifications: dict[str, Any] | None,
        comments: str | None,
        expected_version: int,
        reviewer_id: uuid.UUID,
    ) -> ActionPlanItem:
        item = db.query(ActionPlanItem).filter(ActionPlanItem.id == item_id).first()
        if not item:
            raise LookupError("Action plan item not found")

        logger.info_context(
            "Review action plan item attempt",
            item_id=str(item_id),
            current_version=item.version,
            expected_version=expected_version,
            request_id=request_id_var.get(),
        )

        if item.version != expected_version:
            raise StaleDataError(
                f"Field was modified by another reviewer. Expected version {expected_version}, current version {item.version}. Reload to see latest changes."
            )

        before = {
            "verification_status": item.verification_status.value if item.verification_status else None,
            "title": item.title,
            "description": item.description,
            "priority": item.priority.value if item.priority else None,
            "due_date": item.due_date.isoformat() if item.due_date else None,
            "responsible_officer": item.responsible_officer,
            "risk_if_ignored": item.risk_if_ignored,
            "suggested_next_step": item.suggested_next_step,
            "notes": item.notes,
            "version": item.version,
        }

        if action == ActionPlanDecision.APPROVE:
            after_status = VerificationStatus.APPROVED
            modified_values: dict[str, Any] = {}
        elif action == ActionPlanDecision.MODIFY:
            after_status = VerificationStatus.MODIFIED
            modified_values = modifications or {}
        elif action == ActionPlanDecision.REJECT:
            after_status = VerificationStatus.REJECTED
            modified_values = {}
        else:
            raise ValueError("Invalid review action")

        update_values = {
            "verification_status": after_status.value,
            "verified_by_user_id": reviewer_id,
            "verification_date": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "expected_version": expected_version,
        }

        if action == ActionPlanDecision.MODIFY:
            update_values.update(
                {
                    "title": modified_values.get("title", item.title),
                    "description": modified_values.get("description", item.description),
                    "priority": modified_values.get("priority", item.priority),
                    "due_date": modified_values.get("due_date", item.due_date),
                    "responsible_officer": modified_values.get("responsible_officer", item.responsible_officer),
                    "risk_if_ignored": modified_values.get("risk_if_ignored", item.risk_if_ignored),
                    "suggested_next_step": modified_values.get("suggested_next_step", item.suggested_next_step),
                    "notes": modified_values.get("notes", item.notes),
                }
            )

        after = dict(before)
        after.update(
            {
                "verification_status": after_status.value,
                "version": expected_version + 1,
            }
        )
        after.update({key: value for key, value in update_values.items() if key not in {"expected_version", "verification_status", "verified_by_user_id", "verification_date", "updated_at"}})

        update_stmt = text(
            """
            UPDATE action_plan_items
            SET verification_status = :verification_status,
                title = :title,
                description = :description,
                priority = :priority,
                due_date = :due_date,
                responsible_officer = :responsible_officer,
                risk_if_ignored = :risk_if_ignored,
                suggested_next_step = :suggested_next_step,
                notes = :notes,
                version = version + 1,
                verified_by_user_id = :verified_by_user_id,
                verification_date = :verification_date,
                updated_at = :updated_at
            WHERE id = :id AND version = :expected_version
            """
        )

        try:
            result = db.execute(
                update_stmt,
                {
                    "id": item.id,
                    "verification_status": update_values["verification_status"],
                    "title": update_values.get("title", item.title),
                    "description": update_values.get("description", item.description),
                    "priority": update_values.get("priority", item.priority.value if item.priority else None),
                    "due_date": update_values.get("due_date", item.due_date),
                    "responsible_officer": update_values.get("responsible_officer", item.responsible_officer),
                    "risk_if_ignored": update_values.get("risk_if_ignored", item.risk_if_ignored),
                    "suggested_next_step": update_values.get("suggested_next_step", item.suggested_next_step),
                    "notes": update_values.get("notes", item.notes),
                    "verified_by_user_id": reviewer_id,
                    "verification_date": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "expected_version": expected_version,
                },
            )
            if result.rowcount == 0:
                raise StaleDataError(
                    f"Field was modified by another reviewer. Expected version {expected_version}, current version {item.version}. Reload to see latest changes."
                )

            db.add(
                AuditLog(
                    id=uuid.uuid4(),
                    event_type=AuditEventType.ACTION_PLAN_VERIFIED,
                    user_id=reviewer_id,
                    document_id=item.document_id,
                    entity_type="ActionPlanItem",
                    entity_id=item.id,
                    action=f"review_action_plan_item:{action.value.lower()}",
                    changes={"before": before, "after": after, "comments": comments},
                    request_id=request_id_var.get(),
                )
            )
            db.commit()
            db.refresh(item)
            return item
        except Exception:
            db.rollback()
            raise


review_service = ReviewService()
