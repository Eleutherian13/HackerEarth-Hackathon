"""Celery tasks for document processing pipeline."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from celery import shared_task
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.domain.models import Document, DocumentPage, ProcessingJob
from app.models.enums import JobStatus, JobType, ProcessingStatus
from app.services.extraction.pipeline import perform_structured_extraction
from app.services.ingestion.pdf_classifier import PDFClassifier, PDFClassificationError
from app.services.ingestion.text_extractor import TextExtractor, TextExtractionError
from app.services.ingestion.ocr_pipeline import OCRPipeline, OCRError
from app.services.ingestion.storage import get_storage_backend

logger = get_logger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="document.process_document",
)
def process_document(
    self,
    document_id: str,
) -> dict[str, str]:
    """
    Process document: classify, extract text, and prepare for analysis.

    Args:
        document_id: UUID of document to process

    Returns:
        Dict with "status": "success" or "failed"

    Raises:
        Will retry up to 3 times with exponential backoff
    """
    db: Session = SessionLocal()
    job_id = str(uuid.uuid4())

    try:
        # Get document from database
        doc_uuid = uuid.UUID(document_id)
        document = db.query(Document).filter(Document.id == doc_uuid).first()

        if not document:
            logger.error_context("Document not found", document_id=document_id)
            return {"status": "failed", "error": "Document not found"}

        # Create processing job record
        job = ProcessingJob(
            id=uuid.uuid4(),
            document_id=document.id,
            job_type=JobType.CLASSIFICATION,
            celery_task_id=self.request.id,
            status=JobStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
        )
        db.add(job)
        db.commit()
        job_id = str(job.id)

        logger.info_context(
            "Starting document processing",
            document_id=document_id,
            job_id=job_id,
        )

        # Download document from storage
        logger.info_context("Downloading document from storage", storage_path=document.storage_path)
        storage_backend = get_storage_backend()
        file_bytes = storage_backend.download(document.storage_path)

        # Step 1: Classify PDF type
        logger.info_context("Classifying PDF type", document_id=document_id)
        try:
            pdf_type, _, metrics = PDFClassifier.classify_pdf(file_bytes)
            document.is_text_based = pdf_type.value == "TEXT_BASED"

            logger.info_context(
                "PDF classified",
                pdf_type=pdf_type.value,
                metrics=metrics,
            )
        except PDFClassificationError as e:
            logger.error_context(
                "PDF classification failed",
                document_id=document_id,
                error=str(e),
            )
            return _mark_job_failed(db, job, document, str(e), 1)

        # Step 2: Extract text based on type
        document.processing_status = ProcessingStatus.EXTRACTING
        document.updated_at = datetime.utcnow()
        db.commit()

        if pdf_type.value == "TEXT_BASED":
            logger.info_context("Extracting text from digital PDF", document_id=document_id)
            result = _extract_text_based(db, document, file_bytes)
        elif pdf_type.value == "SCANNED":
            logger.info_context("Processing scanned PDF with OCR", document_id=document_id)
            result = _extract_scanned(db, document, file_bytes)
        else:  # HYBRID
            logger.info_context("Processing hybrid PDF (text + OCR)", document_id=document_id)
            result = _extract_hybrid(db, document, file_bytes)

        if not result:
            logger.error_context("Text extraction failed", document_id=document_id)
            return _mark_job_failed(
                db,
                job,
                document,
                "Text extraction failed",
                2,
            )

        # Step 3: Run structured extraction on extracted pages
        extraction_job = ProcessingJob(
            id=uuid.uuid4(),
            document_id=document.id,
            job_type=JobType.EXTRACTION,
            celery_task_id=self.request.id,
            status=JobStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
        )
        db.add(extraction_job)
        db.commit()

        pages = db.query(DocumentPage).filter(DocumentPage.document_id == document.id).order_by(DocumentPage.page_number).all()
        extraction_summary = perform_structured_extraction(db, document, pages)

        if not extraction_summary:
            logger.error_context("Structured extraction failed", document_id=document_id)
            return _mark_job_failed(
                db,
                extraction_job,
                document,
                "Structured extraction failed",
                3,
            )

        document.processing_status = ProcessingStatus.PENDING_REVIEW
        document.updated_at = datetime.utcnow()

        extraction_job.status = JobStatus.COMPLETED
        extraction_job.completed_at = datetime.utcnow()
        extraction_job.output_summary = {
            "pages_processed": result.get("pages_processed", 0),
            "extraction_method": extraction_summary.get("extraction_method", "unknown"),
            "total_text_extracted": result.get("total_chars", 0),
            "fields_extracted": extraction_summary.get("fields_created", 0),
            "average_confidence": extraction_summary.get("confidence_average", 0),
        }

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.output_summary = {
            "pages_processed": result.get("pages_processed", 0),
            "extraction_method": result.get("extraction_method", "unknown"),
            "total_text_extracted": result.get("total_chars", 0),
        }

        db.commit()

        logger.info_context(
            "Document processing completed",
            document_id=document_id,
            job_id=job_id,
            pages=result.get("pages_processed"),
        )

        return {"status": "success", "document_id": document_id}

    except Exception as e:
        logger.error_context(
            "Unexpected error in process_document",
            document_id=document_id,
            exc_info=True,
        )

        # Retry with exponential backoff
        retry_count = self.request.retries
        if retry_count < 3:
            countdown = 60 * (2 ** retry_count)  # 60s, 120s, 240s
            logger.info_context(
                "Retrying document processing",
                document_id=document_id,
                retry=retry_count + 1,
                countdown=countdown,
            )
            raise self.retry(exc=e, countdown=countdown)
        else:
            # Max retries exceeded
            return _mark_job_failed(db, None, None, str(e), 3)

    finally:
        db.close()


def _extract_text_based(
    db: Session,
    document: Document,
    file_bytes: bytes,
) -> dict | None:
    """
    Extract text from digital PDF.

    Args:
        db: Database session
        document: Document model
        file_bytes: PDF content

    Returns:
        Result dict or None on failure
    """
    try:
        # Extract pages
        pages = TextExtractor.extract_all_pages(file_bytes)

        for page_data in pages:
            page_record = DocumentPage(
                id=uuid.uuid4(),
                document_id=document.id,
                page_number=page_data.page_number,
                raw_text=page_data.raw_text,
                ocr_text=None,  # No OCR for digital PDFs
                extraction_confidence=1.0,
            )
            db.add(page_record)

        db.commit()

        return {
            "pages_processed": len(pages),
            "extraction_method": "text_extraction",
            "total_chars": sum(len(p.raw_text) for p in pages),
        }

    except TextExtractionError as e:
        logger.error_context("Text extraction failed", error=str(e))
        return None


def _extract_scanned(
    db: Session,
    document: Document,
    file_bytes: bytes,
) -> dict | None:
    """
    Extract text from scanned PDF using OCR.

    Args:
        db: Database session
        document: Document model
        file_bytes: PDF content

    Returns:
        Result dict or None on failure
    """
    try:
        # Extract page images
        page_images = PDFClassifier.extract_page_images(file_bytes, dpi=300)

        # Initialize OCR pipeline
        ocr_pipeline = OCRPipeline()

        total_chars = 0
        for page_num, image_bytes in page_images:
            try:
                # OCR the page
                ocr_result = ocr_pipeline.process_page_image(image_bytes)

                # Calculate confidence
                confidence = min(
                    1.0,
                    max(0.0, ocr_result.confidence_score),
                )

                # Create page record
                page_record = DocumentPage(
                    id=uuid.uuid4(),
                    document_id=document.id,
                    page_number=page_num,
                    raw_text=None,
                    ocr_text=ocr_result.text,
                    extraction_confidence=confidence,
                )
                db.add(page_record)
                total_chars += len(ocr_result.text)

                logger.info_context(
                    "OCR processed page",
                    page=page_num,
                    confidence=confidence,
                )

            except OCRError as e:
                logger.warning_context(
                    "OCR failed for page, marking low confidence",
                    page=page_num,
                    error=str(e),
                )
                # Still create record with None text
                page_record = DocumentPage(
                    id=uuid.uuid4(),
                    document_id=document.id,
                    page_number=page_num,
                    raw_text=None,
                    ocr_text=None,
                    extraction_confidence=0.0,
                )
                db.add(page_record)

        db.commit()

        return {
            "pages_processed": len(page_images),
            "extraction_method": "ocr_pipeline",
            "total_chars": total_chars,
        }

    except Exception as e:
        logger.error_context("Scanned PDF processing failed", error=str(e))
        return None


def _extract_hybrid(
    db: Session,
    document: Document,
    file_bytes: bytes,
) -> dict | None:
    """
    Extract text from hybrid PDF (text + images).

    Prefers extracted text, uses OCR for image-heavy pages.

    Args:
        db: Database session
        document: Document model
        file_bytes: PDF content

    Returns:
        Result dict or None on failure
    """
    try:
        # First, try text extraction
        pages = TextExtractor.extract_all_pages(file_bytes)

        # Get page images for OCR fallback
        page_images = PDFClassifier.extract_page_images(file_bytes, dpi=300)
        ocr_pipeline = OCRPipeline()

        total_chars = 0
        for i, page_data in enumerate(pages):
            if len(page_data.raw_text.strip()) > 100:
                # Sufficient text from extraction
                page_record = DocumentPage(
                    id=uuid.uuid4(),
                    document_id=document.id,
                    page_number=page_data.page_number,
                    raw_text=page_data.raw_text,
                    ocr_text=None,
                    extraction_confidence=1.0,
                )
                total_chars += len(page_data.raw_text)
            else:
                # Fallback to OCR
                if i < len(page_images):
                    _, image_bytes = page_images[i]
                    try:
                        ocr_result = ocr_pipeline.process_page_image(image_bytes)
                        page_record = DocumentPage(
                            id=uuid.uuid4(),
                            document_id=document.id,
                            page_number=page_data.page_number,
                            raw_text=page_data.raw_text if page_data.raw_text.strip() else None,
                            ocr_text=ocr_result.text,
                            extraction_confidence=ocr_result.confidence_score,
                        )
                        total_chars += len(ocr_result.text)
                    except OCRError:
                        page_record = DocumentPage(
                            id=uuid.uuid4(),
                            document_id=document.id,
                            page_number=page_data.page_number,
                            raw_text=page_data.raw_text if page_data.raw_text.strip() else None,
                            ocr_text=None,
                            extraction_confidence=0.5,
                        )
                else:
                    page_record = DocumentPage(
                        id=uuid.uuid4(),
                        document_id=document.id,
                        page_number=page_data.page_number,
                        raw_text=page_data.raw_text,
                        ocr_text=None,
                        extraction_confidence=0.5,
                    )

            db.add(page_record)

        db.commit()

        return {
            "pages_processed": len(pages),
            "extraction_method": "hybrid_extraction",
            "total_chars": total_chars,
        }

    except Exception as e:
        logger.error_context("Hybrid PDF processing failed", error=str(e))
        return None


def _mark_job_failed(
    db: Session,
    job: ProcessingJob | None,
    document: Document | None,
    error_message: str,
    step: int,
) -> dict:
    """
    Mark job and document as failed.

    Args:
        db: Database session
        job: ProcessingJob model or None
        document: Document model or None
        error_message: Error details
        step: Processing step where failure occurred

    Returns:
        Dict with "status": "failed"
    """
    try:
        if job:
            job.status = JobStatus.FAILED
            job.error_message = error_message
            job.completed_at = datetime.utcnow()

        if document:
            document.processing_status = ProcessingStatus.FAILED
            document.error_message = error_message
            document.updated_at = datetime.utcnow()

        db.commit()
    except Exception as e:
        logger.error_context("Failed to mark job as failed", error=str(e))

    return {"status": "failed", "error": error_message, "step": step}
