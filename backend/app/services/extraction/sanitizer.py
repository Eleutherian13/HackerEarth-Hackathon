"""
Extraction sanitization module.
Cleans and normalizes extracted field values.
"""

import logging
import re
import unicodedata
from typing import Any

logger = logging.getLogger(__name__)


class ExtractionSanitizer:
    """Sanitizes extracted field values for database storage."""
    
    def sanitize_extraction(self, extraction: dict) -> dict:
        """
        Clean all extracted values:
        - Remove null bytes
        - Normalize Unicode
        - Strip whitespace
        - Truncate long values
        - Remove HTML/XML tags
        - Escape dangerous characters
        
        Args:
            extraction: Raw extraction dictionary from Ollama
            
        Returns:
            Sanitized extraction dictionary
        """
        sanitized = {}
        
        # Sanitize case details
        case_details = extraction.get("case_details", {})
        sanitized["case_details"] = {}
        for key, value in case_details.items():
            if isinstance(value, dict):
                sanitized["case_details"][key] = {
                    "value": self.sanitize_string(str(value.get("value", "")), max_length=500),
                    "confidence": float(value.get("confidence", 0.5)),
                    "source_quote": self.sanitize_string(str(value.get("source_quote", "")), max_length=1000)
                }
        
        # Sanitize parties
        parties = extraction.get("parties", {})
        sanitized["parties"] = {
            "petitioners": [
                {"name": self.sanitize_string(p.get("name", ""), 200), "confidence": float(p.get("confidence", 0.7))}
                for p in parties.get("petitioners", [])
            ],
            "respondents": [
                {"name": self.sanitize_string(r.get("name", ""), 200), "confidence": float(r.get("confidence", 0.7))}
                for r in parties.get("respondents", [])
            ]
        }
        
        # Sanitize operative directions
        sanitized["operative_directions"] = []
        for direction in extraction.get("operative_directions", []):
            sanitized["operative_directions"].append({
                "direction_type": str(direction.get("direction_type", "MANDATORY_ORDER")).upper(),
                "description": self.sanitize_string(str(direction.get("description", "")), max_length=2000),
                "confidence": float(direction.get("confidence", 0.7)),
                "source_quote": self.sanitize_string(str(direction.get("source_quote", "")), max_length=1000),
                "deadline_days": direction.get("deadline_days"),
                "deadline_date": self.sanitize_date(direction.get("deadline_date")),
                "deadline_explicit": bool(direction.get("deadline_explicit", False)),
                "responsible_entity": self.sanitize_string(str(direction.get("responsible_entity", "")), max_length=200) if direction.get("responsible_entity") else None,
                "compliance_indicator": self.sanitize_string(str(direction.get("compliance_indicator", "")), max_length=1000)
            })
        
        # Sanitize deadlines
        sanitized["deadlines"] = []
        for deadline in extraction.get("deadlines", []):
            sanitized["deadlines"].append({
                "description": self.sanitize_string(str(deadline.get("description", "")), max_length=2000),
                "due_date": self.sanitize_date(deadline.get("due_date")),
                "timeframe_text": self.sanitize_string(str(deadline.get("timeframe_text", "")), max_length=500),
                "is_explicit": bool(deadline.get("is_explicit", False)),
                "confidence": float(deadline.get("confidence", 0.7)),
                "source_quote": self.sanitize_string(str(deadline.get("source_quote", "")), max_length=1000)
            })
        
        # Sanitize compliance requirements
        sanitized["compliance_requirements"] = []
        for req in extraction.get("compliance_requirements", []):
            sanitized["compliance_requirements"].append({
                "requirement": self.sanitize_string(str(req.get("requirement", "")), max_length=1000),
                "action_needed": self.sanitize_string(str(req.get("action_needed", "")), max_length=1000),
                "is_mandatory": bool(req.get("is_mandatory", True)),
                "confidence": float(req.get("confidence", 0.75)),
                "source_quote": self.sanitize_string(str(req.get("source_quote", "")), max_length=1000)
            })
        
        # Sanitize appeal indicators
        appeal_info = extraction.get("appeal_indicators", {})
        sanitized["appeal_indicators"] = {
            "is_appealable": bool(appeal_info.get("is_appealable", True)),
            "appeal_forum": self.sanitize_string(str(appeal_info.get("appeal_forum", "")), max_length=200) if appeal_info.get("appeal_forum") else None,
            "limitation_period_days": appeal_info.get("limitation_period_days"),
            "confidence": float(appeal_info.get("confidence", 0.7)),
            "source_quote": self.sanitize_string(str(appeal_info.get("source_quote", "")), max_length=1000)
        }
        
        # Sanitize costs and penalties
        costs_info = extraction.get("costs_and_penalties", {})
        sanitized["costs_and_penalties"] = {
            "costs_awarded": bool(costs_info.get("costs_awarded", False)),
            "amount": self.sanitize_string(str(costs_info.get("amount", "")), max_length=500) if costs_info.get("amount") else None,
            "penalty_risk": str(costs_info.get("penalty_risk", "NONE")).upper(),
            "contempt_risk": str(costs_info.get("contempt_risk", "NONE")).upper(),
            "source_quote": self.sanitize_string(str(costs_info.get("source_quote", "")), max_length=1000),
            "confidence": float(costs_info.get("confidence", 0.75))
        }
        
        return sanitized
    
    def sanitize_string(self, value: str, max_length: int = 5000) -> str:
        """
        Clean a single string value.
        
        Removes:
        - Null bytes
        - Control characters
        - HTML/XML tags
        - Excessive whitespace
        
        Normalizes:
        - Unicode characters
        - Whitespace
        
        Truncates to max_length if needed.
        
        Args:
            value: String to sanitize
            max_length: Maximum length allowed
            
        Returns:
            Sanitized string
        """
        if not value:
            return ""
        
        # Convert to string if needed
        value = str(value).strip()
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Remove control characters (except newline and tab)
        value = ''.join(char for char in value if unicodedata.category(char)[0] != 'C' or char in '\n\t\r')
        
        # Remove HTML/XML tags
        value = re.sub(r'<[^>]+>', '', value)
        
        # Normalize Unicode (decompose combined characters)
        value = unicodedata.normalize('NFKD', value)
        
        # Remove multiple consecutive whitespace
        value = re.sub(r'\s+', ' ', value)
        
        # Strip again after normalization
        value = value.strip()
        
        # Truncate if needed
        if len(value) > max_length:
            value = value[:max_length].rstrip() + "..."
        
        return value
    
    def sanitize_date(self, value: Any) -> str | None:
        """
        Sanitize date value.
        Ensures it's in YYYY-MM-DD format.
        
        Args:
            value: Date string to sanitize
            
        Returns:
            Sanitized date in YYYY-MM-DD format or None
        """
        if not value or value == "NOT_FOUND_IN_TEXT":
            return None
        
        value_str = str(value).strip()
        
        # If already in YYYY-MM-DD format, return as is
        if re.match(r'^\d{4}-\d{2}-\d{2}$', value_str):
            return value_str
        
        # Try to normalize to YYYY-MM-DD
        # Handle DD-MM-YYYY or DD/MM/YYYY
        match = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$', value_str)
        if match:
            day, month, year = match.groups()
            return f"{year}-{month:0>2}-{day:0>2}"
        
        # Handle YYYY/MM/DD
        match = re.match(r'^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$', value_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month:0>2}-{day:0>2}"
        
        # If we can't parse it, return None
        logger.warning(f"Could not normalize date: {value_str}")
        return None
    
    def sanitize_confidence(self, value: Any) -> float:
        """
        Sanitize confidence score.
        Must be between 0.0 and 1.0.
        
        Args:
            value: Confidence value
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            confidence = float(value)
            if confidence < 0.0:
                return 0.0
            elif confidence > 1.0:
                return 1.0
            return confidence
        except (ValueError, TypeError):
            logger.warning(f"Invalid confidence score: {value}")
            return 0.5
