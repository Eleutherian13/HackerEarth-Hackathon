"""
Extraction orchestrator that coordinates document extraction workflow.
Takes document text → Ollama extraction → validation → sanitization → database storage.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.domain.models import Document, DocumentPage, ExtractedField
from app.models.enums import FieldType, ExtractionMethod, VerificationStatus, ProcessingStatus
from app.services.llm import get_ollama_client, OllamaClientError
from .validator import ExtractionValidator, ValidationResult
from .sanitizer import ExtractionSanitizer

logger = logging.getLogger(__name__)


class ExtractionOrchestrator:
    """
    Main extraction orchestrator.
    Coordinates the extraction pipeline: load → extract → validate → sanitize → store.
    """
    
    def __init__(self):
        """Initialize orchestrator with dependencies."""
        self.ollama = get_ollama_client()
        self.validator = ExtractionValidator()
        self.sanitizer = ExtractionSanitizer()
    
    def extract_from_document(self, document_id: str, db: Session) -> dict:
        """
        MAIN EXTRACTION PIPELINE (Synchronous).
        
        Steps:
        1. Load document pages from database
        2. Combine text from all pages
        3. Send to Ollama for extraction
        4. Validate extracted fields
        5. Sanitize values
        6. Store ExtractedField records in database
        7. Update document status to PENDING_REVIEW
        8. Return extraction summary
        
        Args:
            document_id: UUID of document to extract
            db: SQLAlchemy session
            
        Returns:
            Dictionary with extraction summary
        """
        try:
            logger.info(f"Starting extraction for document {document_id}")
            
            # Step 1: Load document and pages
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Step 2: Load document text
            document_text = self._load_document_text(document_id, db)
            if not document_text.strip():
                raise ValueError("Document text is empty")
            
            page_count = document.page_count or 1
            logger.debug(f"Loaded {len(document_text)} characters from {page_count} pages")
            
            # Step 3: Send to Ollama for extraction
            logger.info("Calling Ollama for field extraction...")
            extraction = self.ollama.extract_fields(document_text, page_count)
            logger.debug(f"Received extraction with fields: {list(extraction.keys())}")
            
            # Step 4: Validate (if validator exists)
            try:
                validation_result = self.validator.validate_extraction(extraction)
                if not validation_result.is_valid:
                    logger.warning(f"Extraction validation failed: {validation_result.errors}")
                    # Continue anyway, mark fields with validation issues
            except Exception as e:
                logger.warning(f"Validation skipped: {e}")
            
            # Step 5: Sanitize (if sanitizer exists)
            try:
                extraction = self.sanitizer.sanitize_extraction(extraction)
                logger.debug("Extraction sanitized")
            except Exception as e:
                logger.warning(f"Sanitization skipped: {e}")
            
            # Step 6: Store in database
            stored_count = self._store_extracted_fields(document_id, extraction, db)
            logger.info(f"Stored {stored_count} extracted fields in database")
            
            # Step 7: Update document status
            document.processing_status = ProcessingStatus.PENDING_REVIEW
            document.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"Document {document_id} transitioned to PENDING_REVIEW")
            
            # Step 8: Return summary
            case_details = extraction.get("case_details", {})
            summary = {
                "document_id": str(document_id),
                "fields_count": stored_count,
                "case_number": case_details.get("case_number", {}).get("value", "NOT_FOUND"),
                "court_name": case_details.get("court_name", {}).get("value", "NOT_FOUND"),
                "judgment_date": case_details.get("judgment_date", {}).get("value", "NOT_FOUND"),
                "status": "success",
            }
            
            return summary
        
        except OllamaClientError as e:
            logger.error(f"Ollama extraction failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Extraction pipeline failed: {e}", exc_info=True)
            raise
    
    def _load_document_text(self, document_id: str, db: Session) -> str:
        """
        Load all pages text from database.
        Prefers: cleaned_text > raw_text > ocr_text
        
        Args:
            document_id: UUID of document
            db: SQLAlchemy session
            
        Returns:
            Combined text from all pages
        """
        pages = db.query(DocumentPage).filter(
            DocumentPage.document_id == document_id
        ).order_by(DocumentPage.page_number).all()
        
        if not pages:
            logger.warning(f"No pages found for document {document_id}")
            return ""
        
        text_parts = []
        for page in pages:
            # Use the best available text
            page_text = None
            if hasattr(page, 'cleaned_text') and page.cleaned_text:
                page_text = page.cleaned_text
            elif page.raw_text:
                page_text = page.raw_text
            elif hasattr(page, 'ocr_text') and page.ocr_text:
                page_text = page.ocr_text
            
            if page_text:
                text_parts.append(page_text)
            else:
                logger.warning(f"Page {page.page_number} has no text content")
        
        combined = "\n\n---PAGE BREAK---\n\n".join(text_parts)
        return combined
    
    def _store_extracted_fields(self, document_id: str, extraction: dict, db: Session) -> int:
        """
        Convert extraction JSON to ExtractedField database records.
        
        Args:
            document_id: UUID of document
            extraction: Extraction dictionary from Ollama
            db: SQLAlchemy session
            
        Returns:
            Number of fields stored
        """
        fields_stored = 0
        
        # Store case details
        case_details = extraction.get("case_details", {})
        for field_name, field_value in case_details.items():
            if isinstance(field_value, dict) and "value" in field_value:
                field_type = self._map_field_name_to_type(field_name)
                if field_type:
                    field = ExtractedField(
                        id=uuid.uuid4(),
                        document_id=uuid.UUID(document_id),
                        field_type=field_type,
                        value=str(field_value.get("value", "")),
                        confidence_score=float(field_value.get("confidence", 0.5)),
                        extraction_method=ExtractionMethod.LLM_INFERRED,
                        source_quotes=[{
                            "quote": field_value.get("source_quote", ""),
                            "page": 1,
                            "confidence": field_value.get("confidence", 0.5)
                        }],
                        verification_status=VerificationStatus.UNVERIFIED,
                    )
                    db.add(field)
                    fields_stored += 1
        
        # Store operative directions
        for direction in extraction.get("operative_directions", []):
            field = ExtractedField(
                id=uuid.uuid4(),
                document_id=uuid.UUID(document_id),
                field_type=FieldType.OPERATIVE_DIRECTION,
                value=str(direction.get("description", "")),
                confidence_score=float(direction.get("confidence", 0.7)),
                extraction_method=ExtractionMethod.LLM_INFERRED,
                source_quotes=[{
                    "quote": direction.get("source_quote", ""),
                    "deadline_days": direction.get("deadline_days"),
                    "deadline_date": direction.get("deadline_date"),
                    "confidence": direction.get("confidence", 0.7)
                }],
                verification_status=VerificationStatus.UNVERIFIED,
            )
            db.add(field)
            fields_stored += 1
        
        # Store deadlines
        for deadline in extraction.get("deadlines", []):
            field = ExtractedField(
                id=uuid.uuid4(),
                document_id=uuid.UUID(document_id),
                field_type=FieldType.DEADLINE,
                value=str(deadline.get("due_date", "")),
                confidence_score=float(deadline.get("confidence", 0.8)),
                extraction_method=ExtractionMethod.LLM_INFERRED,
                source_quotes=[{
                    "quote": deadline.get("source_quote", ""),
                    "timeframe_text": deadline.get("timeframe_text", ""),
                    "is_explicit": deadline.get("is_explicit", False),
                    "confidence": deadline.get("confidence", 0.8)
                }],
                verification_status=VerificationStatus.UNVERIFIED,
            )
            db.add(field)
            fields_stored += 1
        
        # Store compliance requirements
        for req in extraction.get("compliance_requirements", []):
            field = ExtractedField(
                id=uuid.uuid4(),
                document_id=uuid.UUID(document_id),
                field_type=FieldType.COMPLIANCE_OBLIGATION,
                value=str(req.get("requirement", "")),
                confidence_score=float(req.get("confidence", 0.75)),
                extraction_method=ExtractionMethod.LLM_INFERRED,
                source_quotes=[{
                    "quote": req.get("source_quote", ""),
                    "action_needed": req.get("action_needed", ""),
                    "is_mandatory": req.get("is_mandatory", True),
                    "confidence": req.get("confidence", 0.75)
                }],
                verification_status=VerificationStatus.UNVERIFIED,
            )
            db.add(field)
            fields_stored += 1
        
        # Store appeal info
        appeal_info = extraction.get("appeal_indicators", {})
        if appeal_info:
            field = ExtractedField(
                id=uuid.uuid4(),
                document_id=uuid.UUID(document_id),
                field_type=FieldType.APPEAL_CLUE,
                value=str(appeal_info.get("appeal_forum", "Not specified")),
                confidence_score=float(appeal_info.get("confidence", 0.7)),
                extraction_method=ExtractionMethod.LLM_INFERRED,
                source_quotes=[{
                    "quote": appeal_info.get("source_quote", ""),
                    "is_appealable": appeal_info.get("is_appealable", True),
                    "limitation_period_days": appeal_info.get("limitation_period_days"),
                    "confidence": appeal_info.get("confidence", 0.7)
                }],
                verification_status=VerificationStatus.UNVERIFIED,
            )
            db.add(field)
            fields_stored += 1
        
        # Store costs and penalties
        costs_info = extraction.get("costs_and_penalties", {})
        if costs_info:
            field = ExtractedField(
                id=uuid.uuid4(),
                document_id=uuid.UUID(document_id),
                field_type=FieldType.COST_ORDER,
                value=str(costs_info.get("amount", "Not specified")),
                confidence_score=float(costs_info.get("confidence", 0.75)),
                extraction_method=ExtractionMethod.LLM_INFERRED,
                source_quotes=[{
                    "quote": costs_info.get("source_quote", ""),
                    "costs_awarded": costs_info.get("costs_awarded", False),
                    "penalty_risk": costs_info.get("penalty_risk", "NONE"),
                    "contempt_risk": costs_info.get("contempt_risk", "NONE"),
                    "confidence": costs_info.get("confidence", 0.75)
                }],
                verification_status=VerificationStatus.UNVERIFIED,
            )
            db.add(field)
            fields_stored += 1
        
        db.commit()
        return fields_stored
    
    def _map_field_name_to_type(self, field_name: str) -> Optional[FieldType]:
        """Map extraction field name to FieldType enum."""
        mapping = {
            "case_number": FieldType.CASE_NUMBER,
            "case_title": FieldType.CASE_TITLE,
            "court_name": FieldType.COURT_NAME,
            "judgment_date": FieldType.JUDGMENT_DATE,
            "judge_bench": FieldType.BENCH_INFO,
        }
        return mapping.get(field_name)
