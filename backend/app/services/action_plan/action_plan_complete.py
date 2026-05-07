"""
Action plan generator.
Converts verified extractions into actionable items for departments.
"""

import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.domain.models import ActionPlanItem, Document, ExtractedField, Department
from app.models.enums import (
    ActionType, Priority, VerificationStatus, DueDateSource,
    FieldType, CompletionStatus
)
from app.services.llm import get_ollama_client, OllamaClientError
from .department_matcher import get_department_matcher

logger = logging.getLogger(__name__)


class ActionPlanGenerator:
    """
    Generates action plan items from verified court judgment extractions.
    """
    
    def __init__(self):
        """Initialize generator with dependencies."""
        self.ollama = get_ollama_client()
        self.department_matcher = get_department_matcher()
    
    async def generate_action_plan(self, document_id: str, db: Session) -> list[dict]:
        """
        GENERATE ACTION PLAN FROM VERIFIED EXTRACTIONS.
        
        Steps:
        1. Load VERIFIED extractions (status APPROVED or EDITED) only
        2. Separate into categories
        3. For each direction: create action item
        4. Map responsible department
        5. Calculate due dates
        6. Assess risk
        7. Store ActionPlanItem records
        8. Return generated items
        
        Args:
            document_id: UUID of document
            db: SQLAlchemy session
            
        Returns:
            List of generated action plan items
        """
        try:
            logger.info(f"Generating action plan for document {document_id}")
            
            # Load document and verified extractions
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            verified_fields = db.query(ExtractedField).filter(
                ExtractedField.document_id == document_id,
                ExtractedField.verification_status.in_([VerificationStatus.APPROVED, VerificationStatus.EDITED])
            ).all()
            
            if not verified_fields:
                raise ValueError("No verified extractions found")
            
            logger.info(f"Found {len(verified_fields)} verified fields")
            
            # Extract and structure verified data
            structured_extractions = self._structure_extractions(verified_fields)
            logger.debug(f"Structured extractions: {structured_extractions.keys()}")
            
            # Get judgment date for calculations
            judgment_date = self._get_judgment_date(structured_extractions)
            
            # Generate action items using rule-based approach
            action_items = []
            
            # Process operative directions
            for direction in structured_extractions.get("operative_directions", []):
                item = self._create_action_item_from_direction(
                    direction, judgment_date, db
                )
                if item:
                    action_items.append(item)
            
            # Process deadlines
            for deadline in structured_extractions.get("deadlines", []):
                item = self._create_action_item_from_deadline(deadline, db)
                if item:
                    action_items.append(item)
            
            # Process compliance requirements
            for req in structured_extractions.get("compliance_requirements", []):
                item = self._create_action_item_from_requirement(req, judgment_date, db)
                if item:
                    action_items.append(item)
            
            # Process appeal indicators
            appeal_items = self._create_appeal_action_items(
                structured_extractions.get("appeal_indicators", {}),
                judgment_date, db
            )
            action_items.extend(appeal_items)
            
            # Store in database
            stored_items = []
            for action_item in action_items:
                db_item = ActionPlanItem(**action_item)
                db.add(db_item)
                stored_items.append(db_item)
            
            db.commit()
            logger.info(f"Stored {len(stored_items)} action plan items")
            
            # Return as dictionaries
            return [self._action_item_to_dict(item) for item in stored_items]
        
        except Exception as e:
            logger.error(f"Action plan generation failed: {e}", exc_info=True)
            raise
    
    def _structure_extractions(self, fields: list[ExtractedField]) -> dict:
        """Convert extracted fields to structured dictionary."""
        structured = {
            "operative_directions": [],
            "deadlines": [],
            "compliance_requirements": [],
            "appeal_indicators": {},
            "case_details": {}
        }
        
        for field in fields:
            if field.field_type == FieldType.OPERATIVE_DIRECTION:
                base_dict = {
                    "description": field.value,
                    "source_quote": field.source_quotes[0].get("quote", "") if field.source_quotes else "",
                    "confidence": field.confidence_score,
                }
                if field.source_quotes:
                    base_dict.update(field.source_quotes[0])
                structured["operative_directions"].append(base_dict)
            elif field.field_type == FieldType.DEADLINE:
                base_dict = {
                    "due_date": field.value,
                    "source_quote": field.source_quotes[0].get("quote", "") if field.source_quotes else "",
                    "confidence": field.confidence_score,
                }
                if field.source_quotes:
                    base_dict.update(field.source_quotes[0])
                structured["deadlines"].append(base_dict)
            elif field.field_type == FieldType.COMPLIANCE_OBLIGATION:
                base_dict = {
                    "requirement": field.value,
                    "source_quote": field.source_quotes[0].get("quote", "") if field.source_quotes else "",
                    "confidence": field.confidence_score,
                }
                if field.source_quotes:
                    base_dict.update(field.source_quotes[0])
                structured["compliance_requirements"].append(base_dict)
            elif field.field_type == FieldType.APPEAL_CLUE:
                base_dict = {
                    "appeal_forum": field.value,
                    "source_quote": field.source_quotes[0].get("quote", "") if field.source_quotes else "",
                    "confidence": field.confidence_score,
                }
                if field.source_quotes:
                    base_dict.update(field.source_quotes[0])
                structured["appeal_indicators"] = base_dict
            elif field.field_type in [FieldType.CASE_NUMBER, FieldType.CASE_TITLE, FieldType.COURT_NAME, FieldType.JUDGMENT_DATE]:
                structured["case_details"][field.field_type.value.lower()] = field.value
        
        return structured
    
    def _get_judgment_date(self, structured: dict) -> date:
        """Extract judgment date from structured data."""
        judgment_date_str = structured.get("case_details", {}).get("judgment_date", "")
        
        if not judgment_date_str:
            logger.warning("Judgment date not found, using today's date")
            return date.today()
        
        # Parse YYYY-MM-DD format
        try:
            return datetime.strptime(judgment_date_str, "%Y-%m-%d").date()
        except ValueError:
            logger.warning(f"Could not parse judgment date: {judgment_date_str}")
            return date.today()
    
    def _create_action_item_from_direction(self, direction: dict, judgment_date: date, db: Session) -> Optional[dict]:
        """Create action item from operative direction."""
        action_type = self._determine_action_type(direction.get("description", ""))
        priority = self._determine_priority(direction, judgment_date)
        due_date = self._calculate_due_date(direction, judgment_date)
        
        dept_text = direction.get("responsible_entity", "Ministry of Law and Justice")
        department = self._match_and_get_department(dept_text, db)
        
        return {
            "id": uuid.uuid4(),
            "document_id": None,  # Will be set by caller
            "item_type": action_type,
            "title": f"Comply with operative direction",
            "description": direction.get("description", "")[:2000],
            "priority": priority,
            "due_date": due_date,
            "due_date_source": DueDateSource.EXPLICIT_IN_JUDGMENT if direction.get("deadline_explicit") else DueDateSource.INFERRED,
            "responsible_department_id": department.id if department else None,
            "risk_if_ignored": self._assess_risk(direction, {}),
            "suggested_next_step": "Review direction and prepare compliance plan",
            "source_evidence": {
                "source_quote": direction.get("source_quote", ""),
                "confidence": direction.get("confidence", 0.7)
            },
            "verification_status": VerificationStatus.PENDING,
            "completion_status": CompletionStatus.NOT_STARTED,
        }
    
    def _create_action_item_from_deadline(self, deadline: dict, db: Session) -> Optional[dict]:
        """Create action item from deadline."""
        due_date = deadline.get("due_date")
        if isinstance(due_date, str):
            try:
                due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
            except ValueError:
                due_date = None
        
        priority = Priority.CRITICAL if due_date and (due_date - date.today()).days <= 7 else Priority.HIGH
        
        return {
            "id": uuid.uuid4(),
            "document_id": None,
            "item_type": ActionType.COMPLIANCE,
            "title": f"Meet deadline: {deadline.get('description', '')[:100]}",
            "description": deadline.get("description", "")[:2000],
            "priority": priority,
            "due_date": due_date,
            "due_date_source": DueDateSource.EXPLICIT_IN_JUDGMENT if deadline.get("is_explicit") else DueDateSource.INFERRED,
            "responsible_department_id": None,
            "risk_if_ignored": "Failure to meet court-ordered deadline may result in contempt of court proceedings",
            "suggested_next_step": "Assign owner and create task tracking",
            "source_evidence": {
                "source_quote": deadline.get("source_quote", ""),
                "timeframe_text": deadline.get("timeframe_text", ""),
                "confidence": deadline.get("confidence", 0.8)
            },
            "verification_status": VerificationStatus.PENDING,
            "completion_status": CompletionStatus.NOT_STARTED,
        }
    
    def _create_action_item_from_requirement(self, req: dict, judgment_date: date, db: Session) -> Optional[dict]:
        """Create action item from compliance requirement."""
        due_date = judgment_date + timedelta(days=30)
        
        return {
            "id": uuid.uuid4(),
            "document_id": None,
            "item_type": ActionType.COMPLIANCE if req.get("is_mandatory") else ActionType.INTERNAL_REVIEW,
            "title": f"Comply with: {req.get('requirement', '')[:100]}",
            "description": req.get("requirement", "")[:2000],
            "priority": Priority.HIGH if req.get("is_mandatory") else Priority.MEDIUM,
            "due_date": due_date,
            "due_date_source": DueDateSource.INFERRED,
            "responsible_department_id": None,
            "risk_if_ignored": "Non-compliance with court requirements" if req.get("is_mandatory") else "Unaddressed compliance requirement",
            "suggested_next_step": req.get("action_needed", "Take appropriate action"),
            "source_evidence": {
                "source_quote": req.get("source_quote", ""),
                "is_mandatory": req.get("is_mandatory", False),
                "confidence": req.get("confidence", 0.75)
            },
            "verification_status": VerificationStatus.PENDING,
            "completion_status": CompletionStatus.NOT_STARTED,
        }
    
    def _create_appeal_action_items(self, appeal_info: dict, judgment_date: date, db: Session) -> list[dict]:
        """Create action items for appeal considerations."""
        items = []
        
        if not appeal_info or not appeal_info.get("is_appealable"):
            return items
        
        limitation_days = appeal_info.get("limitation_period_days", 30)
        due_date = judgment_date + timedelta(days=limitation_days)
        
        items.append({
            "id": uuid.uuid4(),
            "document_id": None,
            "item_type": ActionType.APPEAL_CONSIDERATION,
            "title": "Consider filing appeal or revision petition",
            "description": f"Review judgment for appeal/revision options. Forum: {appeal_info.get('appeal_forum', 'Not specified')}",
            "priority": Priority.HIGH,
            "due_date": due_date,
            "due_date_source": DueDateSource.EXPLICIT_IN_JUDGMENT,
            "responsible_department_id": self._match_and_get_department("Ministry of Law and Justice", db).id,
            "risk_if_ignored": f"Appeal/revision window closes on {due_date.isoformat()}",
            "suggested_next_step": "Consult with legal counsel regarding appeal viability",
            "source_evidence": {
                "source_quote": appeal_info.get("source_quote", ""),
                "limitation_period_days": limitation_days,
                "confidence": appeal_info.get("confidence", 0.7)
            },
            "verification_status": VerificationStatus.PENDING,
            "completion_status": CompletionStatus.NOT_STARTED,
        })
        
        return items
    
    def _determine_action_type(self, description: str) -> ActionType:
        """
        Classify action type based on direction description.
        
        Rules:
        - "comply"/"implement"/"execute" → COMPLIANCE
        - "appeal"/"review petition"/"SLP" → APPEAL_CONSIDERATION
        - "examine"/"verify"/"check"/"audit" → INTERNAL_REVIEW
        - "report"/"escalate"/"refer"/"forward" → ESCALATION
        - "monitor"/"track"/"oversee" → MONITORING
        """
        description_lower = description.lower()
        
        if any(word in description_lower for word in ["appeal", "revision", "slp", "special leave", "writ"]):
            return ActionType.APPEAL_CONSIDERATION
        elif any(word in description_lower for word in ["examine", "verify", "check", "audit", "inspect", "review"]):
            return ActionType.INTERNAL_REVIEW
        elif any(word in description_lower for word in ["report", "escalate", "refer", "forward", "submit", "file"]):
            return ActionType.ESCALATION
        elif any(word in description_lower for word in ["monitor", "track", "oversee", "observe"]):
            return ActionType.MONITORING
        else:
            return ActionType.COMPLIANCE
    
    def _determine_priority(self, direction: dict, judgment_date: date) -> Priority:
        """
        Determine priority based on deadline and risk.
        
        Rules:
        - Deadline within 7 days → CRITICAL
        - "urgent"/"immediately"/"forthwith" → CRITICAL
        - Penalty risk HIGH/CRITICAL → CRITICAL
        - Deadline within 30 days → HIGH
        - Deadline within 90 days → MEDIUM
        """
        description = direction.get("description", "").lower()
        
        # Check for urgent language
        if any(word in description for word in ["urgent", "immediately", "forthwith", "at once"]):
            return Priority.CRITICAL
        
        # Check deadline
        deadline_days = direction.get("deadline_days")
        if deadline_days:
            if deadline_days <= 7:
                return Priority.CRITICAL
            elif deadline_days <= 30:
                return Priority.HIGH
            elif deadline_days <= 90:
                return Priority.MEDIUM
        
        # Default priority
        return Priority.MEDIUM
    
    def _calculate_due_date(self, direction: dict, judgment_date: date) -> Optional[date]:
        """
        Calculate due date from direction.
        
        Rules:
        - If explicit deadline_date → use it
        - If "within X days" → judgment_date + X days
        - If "forthwith"/"immediately" → judgment_date + 7 days
        - If "within X weeks" → judgment_date + X*7 days
        - If "within X months" → judgment_date + X*30 days
        """
        if direction.get("deadline_date"):
            try:
                return datetime.strptime(direction.get("deadline_date"), "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass
        
        description = direction.get("description", "").lower()
        
        # Check for relative dates
        import re
        
        # "within X days"
        match = re.search(r'within\s+(\d+)\s+days?', description)
        if match:
            days = int(match.group(1))
            return judgment_date + timedelta(days=days)
        
        # "forthwith" or "immediately"
        if any(word in description for word in ["forthwith", "immediately", "at once"]):
            return judgment_date + timedelta(days=7)
        
        # "within X weeks"
        match = re.search(r'within\s+(\d+)\s+weeks?', description)
        if match:
            weeks = int(match.group(1))
            return judgment_date + timedelta(weeks=weeks)
        
        # "within X months"
        match = re.search(r'within\s+(\d+)\s+months?', description)
        if match:
            months = int(match.group(1))
            return judgment_date + timedelta(days=months * 30)
        
        # Default: 30 days
        return judgment_date + timedelta(days=30)
    
    def _match_and_get_department(self, text: str, db: Session) -> Optional:
        """Match text to department and return Department object."""
        dept_name, score = self.department_matcher.match_responsible_entity(text)
        
        if not dept_name or score < 0.5:
            return None
        
        # Find or create department
        dept = db.query(Department).filter(Department.name == dept_name).first()
        return dept
    
    def _assess_risk(self, direction: dict, costs_info: dict) -> str:
        """
        Assess risk if direction is not complied with.
        
        Rules:
        - Contempt risk HIGH → mention contempt of court
        - Penalty risk HIGH → mention penalty amount
        - Costs awarded → mention costs
        - Mandatory direction without deadline → mention mandatory compliance
        """
        description = direction.get("description", "").lower()
        
        # Check for contempt language
        if "contempt" in description:
            return "Non-compliance may result in contempt of court proceedings"
        
        # Default risk message
        return "Non-compliance with court order may result in legal action against responsible department"
    
    def _action_item_to_dict(self, item: ActionPlanItem) -> dict:
        """Convert ActionPlanItem ORM object to dictionary."""
        return {
            "id": str(item.id),
            "item_type": item.item_type.value,
            "title": item.title,
            "description": item.description,
            "priority": item.priority.value,
            "due_date": item.due_date.isoformat() if item.due_date else None,
            "due_date_source": item.due_date_source.value,
            "responsible_department": item.responsible_department.name if item.responsible_department else None,
            "risk_if_ignored": item.risk_if_ignored,
            "suggested_next_step": item.suggested_next_step,
            "verification_status": item.verification_status.value,
            "completion_status": item.completion_status.value,
        }
