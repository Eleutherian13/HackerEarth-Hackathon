"""
Additional endpoints for AI extraction and retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.api.deps import get_current_active_user, get_db
from app.models.domain.models import Document, DocumentPage, ExtractedField, User
from app.models.enums import ProcessingStatus, VerificationStatus
from app.services.extraction.extractor import ExtractionOrchestrator

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/{document_id}/extract")
async def trigger_extraction(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Trigger AI extraction on a processed document.
    
    Only works on documents with status EXTRACTION_COMPLETE or PENDING_REVIEW.
    
    Steps:
    1. Load document and validate status
    2. Call Ollama for extraction
    3. Validate and store extracted fields
    4. Update document status to PENDING_REVIEW
    5. Return extraction summary
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    doc = db.query(Document).filter(Document.id == doc_uuid).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if doc.processing_status not in [ProcessingStatus.EXTRACTION_COMPLETE, ProcessingStatus.PENDING_REVIEW]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot extract from status: {doc.processing_status.value}"
        )
    
    try:
        # Update status to extracting
        doc.processing_status = ProcessingStatus.EXTRACTING
        db.commit()
        
        # Run extraction
        extractor = ExtractionOrchestrator()
        result = await extractor.extract_from_document(document_id, db)
        
        # Update document status
        doc.processing_status = ProcessingStatus.PENDING_REVIEW
        db.commit()
        
        return {
            "status": "success",
            "document_id": document_id,
            "extraction_summary": result
        }
    except Exception as e:
        doc.processing_status = ProcessingStatus.FAILED
        doc.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.get("/{document_id}/extractions")
async def get_extractions(
    document_id: str,
    verification_status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all extracted fields for a document.
    
    Optional filter by verification status:
    - UNVERIFIED
    - APPROVED
    - EDITED
    - REJECTED
    - FLAGGED_FOR_REVIEW
    - PENDING
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    doc = db.query(Document).filter(Document.id == doc_uuid).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    query = db.query(ExtractedField).filter(ExtractedField.document_id == doc_uuid)
    
    if verification_status:
        try:
            status_enum = VerificationStatus[verification_status]
            query = query.filter(ExtractedField.verification_status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid verification status: {verification_status}")
    
    fields = query.all()
    
    return {
        "document_id": document_id,
        "total_fields": len(fields),
        "fields_by_status": {},
        "fields": [
            {
                "id": str(f.id),
                "field_type": f.field_type.value,
                "value": f.value[:500],  # Truncate for API response
                "confidence_score": f.confidence_score,
                "source_quotes": f.source_quotes,
                "verification_status": f.verification_status.value,
                "version": f.version,
                "verified_at": f.verified_at.isoformat() if f.verified_at else None,
                "reviewer_comments": f.reviewer_comments
            }
            for f in fields
        ]
    }


@router.get("/{document_id}/pages/{page_number}/text")
async def get_page_text(
    document_id: str,
    page_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get text content for a specific page.
    
    Returns the best available text:
    - cleaned_text (if available)
    - raw_text (if available)
    - ocr_text (if available)
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    doc = db.query(Document).filter(Document.id == doc_uuid).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    page = db.query(DocumentPage).filter(
        DocumentPage.document_id == doc_uuid,
        DocumentPage.page_number == page_number
    ).first()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Return best available text
    page_text = None
    source = None
    
    if hasattr(page, 'cleaned_text') and page.cleaned_text:
        page_text = page.cleaned_text
        source = "cleaned"
    elif page.raw_text:
        page_text = page.raw_text
        source = "raw"
    elif page.ocr_text:
        page_text = page.ocr_text
        source = "ocr"
    
    return {
        "document_id": document_id,
        "page_number": page_number,
        "text": page_text,
        "source": source,
        "extraction_confidence": getattr(page, 'extraction_confidence', None),
        "needs_manual_review": getattr(page, 'needs_manual_review', False)
    }
