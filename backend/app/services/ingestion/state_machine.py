from __future__ import annotations

from typing import Dict, List

from app.core.logging import get_logger, request_id_var
from app.models.enums import ProcessingStatus

logger = get_logger(__name__)


class InvalidStatusTransition(Exception):
    pass


ALLOWED_TRANSITIONS: Dict[ProcessingStatus, List[ProcessingStatus]] = {
    ProcessingStatus.UPLOADED: [ProcessingStatus.CLASSIFYING, ProcessingStatus.FAILED],
    ProcessingStatus.CLASSIFYING: [ProcessingStatus.EXTRACTING, ProcessingStatus.FAILED],
    ProcessingStatus.EXTRACTING: [ProcessingStatus.EXTRACTION_COMPLETE, ProcessingStatus.FAILED],
    ProcessingStatus.EXTRACTION_COMPLETE: [ProcessingStatus.PENDING_REVIEW],
    ProcessingStatus.PENDING_REVIEW: [ProcessingStatus.UNDER_REVIEW],
    ProcessingStatus.UNDER_REVIEW: [ProcessingStatus.VERIFIED, ProcessingStatus.REJECTED],
    ProcessingStatus.FAILED: [ProcessingStatus.CLASSIFYING],
}


def transition_validator(current_status: ProcessingStatus, new_status: ProcessingStatus) -> None:
    """Validate allowed transitions between processing statuses.

    Raises InvalidStatusTransition on invalid transitions.
    Always logs attempts, including rejected ones, and includes request_id in context.
    """
    allowed = ALLOWED_TRANSITIONS.get(current_status, [])

    # Log attempt
    request_id = request_id_var.get()
    logger.info_context(
        "Status transition attempt",
        current_status=current_status.value if current_status else None,
        new_status=new_status.value if new_status else None,
        allowed=[s.value for s in allowed],
        request_id=request_id,
    )

    if new_status not in allowed:
        msg = f"Cannot transition from {current_status} to {new_status}. Allowed transitions: {[s for s in allowed]}"
        logger.error_context("Invalid status transition", error=msg, request_id=request_id)
        raise InvalidStatusTransition(msg)
