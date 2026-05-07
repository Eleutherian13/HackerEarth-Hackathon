"""
Extraction validation module.
Validates extracted fields from Ollama for quality and completeness.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of extraction validation."""
    is_valid: bool
    errors: list[str]
    warnings: list[str]


class ExtractionValidator:
    """Validates extracted fields from Ollama."""
    
    def validate_extraction(self, extraction: dict) -> ValidationResult:
        """
        Validate extracted fields.
        
        Checks:
        - Case number matches Indian court format
        - Dates are parseable and in reasonable range
        - Confidence scores are 0.0-1.0
        - Source quotes are not empty
        - Required fields present
        
        Args:
            extraction: Extraction dictionary from Ollama
            
        Returns:
            ValidationResult with is_valid flag and error messages
        """
        errors = []
        warnings = []
        
        try:
            # Validate case details
            case_details = extraction.get("case_details", {})
            
            case_number = case_details.get("case_number", {}).get("value", "")
            if case_number and case_number != "NOT_FOUND_IN_TEXT":
                if not self.validate_case_number(case_number):
                    warnings.append(f"Case number format unusual: {case_number}")
            else:
                errors.append("Case number is required but not found")
            
            court_name = case_details.get("court_name", {}).get("value", "")
            if not court_name or court_name == "NOT_FOUND_IN_TEXT":
                errors.append("Court name is required")
            
            judgment_date = case_details.get("judgment_date", {}).get("value", "")
            if judgment_date and judgment_date != "NOT_FOUND_IN_TEXT":
                if not self.validate_date(judgment_date):
                    errors.append(f"Invalid judgment date format: {judgment_date}")
            else:
                warnings.append("Judgment date not found")
            
            # Validate confidence scores
            for field_type, field_data in case_details.items():
                if isinstance(field_data, dict):
                    confidence = field_data.get("confidence", 0)
                    if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                        errors.append(f"Invalid confidence score for {field_type}: {confidence}")
                    
                    # Check for source quote on high-confidence fields
                    source_quote = field_data.get("source_quote", "")
                    if confidence > 0.8 and not source_quote:
                        warnings.append(f"High confidence {field_type} lacks source quote")
            
            # Validate operative directions
            for direction in extraction.get("operative_directions", []):
                if direction.get("deadline_explicit") and not direction.get("deadline_date"):
                    warnings.append("Explicit deadline marked but no deadline_date provided")
                
                confidence = direction.get("confidence", 0)
                if not (0 <= confidence <= 1):
                    errors.append(f"Invalid confidence for operative direction: {confidence}")
            
            # Validate deadlines
            for deadline in extraction.get("deadlines", []):
                due_date = deadline.get("due_date", "")
                if due_date and not self.validate_date(due_date):
                    errors.append(f"Invalid deadline date format: {due_date}")
            
            # Determine validity
            is_valid = len(errors) == 0
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings
            )
        
        except Exception as e:
            logger.error(f"Validation error: {e}", exc_info=True)
            return ValidationResult(
                is_valid=False,
                errors=[str(e)],
                warnings=[]
            )
    
    def validate_case_number(self, value: str) -> bool:
        """
        Validate case number format.
        
        Matches patterns:
        - WP(C) 1234/2024
        - Crl.A. 567/2024
        - SLP 8901/2024
        - CA 123/2024
        - Civil 456/2024
        
        Args:
            value: Case number string
            
        Returns:
            True if valid format, False otherwise
        """
        patterns = [
            r'^(?:WP|Crl\.A|SLP|CA|Civil|Crim)\s*(?:\(C\))?\s*(?:No\.|\#)?\s*(\d+/\d{4})$',
            r'^\d+/\d{4}$',  # Generic number/year pattern
        ]
        
        value_normalized = value.strip()
        for pattern in patterns:
            if re.match(pattern, value_normalized, re.IGNORECASE):
                return True
        
        return False
    
    def validate_date(self, value: str) -> bool:
        """
        Parse and validate date.
        Must be between 1950 and current year+1.
        
        Accepts formats:
        - YYYY-MM-DD
        - DD-MM-YYYY
        - DD/MM/YYYY
        
        Args:
            value: Date string
            
        Returns:
            True if valid date in reasonable range, False otherwise
        """
        if not value or value == "NOT_FOUND_IN_TEXT":
            return False
        
        value_clean = value.strip()
        
        # Try parsing different formats
        formats = [
            ('%Y-%m-%d', 'YYYY-MM-DD'),
            ('%d-%m-%Y', 'DD-MM-YYYY'),
            ('%d/%m/%Y', 'DD/MM/YYYY'),
            ('%d %m %Y', 'DD MM YYYY'),
            ('%d.%m.%Y', 'DD.MM.YYYY'),
        ]
        
        for date_format, _ in formats:
            try:
                parsed_date = datetime.strptime(value_clean, date_format)
                
                # Check if date is in reasonable range (1950 to current year + 1)
                current_year = datetime.now().year
                if 1950 <= parsed_date.year <= current_year + 1:
                    return True
            except ValueError:
                continue
        
        return False
    
    def validate_extracted_fields_count(self, extraction: dict, min_fields: int = 3) -> bool:
        """
        Validate that extraction has minimum number of meaningful fields.
        
        Args:
            extraction: Extraction dictionary
            min_fields: Minimum required number of fields
            
        Returns:
            True if extraction has enough fields
        """
        field_count = 0
        
        # Count case details
        case_details = extraction.get("case_details", {})
        for key, value in case_details.items():
            if isinstance(value, dict) and value.get("value") != "NOT_FOUND_IN_TEXT":
                field_count += 1
        
        # Count operative directions
        field_count += len(extraction.get("operative_directions", []))
        
        # Count deadlines
        field_count += len(extraction.get("deadlines", []))
        
        return field_count >= min_fields
