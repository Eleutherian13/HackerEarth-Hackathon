"""
Document management endpoints.

Handles:
- PDF document upload with validation and deduplication
- Document metadata retrieval
- Processing status tracking
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.api.deps import get_current_active_user, get_db
from app.core.validators import InputValidator
from app.core.audit import log_document_upload
from app.core.logging import get_logger
from app.models.domain.models import Document, DocumentPage, ExtractedField, User
from app.models.enums import ProcessingStatus, VerificationStatus
from app.models.schemas.requests import DocumentUploadRequest, HumanReviewSubmitRequest, HumanReviewAction
from app.models.schemas.responses import DocumentResponse, ExtractedFieldResponse
from app.api.v1.endpoints.review import build_stale_review_response
from app.services.ingestion.storage import get_storage_backend
from app.services.verification import review_service
from app.services.ingestion.upload_handler import (
    PDFAlreadyExistsError,
    PDFValidationError,
    UploadHandler,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


def _processing_stage_label(status: ProcessingStatus) -> str:
    return {
        ProcessingStatus.UPLOADED: "Uploaded",
        ProcessingStatus.CLASSIFYING: "Classifying",
        ProcessingStatus.EXTRACTING: "Extracting",
        ProcessingStatus.EXTRACTION_COMPLETE: "Extraction complete",
        ProcessingStatus.PENDING_REVIEW: "Pending review",
        ProcessingStatus.UNDER_REVIEW: "Under review",
        ProcessingStatus.VERIFIED: "Verified",
        ProcessingStatus.REJECTED: "Rejected",
        ProcessingStatus.FAILED: "Failed",
    }[status]


def _status_color(status: ProcessingStatus) -> str:
    return {
        ProcessingStatus.UPLOADED: "info",
        ProcessingStatus.CLASSIFYING: "warning",
        ProcessingStatus.EXTRACTING: "warning",
        ProcessingStatus.EXTRACTION_COMPLETE: "warning",
        ProcessingStatus.PENDING_REVIEW: "secondary",
        ProcessingStatus.UNDER_REVIEW: "secondary",
        ProcessingStatus.VERIFIED: "success",
        ProcessingStatus.REJECTED: "error",
        ProcessingStatus.FAILED: "error",
    }[status]


def _processing_progress(status: ProcessingStatus, pages_processed: int, page_count: int | None) -> int:
    if status == ProcessingStatus.EXTRACTING and page_count:
        page_progress = int((pages_processed / max(page_count, 1)) * 60)
        return min(85, 35 + page_progress)

    return {
        ProcessingStatus.UPLOADED: 5,
        ProcessingStatus.CLASSIFYING: 15,
        ProcessingStatus.EXTRACTING: 35,
        ProcessingStatus.EXTRACTION_COMPLETE: 80,
        ProcessingStatus.PENDING_REVIEW: 90,
        ProcessingStatus.UNDER_REVIEW: 95,
        ProcessingStatus.VERIFIED: 100,
        ProcessingStatus.REJECTED: 100,
        ProcessingStatus.FAILED: min(95, 10 + pages_processed * 10),
    }[status]


def _current_stage(status: ProcessingStatus) -> str:
    return _processing_stage_label(status)


def _build_processing_log(document: Document, jobs: list[ProcessingJob], pages: list[DocumentPage]) -> list[dict[str, Any]]:
    log_entries: list[dict[str, Any]] = [
        {
            "stage": "UPLOAD",
            "status": ProcessingStatus.UPLOADED.value,
            "message": "Document uploaded",
            "timestamp": document.created_at.isoformat(),
        }
    ]

    for job in sorted(jobs, key=lambda item: item.created_at):
        log_entries.append(
            {
                "stage": job.job_type.value,
                "status": job.status.value,
                "message": job.error_message or f"{job.job_type.value.title()} job {job.status.value.lower()}",
                "timestamp": (job.started_at or job.created_at).isoformat(),
                "retry_count": job.retry_count,
            }
        )
        if job.completed_at:
            log_entries.append(
                {
                    "stage": job.job_type.value,
                    "status": job.status.value,
                    "message": f"{job.job_type.value.title()} job completed",
                    "timestamp": job.completed_at.isoformat(),
                    "retry_count": job.retry_count,
                }
            )

    for page in pages:
        page_text = page.raw_text or page.ocr_text or ""
        log_entries.append(
            {
                "stage": "EXTRACTION",
                "status": ProcessingStatus.EXTRACTION_COMPLETE.value if page_text else ProcessingStatus.EXTRACTING.value,
                "message": f"Page {page.page_number} processed",
                "timestamp": page.created_at.isoformat(),
                "page_number": page.page_number,
                "confidence": page.extraction_confidence,
            }
        )

    log_entries.sort(key=lambda item: item["timestamp"])
    return log_entries


def _build_page_previews(pages: list[DocumentPage]) -> tuple[list[dict[str, Any]], list[int]]:
    previews: list[dict[str, Any]] = []
    low_confidence_pages: list[int] = []

    for page in pages:
        page_text = page.raw_text or page.ocr_text or ""
        confidence = float(page.extraction_confidence or 0.0)
        if confidence < 0.75:
            low_confidence_pages.append(page.page_number)
        previews.append(
            {
                "page_number": page.page_number,
                "preview_text": (page_text[:240] + "...") if len(page_text) > 240 else page_text,
                "confidence": confidence,
                "is_low_confidence": confidence < 0.75,
                "has_text": bool(page.raw_text),
                "has_ocr": bool(page.ocr_text),
            }
        )

    return previews, low_confidence_pages


def _estimated_remaining_seconds(document: Document, page_count: int | None, pages_processed: int) -> int | None:
    if not page_count or pages_processed <= 0:
        return None

    elapsed_seconds = max((datetime.utcnow() - document.created_at).total_seconds(), 0)
    average_seconds_per_page = elapsed_seconds / max(pages_processed, 1)
    remaining = int(max(page_count - pages_processed, 0) * average_seconds_per_page)
    return remaining if remaining > 0 else None


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload PDF Document",
    description="Upload and validate PDF document. Returns 202 Accepted with processing status URL.",
)
async def upload_document(
    request: Request,
    file: bytes = File(..., description="PDF file to upload"),
    metadata_json: str = Form(default="{}", description="Optional JSON metadata"),
    force: bool = Form(default=False, description="Force reprocess if duplicate (admin only)"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DocumentResponse:
    """
    Upload and validate a PDF document.

    **Request:**
    - `file`: PDF file (multipart/form-data)
    - `metadata_json`: Optional JSON string with metadata (default: "{}")
    - `force`: Force reprocess if duplicate (admin only, default: false)

    **Response:** 202 Accepted with document details and status URL

    **Validations:**
    - File must be valid PDF (magic bytes)
    - File must not be corrupted
    - File must be ≤ 50MB
    - PDF must not be password protected
    - Detects duplicate PDFs by SHA-256 hash

    **On Success:**
    - Creates Document record with status UPLOADED
    - Stores file to configured backend (local or S3)
    - Enqueues classification job
    - Returns processing status URL

    **On Duplicate:**
    - Returns 409 Conflict if identical PDF already exists
    - Unless ?force=true (admin only)

    **Errors:**
    - 400: Invalid PDF or metadata
    - 409: Duplicate document
    - 413: File too large
    - 422: Invalid metadata JSON
    - 500: Storage error
    """
    try:
        # Validate file size first (before parsing)
        file_size = len(file)
        if not InputValidator.validate_file_size(file_size, max_mb=50):
            logger.warning_context(
                "Upload rejected: file size exceeds limit",
                file_size=file_size,
                max_size=50 * 1024 * 1024,
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size {file_size} bytes exceeds maximum of 50MB",
            )
        
        # Parse metadata
        try:
            import json

            if isinstance(metadata_json, str):
                metadata = json.loads(metadata_json)
            else:
                metadata = metadata_json or {}
        except json.JSONDecodeError as e:
            logger.warning_context("Invalid metadata JSON", error=str(e))
            raise HTTPException(status_code=400, detail="Invalid metadata JSON")

        # Validate PDF
        try:
            page_count, is_encrypted, file_hash = UploadHandler.validate_pdf(file)
        except PDFValidationError as e:
            logger.warning_context("PDF validation failed", error=str(e))
            raise HTTPException(status_code=400, detail=str(e))

        # Check for duplicates
        existing_doc = UploadHandler.check_duplicate(db, file_hash)
        if existing_doc and not force:
            logger.info_context(
                "Duplicate document upload rejected",
                existing_document_id=str(existing_doc.id),
            )
            raise HTTPException(
                status_code=409,
                detail=f"Document with same content already exists: {existing_doc.id}",
            )

        # If duplicate and force=True, check admin permission
        if existing_doc and force:
            # In production, check if user has ADMIN or SUPERADMIN role
            logger.info_context(
                "Duplicate document reprocessing forced",
                existing_document_id=str(existing_doc.id),
                user_id=str(current_user.id),
            )

        # Generate document ID
        document_id = uuid.uuid4()

        # Generate storage path: documents/{uuid}/{filename}
        filename = "document.pdf"
        if hasattr(file, "filename") and file.filename:
            filename = file.filename
        elif request.headers.get("x-filename"):
            filename = request.headers.get("x-filename")
        
        # Validate filename (prevent path traversal, check length)
        if not InputValidator.validate_filename(filename, max_length=500):
            logger.warning_context(
                "Upload rejected: invalid filename",
                filename=filename,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename. Filename must not contain path traversal sequences (.., /, \\) and must be < 500 characters",
            )

        storage_path = f"documents/{document_id}/{filename}"

        # Upload to storage backend
        try:
            storage_backend = get_storage_backend()
            await storage_backend.upload(file, storage_path)
        except Exception as e:
            logger.error_context(
                "Storage upload failed",
                storage_path=storage_path,
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to store document",
            )

        # Create Document record
        try:
            document = UploadHandler.create_document_record(
                db=db,
                document_id=document_id,
                file_hash=file_hash,
                original_filename=filename,
                storage_path=storage_path,
                mime_type="application/pdf",
                file_size_bytes=len(file),
                page_count=page_count,
                uploaded_by_user_id=current_user.id,
                metadata=metadata,
            )
        except Exception as e:
            logger.error_context(
                "Failed to create document record",
                document_id=str(document_id),
                exc_info=True,
            )
            # Clean up uploaded file
            try:
                await storage_backend.delete(storage_path)
            except Exception:
                pass
            raise HTTPException(
                status_code=500,
                detail="Failed to create document record",
            )

        # Log audit event
        try:
            await log_document_upload(
                db=db,
                document_id=document.id,
                user_id=current_user.id,
                changes={
                    "filename": filename,
                    "size_bytes": len(file),
                    "page_count": page_count,
                    "hash": file_hash[:16],
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        except Exception as e:
            logger.error_context("Failed to log audit event", exc_info=True)

        # Enqueue background job for classification and extraction.
        try:
            from app.worker.tasks import process_document

            document.processing_status = ProcessingStatus.CLASSIFYING
            document.updated_at = datetime.utcnow()
            db.commit()
            process_document.delay(str(document.id))
        except Exception:
            logger.error_context(
                "Failed to enqueue document processing",
                document_id=str(document.id),
                exc_info=True,
            )
            document.processing_status = ProcessingStatus.FAILED
            document.error_message = "Failed to enqueue processing job"
            document.updated_at = datetime.utcnow()
            db.commit()

        logger.info_context(
            "Document uploaded successfully",
            document_id=str(document.id),
            page_count=page_count,
            file_size=len(file),
        )

        return DocumentResponse.model_validate(document)

    except HTTPException:
        raise
    except Exception as e:
        logger.error_context(
            "Unexpected error during document upload",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Unexpected server error during upload",
        )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get Document",
    description="Retrieve document details by ID.",
)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DocumentResponse:
    """
    Get document details by ID.

    Args:
        document_id: Document UUID

    Returns:
        Document details including processing status
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    document = db.query(Document).filter(Document.id == doc_uuid).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    logger.info_context("Document retrieved", document_id=str(document.id))

    return DocumentResponse.model_validate(document)


