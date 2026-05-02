"""
PDF upload and validation handler.

Handles:
- PDF magic byte verification
- PDF structure validation (PyMuPDF)
- File size validation
- Duplicate detection via SHA-256 hash
- Password-protected PDF detection
- Page count detection
"""

from __future__ import annotations

import hashlib
from io import BytesIO
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.domain.models import Document
from app.models.enums import ProcessingStatus

logger = get_logger(__name__)

# PDF magic bytes
PDF_MAGIC_BYTES = b"%PDF"

# Maximum file size (MB)
MAX_FILE_SIZE_MB = settings.MAX_UPLOAD_SIZE_MB


class PDFValidationError(Exception):
    """Raised when PDF validation fails."""
    pass


class PDFAlreadyExistsError(Exception):
    """Raised when document with same hash already exists."""
    pass


class UploadHandler:
    """Handles PDF upload, validation, and storage."""

    @staticmethod
    def compute_hash(file_bytes: bytes) -> str:
        """
        Compute SHA-256 hash of file.

        Args:
            file_bytes: File content as bytes

        Returns:
            Hex-encoded SHA-256 hash
        """
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def validate_pdf_magic_bytes(file_bytes: bytes) -> None:
        """
        Validate PDF magic bytes.

        Args:
            file_bytes: File content as bytes

        Raises:
            PDFValidationError: If file doesn't start with %PDF
        """
        if not file_bytes.startswith(PDF_MAGIC_BYTES):
            raise PDFValidationError("File does not have valid PDF magic bytes (%PDF)")

        logger.debug_context("PDF magic bytes validated")

    @staticmethod
    def validate_pdf_structure(file_bytes: bytes) -> tuple[int, bool]:
        """
        Validate PDF structure and extract metadata.

        Args:
            file_bytes: File content as bytes

        Returns:
            Tuple of (page_count, is_password_protected)

        Raises:
            PDFValidationError: If PDF is corrupted or invalid
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.warning("PyMuPDF not installed. Install with: pip install pymupdf")
            # Skip structure validation if PyMuPDF not available
            return 0, False

        try:
            # Open PDF from bytes
            pdf_stream = BytesIO(file_bytes)
            pdf_doc = fitz.open(stream=pdf_stream, filetype="pdf")

            # Check if password protected
            is_encrypted = pdf_doc.is_encrypted

            if is_encrypted:
                # Try to unlock with empty password
                if not pdf_doc.authenticate(""):
                    raise PDFValidationError(
                        "PDF is password protected. Please provide unencrypted document."
                    )

            # Get page count
            page_count = len(pdf_doc)

            pdf_doc.close()

            logger.debug_context(
                "PDF structure validated",
                page_count=page_count,
                is_encrypted=is_encrypted,
            )

            return page_count, is_encrypted

        except fitz.FileError:
            raise PDFValidationError("PDF file is corrupted or invalid")
        except Exception as e:
            if isinstance(e, PDFValidationError):
                raise
            raise PDFValidationError(f"Error validating PDF structure: {str(e)}")

    @staticmethod
    def validate_file_size(file_bytes: bytes) -> None:
        """
        Validate file size.

        Args:
            file_bytes: File content as bytes

        Raises:
            PDFValidationError: If file exceeds maximum size
        """
        file_size_mb = len(file_bytes) / (1024 * 1024)

        if file_size_mb > MAX_FILE_SIZE_MB:
            raise PDFValidationError(
                f"File size {file_size_mb:.2f}MB exceeds maximum {MAX_FILE_SIZE_MB}MB"
            )

        logger.debug_context("File size validated", file_size_mb=round(file_size_mb, 2))

    @staticmethod
    def validate_pdf(file_bytes: bytes) -> tuple[int, bool, str]:
        """
        Complete PDF validation.

        Args:
            file_bytes: File content as bytes

        Returns:
            Tuple of (page_count, is_encrypted, file_hash)

        Raises:
            PDFValidationError: If validation fails
        """
        # Validate magic bytes
        UploadHandler.validate_pdf_magic_bytes(file_bytes)

        # Validate file size
        UploadHandler.validate_file_size(file_bytes)

        # Validate PDF structure and get metadata
        page_count, is_encrypted = UploadHandler.validate_pdf_structure(file_bytes)

        # Compute hash
        file_hash = UploadHandler.compute_hash(file_bytes)

        logger.info_context(
            "PDF validation completed",
            page_count=page_count,
            is_encrypted=is_encrypted,
            file_hash=file_hash[:16],  # Log first 16 chars
        )

        return page_count, is_encrypted, file_hash

    @staticmethod
    def check_duplicate(db: Session, file_hash: str) -> Document | None:
        """
        Check if document with same hash already exists.

        Args:
            db: Database session
            file_hash: SHA-256 hash of file

        Returns:
            Existing Document if found, None otherwise
        """
        existing = db.query(Document).filter(Document.file_hash == file_hash).first()

        if existing:
            logger.info_context(
                "Document duplicate detected",
                existing_document_id=str(existing.id),
                file_hash=file_hash[:16],
            )

        return existing

    @staticmethod
    def create_document_record(
        db: Session,
        document_id: UUID,
        file_hash: str,
        original_filename: str,
        storage_path: str,
        mime_type: str,
        file_size_bytes: int,
        page_count: int,
        uploaded_by_user_id: UUID,
        metadata: dict | None = None,
    ) -> Document:
        """
        Create Document database record.

        Args:
            db: Database session
            document_id: UUID for document
            file_hash: SHA-256 hash
            original_filename: Original file name
            storage_path: Path where file is stored
            mime_type: MIME type (application/pdf)
            file_size_bytes: File size in bytes
            page_count: Number of pages
            uploaded_by_user_id: UUID of uploading user
            metadata: Optional metadata JSON

        Returns:
            Created Document record
        """
        document = Document(
            id=document_id,
            file_hash=file_hash,
            original_filename=original_filename,
            storage_path=storage_path,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            page_count=page_count,
            is_text_based=False,  # Will be determined after OCR
            processing_status=ProcessingStatus.UPLOADED,
            uploaded_by_user_id=uploaded_by_user_id,
            metadata_json=metadata or {},
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        logger.info_context(
            "Document record created",
            document_id=str(document.id),
            file_hash=file_hash[:16],
            page_count=page_count,
            file_size_bytes=file_size_bytes,
        )

        return document
