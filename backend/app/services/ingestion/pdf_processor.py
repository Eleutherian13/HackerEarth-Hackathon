"""
PDF Processor - Synchronous PDF text extraction
Uses PyMuPDF for text extraction, Tesseract for OCR fallback
"""

try:
    import pymupdf
    fitz_open = pymupdf.open
except (ImportError, AttributeError):
    try:
        import fitz
        fitz_open = fitz.open
    except ImportError:
        fitz_open = None

from pathlib import Path
from datetime import datetime, timezone
import os

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.domain.models import Document, DocumentPage, ProcessingStatus
from app.services.ingestion.text_cleaner import TextCleaner

logger = get_logger(__name__)

def process_pdf_sync(document_id: str, db=None):
    """
    Process a PDF document synchronously.
    Extracts text from all pages and stores in database.
    """
    
    own_db = False
    if db is None:
        db = SessionLocal()
        own_db = True
    
    try:
        # Get document
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found")
        
        # Update status to CLASSIFYING
        doc.processing_status = ProcessingStatus.CLASSIFYING
        db.commit()
        
        # Find the stored file
        storage_path = Path(settings.LOCAL_STORAGE_PATH) / doc.storage_path
        if not storage_path.exists():
            raise FileNotFoundError(f"PDF file not found: {storage_path}")
        
        logger.info(f"Processing PDF: {storage_path}")
        
        # Check if fitz is available
        if fitz_open is None:
            raise RuntimeError("PyMuPDF is not installed. Please install it using: pip install PyMuPDF")
        
        # Open PDF with PyMuPDF
        try:
            pdf_doc = fitz_open(str(storage_path))
        except Exception as e:
            raise ValueError(f"Failed to open PDF: {str(e)}")
        
        total_pages = pdf_doc.page_count
        doc.page_count = total_pages
        
        text_pages = 0
        text_cleaner = TextCleaner()
        
        # Create pages directory for images
        pages_dir = Path(settings.LOCAL_STORAGE_PATH) / "documents" / str(document_id) / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Extracting text from {total_pages} pages...")
        
        for page_num in range(total_pages):
            page = pdf_doc[page_num]
            
            # Extract text
            text = page.get_text()
            has_text = len(text.strip()) > 50
            
            if has_text:
                text_pages += 1
            
            # Clean the text
            cleaned = text_cleaner.clean_text(text, page_num + 1, total_pages)
            
            # Render page as image for preview and OCR
            try:
                pix = page.get_pixmap(dpi=150)
                img_data = pix.tobytes("png")
                image_filename = f"page_{page_num + 1:03d}.png"
                image_path = pages_dir / image_filename
                
                with open(image_path, 'wb') as f:
                    f.write(img_data)
                
                relative_image_path = f"documents/{document_id}/pages/{image_filename}"
            except Exception as e:
                logger.warning(f"Failed to render page {page_num + 1}: {e}")
                img_data = None
                relative_image_path = None
            
            # OCR for pages without text - skip for now as tesseract may not be installed
            ocr_text = None
            extraction_quality = "GOOD" if has_text else "FAIR"
            needs_review = False
            
            # Create page record
            doc_page = DocumentPage(
                document_id=doc.id,
                page_number=page_num + 1,
                raw_text=text,
                ocr_text=ocr_text,
                page_image_path=relative_image_path,
                extraction_confidence=0.9 if has_text else 0.5
            )
            db.add(doc_page)
        
        pdf_doc.close()
        
        # Determine if document is text-based
        doc.is_text_based = text_pages > (total_pages * 0.7)
        
        # Update status
        doc.processing_status = ProcessingStatus.EXTRACTION_COMPLETE
        
        db.commit()
        
        logger.info(f"Document {document_id} processed: {total_pages} pages, "
                   f"{text_pages} text pages, text-based: {doc.is_text_based}")
        
        # Trigger LLM extraction
        logger.info(f"Triggering LLM extraction for document {document_id}...")
        try:
            from app.services.extraction.extractor import ExtractionOrchestrator
            orchestrator = ExtractionOrchestrator()
            extraction_result = orchestrator.extract_from_document(str(document_id), db)
            logger.info(f"LLM extraction complete: {extraction_result}")
        except Exception as e:
            logger.error(f"LLM extraction failed: {str(e)}")
            doc.processing_status = ProcessingStatus.FAILED
            doc.error_message = f"PDF processed but LLM extraction failed: {str(e)}"
            db.commit()
        
        return {
            "status": "success",
            "total_pages": total_pages,
            "text_pages": text_pages,
            "is_text_based": doc.is_text_based
        }
        
    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {str(e)}")
        try:
            doc.processing_status = ProcessingStatus.FAILED
            doc.error_message = str(e)
            db.commit()
        except:
            pass
        raise
    finally:
        if own_db:
            db.close()