@router.get(
    "/{document_id}/status",
    summary="Get Document Processing Status",
    description="Get current processing status of document with all related data.",
)
async def get_document_status(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """
    Get comprehensive document processing status.

    Returns detailed status including:
    - Document metadata and processing status
    - Processing jobs and their status
    - Extracted fields with verification status
    - Action plan items with completion status
    - Audit trail
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    from app.models.domain.models import ActionPlanItem, ExtractedField, ProcessingJob

    document = db.query(Document).filter(Document.id == doc_uuid).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get processing jobs
    jobs = db.query(ProcessingJob).filter(ProcessingJob.document_id == doc_uuid).all()

    # Get extracted pages and fields
    pages = db.query(DocumentPage).filter(DocumentPage.document_id == doc_uuid).order_by(DocumentPage.page_number).all()
    fields = db.query(ExtractedField).filter(ExtractedField.document_id == doc_uuid).all()

    # Get action plan items
    action_items = db.query(ActionPlanItem).filter(ActionPlanItem.document_id == doc_uuid).all()

    pages_processed = sum(1 for page in pages if (page.raw_text or page.ocr_text))
    page_previews, low_confidence_pages = _build_page_previews(pages)
    processing_log = _build_processing_log(document, jobs, pages)
    latest_job = max(jobs, key=lambda item: item.updated_at or item.created_at, default=None)

    response = {
        "document": {
            "id": str(document.id),
            "filename": document.original_filename,
            "status": document.processing_status.value,
            "status_label": _processing_stage_label(document.processing_status),
            "status_color": _status_color(document.processing_status),
            "error_message": document.error_message,
            "page_count": document.page_count,
            "file_size_mb": document.file_size_bytes / (1024 * 1024),
            "is_text_based": document.is_text_based,
            "metadata": document.metadata_json or {},
            "uploaded_by_user_id": str(document.uploaded_by_user_id),
            "uploaded_by_department": document.uploaded_by_user.department.name if document.uploaded_by_user and document.uploaded_by_user.department else None,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
        },
        "progress_percentage": _processing_progress(document.processing_status, pages_processed, document.page_count),
        "current_stage": _current_stage(document.processing_status),
        "estimated_time_remaining_seconds": _estimated_remaining_seconds(document, document.page_count, pages_processed),
        "processing_log": processing_log,
        "page_previews": page_previews,
        "low_confidence_pages": low_confidence_pages,
        "can_retry": document.processing_status == ProcessingStatus.FAILED,
        "retry_endpoint": f"/api/v1/documents/{document.id}/retry-processing" if document.processing_status == ProcessingStatus.FAILED else None,
        "retry_count": latest_job.retry_count if latest_job else 0,
        "processing_jobs": [
            {
                "id": str(job.id),
                "type": job.job_type.value,
                "status": job.status.value,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message,
                "retry_count": job.retry_count,
                "created_at": job.created_at.isoformat(),
            }
            for job in jobs
        ],
        "extracted_fields": [
            {
                "id": str(field.id),
                "field_type": field.field_type.value,
                "value": field.value,
                "normalized_value": field.normalized_value,
                "confidence_score": float(field.confidence_score),
                "extraction_method": field.extraction_method.value,
                "verification_status": field.verification_status.value,
                "version": field.version,
                "is_inferred": field.is_inferred,
                "inference_rationale": field.inference_rationale,
                "source_page_ids": field.source_page_ids,
                "source_quotes": field.source_quotes,
                "reviewer_comments": field.reviewer_comments,
                "verified_by_user_id": str(field.verified_by_user_id) if field.verified_by_user_id else None,
                "verified_at": field.verified_at.isoformat() if field.verified_at else None,
            }
            for field in fields
        ],
        "action_plan_items": [
            {
                "id": str(item.id),
                "title": item.title,
                "type": item.item_type.value,
                "priority": item.priority.value,
                "due_date": item.due_date.isoformat() if item.due_date else None,
                "completion_status": item.completion_status.value,
                "verification_status": item.verification_status.value,
                "version": item.version,
                "description": item.description,
            }
            for item in action_items
        ],
        "summary": {
            "total_fields_extracted": len(fields),
            "fields_verified": sum(1 for f in fields if f.verification_status.value == "VERIFIED"),
            "total_action_items": len(action_items),
            "action_items_completed": sum(1 for a in action_items if a.completion_status.value == "COMPLETED"),
            "action_items_pending": sum(1 for a in action_items if a.completion_status.value == "PENDING"),
        },
    }

    return response


@router.post(
    "/{document_id}/fields/{field_id}/review",
    response_model=ExtractedFieldResponse,
    summary="Review an extracted field",
    description="Approve, edit, or reject a specific extracted field during human review.",
)
async def review_extracted_field(
    document_id: str,
    field_id: str,
    review_request: HumanReviewSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ExtractedFieldResponse:
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    try:
        field_uuid = uuid.UUID(field_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid field ID format")
    
    # Validate review request inputs
    if review_request.expected_version is not None and review_request.expected_version < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="expected_version must be a positive integer",
        )
    
    # Validate comments don't contain XSS
    if review_request.comments:
        if not InputValidator.validate_no_html_script(review_request.comments):
            logger.warning_context(
                "Review submission blocked: XSS detected in comments",
                field_id=str(field_uuid),
                user_id=str(current_user.id),
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Comments contain invalid HTML or script content",
            )
        
        # Validate comments length
        if not InputValidator.validate_text_length(review_request.comments, max_length=2000):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Comments must not exceed 2000 characters",
            )

    document = db.query(Document).filter(Document.id == doc_uuid).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    field = db.query(ExtractedField).filter(
        ExtractedField.id == field_uuid,
        ExtractedField.document_id == doc_uuid,
    ).first()

    if not field:
        raise HTTPException(status_code=404, detail="Extracted field not found")

    try:
        field = review_service.review_field(
            db=db,
            field_id=field.id,
            action=review_request.action,
            edited_value=review_request.edited_value,
            comments=review_request.comments,
            expected_version=review_request.expected_version,
            reviewer_id=current_user.id,
            edit_reason=review_request.edit_reason,
        )
    except StaleDataError as exc:
        db.rollback()
        latest = db.query(ExtractedField).filter(ExtractedField.id == field.id).first()
        last_modified_by = None
        last_modified_at = None
        current_version = latest.version if latest else field.version
        if latest and latest.verified_by_user:
            last_modified_by = latest.verified_by_user.full_name
            last_modified_at = latest.verified_at.isoformat() if latest.verified_at else None
        return build_stale_review_response(
            current_version=current_version,
            last_modified_by=last_modified_by,
            last_modified_at=last_modified_at,
        )

    all_fields = db.query(ExtractedField).filter(ExtractedField.document_id == doc_uuid).all()
    if all(f.verification_status in {VerificationStatus.APPROVED, VerificationStatus.EDITED, VerificationStatus.REJECTED} for f in all_fields):
        if document.processing_status == ProcessingStatus.PENDING_REVIEW:
            document.transition_to(ProcessingStatus.UNDER_REVIEW, current_user.id, reason="Field review completed")
        if document.processing_status == ProcessingStatus.UNDER_REVIEW:
            document.transition_to(ProcessingStatus.VERIFIED, current_user.id, reason="All fields reviewed")
    else:
        if document.processing_status == ProcessingStatus.PENDING_REVIEW:
            document.transition_to(ProcessingStatus.UNDER_REVIEW, current_user.id, reason="Field review in progress")

    db.commit()

    return ExtractedFieldResponse.model_validate(field)


@router.post(
    "/{document_id}/retry-processing",
    summary="Retry Document Processing",
    description="Queue processing again for a failed document.",
)
async def retry_document_processing(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    document = db.query(Document).filter(Document.id == doc_uuid).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.processing_status != ProcessingStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed documents can be retried")

    document.transition_to(ProcessingStatus.CLASSIFYING, current_user.id, reason="Retry requested")
    document.error_message = None
    db.commit()

    try:
        from app.worker.tasks import process_document

        process_document.delay(str(document.id))
    except Exception:
        document.transition_to(ProcessingStatus.FAILED, current_user.id, reason="Failed to enqueue retry")
        document.error_message = "Failed to enqueue retry"
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to queue retry")

    return {
        "document_id": str(document.id),
        "status": document.processing_status.value,
        "message": "Processing retried",
    }


@router.get(
    "",
    summary="List Documents",
    description="List documents with pagination, filtering, and sorting.",
)
async def list_documents(
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
    status: str | None = None,
    department: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """
    List documents with filtering and pagination.

    **Query Parameters:**
    - `page`: Page number (1-indexed, default: 1)
    - `page_size`: Items per page (default: 10)
    - `search`: Search by filename (optional)
    - `status`: Filter by processing status (optional)
    - `department`: Filter by uploader department name or code (optional)
    - `sort_by`: Sort field: created_at, updated_at, original_filename (default: created_at)
    - `sort_order`: asc or desc (default: desc)

    **Returns:**
    - `items`: List of documents
    - `total`: Total document count
    - `page`: Current page
    - `page_size`: Items per page
    """
    # Validate parameters
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10
    if page_size > 100:
        page_size = 100

    # Build query
    query = db.query(Document)

    # Apply search filter
    if search:
        query = query.filter(Document.original_filename.ilike(f"%{search}%"))

    # Apply status filter
    if status:
        try:
            status_enum = ProcessingStatus[status.upper()]
            query = query.filter(Document.processing_status == status_enum)
        except KeyError:
            logger.warning_context(
                "Invalid status filter",
                status=status,
            )

    if department:
        query = query.join(Document.uploaded_by_user).join(User.department).filter(
            (User.department.has(name=department)) | (User.department.has(code=department))
        )

    # Get total before pagination
    total = query.count()

    # Apply sorting
    sort_column = getattr(Document, sort_by, Document.created_at)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Apply pagination
    offset = (page - 1) * page_size
    documents = query.offset(offset).limit(page_size).all()

    logger.info_context(
        "Documents listed",
        page=page,
        page_size=page_size,
        total=total,
        search=search,
        status=status,
    )

    return {
        "items": [
            {
                "id": str(doc.id),
                "original_filename": doc.original_filename,
                "processing_status": doc.processing_status.value,
                "page_count": doc.page_count,
                "file_size_bytes": doc.file_size_bytes,
                "is_text_based": doc.is_text_based,
                "uploaded_by_department": doc.uploaded_by_user.department.name if doc.uploaded_by_user and doc.uploaded_by_user.department else None,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat(),
            }
            for doc in documents
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
