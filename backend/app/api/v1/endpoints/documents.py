"""
Document management endpoints - FIXED version.

Handles:
- PDF document upload with validation and deduplication  
- Document metadata retrieval
- Processing status tracking
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from typing import Optional
from datetime import datetime, timezone
import uuid
import hashlib
from pathlib import Path
from threading import Thread

from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.domain.models import User, Document, DocumentPage, ProcessingStatus
from app.api.v1.endpoints.auth_complete import get_current_user
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a court judgment PDF.
    1. Validates the PDF
    2. Computes SHA-256 hash for deduplication
    3. Stores the file
    4. Creates document record
    5. Triggers processing
    """
    
    # ─── VALIDATE FILE ───────────────────────────
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    
    file_size = len(content)
    
    # Validate file size (50MB max)
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB"
        )
    
    # Validate PDF magic bytes
    if not content[:5] == b'%PDF-':
        raise HTTPException(status_code=400, detail="File is not a valid PDF")
    
    # ─── DEDUPLICATION CHECK ────────────────────
    
    file_hash = hashlib.sha256(content).hexdigest()
    
    existing = db.query(Document).filter(Document.file_hash == file_hash).first()
    if existing:
        return {
            "message": "Document already exists",
            "document_id": str(existing.id),
            "filename": existing.original_filename,
            "status": existing.processing_status.value if hasattr(existing.processing_status, 'value') else str(existing.processing_status),
            "duplicate": True
        }
    
    # ─── STORE FILE ─────────────────────────────
    
    doc_id = uuid.uuid4()
    storage_dir = Path(settings.LOCAL_STORAGE_PATH) / "documents" / str(doc_id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize filename
    safe_filename = "".join(c for c in file.filename if c.isalnum() or c in '._- ')
    storage_path = storage_dir / safe_filename
    
    try:
        with open(storage_path, 'wb') as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store file: {str(e)}")
    
    # ─── CREATE DATABASE RECORD ─────────────────
    
    try:
        document = Document(
            id=doc_id,
            file_hash=file_hash,
            original_filename=safe_filename,
            storage_path=str(storage_path.relative_to(Path(settings.LOCAL_STORAGE_PATH))),
            mime_type="application/pdf",
            file_size_bytes=file_size,
            processing_status=ProcessingStatus.UPLOADED,
            uploaded_by_user_id=current_user.id,
            metadata_json={
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "uploaded_by": current_user.full_name,
                "original_filename": file.filename
            }
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
    except Exception as e:
        # Clean up stored file if database fails
        if storage_path.exists():
            storage_path.unlink()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # ─── TRIGGER PROCESSING ─────────────────────
    
    def process_pdf_background(document_id: str):
        """Process PDF in background thread to avoid blocking the response."""
        try:
            from app.services.ingestion.pdf_processor import process_pdf_sync
            from app.db.session import SessionLocal
            
            bg_db = SessionLocal()
            try:
                process_pdf_sync(str(document_id), bg_db)
                logger.info(f"Background PDF processing completed for document {document_id}")
            finally:
                bg_db.close()
        except Exception as e:
            logger.error(f"Background PDF processing failed for document {document_id}: {e}")
            try:
                # Try to update document status in database
                from app.db.session import SessionLocal
                bg_db = SessionLocal()
                doc = bg_db.query(Document).filter(Document.id == document_id).first()
                if doc:
                    doc.processing_status = ProcessingStatus.FAILED
                    doc.error_message = str(e)
                    bg_db.commit()
                bg_db.close()
            except:
                pass
    
    # Start PDF processing in background thread (non-blocking)
    thread = Thread(target=process_pdf_background, args=(str(doc_id),), daemon=True)
    thread.start()
    
    db.refresh(document)
    
    return {
        "document_id": str(document.id),
        "filename": document.original_filename,
        "file_hash": file_hash,
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "status": document.processing_status.value if hasattr(document.processing_status, 'value') else str(document.processing_status),
        "page_count": document.page_count,
        "is_text_based": document.is_text_based,
        "duplicate": False
    }


@router.get("/")
async def list_documents(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all documents with filtering and pagination"""
    
    query = db.query(Document)
    
    # Filter by status
    if status_filter:
        try:
            ps = ProcessingStatus(status_filter)
            query = query.filter(Document.processing_status == ps)
        except ValueError:
            pass
    
    # Search by filename
    if search:
        query = query.filter(Document.original_filename.ilike(f"%{search}%"))
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    documents = query.order_by(Document.created_at.desc()) \
                     .offset((page - 1) * per_page) \
                     .limit(per_page) \
                     .all()
    
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "documents": [
            {
                "id": str(doc.id),
                "filename": doc.original_filename,
                "status": doc.processing_status.value if hasattr(doc.processing_status, 'value') else str(doc.processing_status),
                "page_count": doc.page_count,
                "file_size_mb": round(doc.file_size_bytes / (1024 * 1024), 2) if doc.file_size_bytes else 0,
                "is_text_based": doc.is_text_based,
                "uploaded_at": doc.created_at.isoformat() if doc.created_at else None,
                "error_message": doc.error_message
            }
            for doc in documents
        ]
    }


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document details"""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    
    doc = db.query(Document).filter(Document.id == doc_uuid).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": str(doc.id),
        "filename": doc.original_filename,
        "status": doc.processing_status.value if hasattr(doc.processing_status, 'value') else str(doc.processing_status),
        "page_count": doc.page_count,
        "file_size_bytes": doc.file_size_bytes,
        "is_text_based": doc.is_text_based,
        "error_message": doc.error_message,
        "metadata": doc.metadata_json,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
    }


@router.get("/{document_id}/status")
async def get_document_status(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed document processing status"""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    
    doc = db.query(Document).filter(Document.id == doc_uuid).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get pages
    pages = db.query(DocumentPage).filter(
        DocumentPage.document_id == doc_uuid
    ).order_by(DocumentPage.page_number).all()
    
    return {
        "document_id": str(doc.id),
        "filename": doc.original_filename,
        "status": doc.processing_status.value if hasattr(doc.processing_status, 'value') else str(doc.processing_status),
        "page_count": doc.page_count,
        "is_text_based": doc.is_text_based,
        "error_message": doc.error_message,
        "pages": [
            {
                "page_number": p.page_number,
                "has_text": bool(p.raw_text or p.ocr_text),
                "text_length": len(p.raw_text or p.ocr_text or ""),
                "extraction_confidence": p.extraction_confidence
            }
            for p in pages
        ] if pages else []
    }
