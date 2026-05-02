"""
Input validation module providing defense-in-depth validation for API endpoints.

Includes validators for:
- Case numbers (Indian court formats)
- Dates and date ranges
- Email domains (government email validation)
- Search queries (injection prevention)
- File sizes and types
- Text input (XSS prevention)
- Pagination parameters
- UUID formats
"""

import re
from datetime import datetime
from typing import Optional

import dateutil.parser


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class InputValidator:
    """Comprehensive input validation utilities."""

    # Government email domains (configurable via environment)
    ALLOWED_EMAIL_DOMAINS = {
        "nic.in",
        "gov.in",
        "mailbox.nic.in",
        "meity.gov.in",
        "dopt.gov.in",
        "agmis.nic.in",
        "judiciary.nic.in",
    }

    @staticmethod
    def validate_case_number(value: str) -> bool:
        """
        Validate case number format for Indian courts.
        
        Supported formats:
        - WP(C) 1234/2024
        - CIVIL APPEAL NO. 1234/2024
        - SLP 12345/2024
        - Crl.A. 123/2024
        
        Args:
            value: Case number string
            
        Returns:
            True if valid, False otherwise
        """
        if not value or not isinstance(value, str):
            return False
        
        patterns = [
            r'^[A-Z]+[\s/-]*\(?[A-Z]?\)?\s*\d+[\s/-]\d{4}$',  # WP(C) 1234/2024
            r'^[A-Z\s]+NO\.?\s*\d+[\s/]*\d{4}$',  # CIVIL APPEAL NO. 1234/2024
            r'^[A-Z]+\.?[A-Z]?\.?\s*\d+[\s/]\d{4}$',  # SLP 12345/2024
            r'^[A-Z]+\s*\d+[\s/]\d{4}$',  # General format
        ]
        
        return any(re.match(p, value.strip(), re.IGNORECASE) for p in patterns)

    @staticmethod
    def validate_date_range(date_str: str, min_year: int = 1900, allow_future: bool = True) -> bool:
        """
        Validate date is parseable and within reasonable range.
        
        Args:
            date_str: Date string to parse
            min_year: Minimum year allowed (default 1900)
            allow_future: Whether to allow dates in the future (default True)
            
        Returns:
            True if valid date, False otherwise
        """
        try:
            parsed = dateutil.parser.parse(date_str)
            max_year = datetime.now().year + (1 if allow_future else 0)
            return min_year <= parsed.year <= max_year
        except (ValueError, TypeError, AttributeError):
            return False

    @staticmethod
    def validate_email_domain(email: str, allowed_domains: Optional[set] = None) -> bool:
        """
        Validate email domain against whitelist.
        
        Args:
            email: Email address to validate
            allowed_domains: Set of allowed domains (uses default if None)
            
        Returns:
            True if domain is in allowed list, False otherwise
        """
        if not email or "@" not in email:
            return False
        
        domains = allowed_domains or InputValidator.ALLOWED_EMAIL_DOMAINS
        try:
            domain = email.split("@")[1].lower()
            return domain in domains
        except (IndexError, AttributeError):
            return False

    @staticmethod
    def sanitize_search_query(query: str, max_length: int = 200) -> str:
        """
        Sanitize search query to prevent injection attacks.
        
        Removes SQL wildcards, special characters, and enforces length limits.
        
        Args:
            query: Raw search query
            max_length: Maximum allowed length (default 200)
            
        Returns:
            Cleaned search query
        """
        if not query:
            return ""
        
        # Remove potentially dangerous characters for SQL/NoSQL injection
        # Keep: alphanumeric, spaces, common punctuation (-, ., ,)
        cleaned = re.sub(r'[^\w\s\-.,]', '', query)
        
        # Limit length
        cleaned = cleaned[:max_length].strip()
        
        # Remove multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned

    @staticmethod
    def validate_file_size(size: int, max_mb: int = 50) -> bool:
        """
        Validate file size is within limits.
        
        Args:
            size: File size in bytes
            max_mb: Maximum size in megabytes (default 50)
            
        Returns:
            True if size is valid, False otherwise
        """
        max_bytes = max_mb * 1024 * 1024
        return 0 < size <= max_bytes

    @staticmethod
    def validate_page_number(page: int, total_pages: int) -> bool:
        """
        Validate page number is within document range.
        
        Args:
            page: Page number to validate
            total_pages: Total number of pages in document
            
        Returns:
            True if page number is valid, False otherwise
        """
        return isinstance(page, int) and 1 <= page <= max(total_pages, 1)

    @staticmethod
    def validate_pagination(page: int, per_page: int, max_per_page: int = 100) -> bool:
        """
        Validate pagination parameters.
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            max_per_page: Maximum items per page (default 100)
            
        Returns:
            True if pagination parameters are valid, False otherwise
        """
        return (
            isinstance(page, int)
            and isinstance(per_page, int)
            and page >= 1
            and 1 <= per_page <= max_per_page
        )

    @staticmethod
    def validate_sort_column(column: str, allowed_columns: list[str]) -> bool:
        """
        Validate sort column name against whitelist.
        
        Prevents SQL injection via sort parameters.
        
        Args:
            column: Column name to validate
            allowed_columns: List of allowed column names
            
        Returns:
            True if column is in allowed list, False otherwise
        """
        return column in allowed_columns

    @staticmethod
    def validate_sort_order(order: str) -> bool:
        """
        Validate sort order parameter.
        
        Args:
            order: Sort order string (should be "ASC" or "DESC")
            
        Returns:
            True if valid order, False otherwise
        """
        return order.upper() in {"ASC", "DESC"}

    @staticmethod
    def validate_no_html_script(text: str) -> bool:
        """
        Check if text contains HTML/script tags (XSS prevention).
        
        Args:
            text: Text to check
            
        Returns:
            False if HTML/script tags detected, True otherwise
        """
        if not text:
            return True
        
        dangerous_patterns = [
            r'<script[^>]*>',
            r'<iframe[^>]*>',
            r'javascript:',
            r'onerror=',
            r'onload=',
            r'onclick=',
            r'<object[^>]*>',
            r'<embed[^>]*>',
        ]
        
        text_lower = text.lower()
        return not any(re.search(p, text_lower, re.IGNORECASE) for p in dangerous_patterns)

    @staticmethod
    def validate_text_length(text: str, min_length: int = 0, max_length: int = 2000) -> bool:
        """
        Validate text is within length bounds.
        
        Args:
            text: Text to validate
            min_length: Minimum length (default 0)
            max_length: Maximum length (default 2000)
            
        Returns:
            True if length is valid, False otherwise
        """
        if text is None:
            return min_length == 0
        
        length = len(str(text))
        return min_length <= length <= max_length

    @staticmethod
    def validate_filename(filename: str, max_length: int = 500) -> bool:
        """
        Validate filename to prevent path traversal and length issues.
        
        Args:
            filename: Filename to validate
            max_length: Maximum filename length (default 500)
            
        Returns:
            True if filename is valid, False otherwise
        """
        if not filename or len(filename) > max_length:
            return False
        
        # Check for path traversal attempts
        if ".." in filename or "/" in filename or "\\" in filename:
            return False
        
        # Check for null bytes
        if "\x00" in filename:
            return False
        
        return True

    @staticmethod
    def validate_mime_type(mime_type: str, allowed_types: set[str]) -> bool:
        """
        Validate MIME type against whitelist.
        
        Args:
            mime_type: MIME type to validate
            allowed_types: Set of allowed MIME types
            
        Returns:
            True if MIME type is allowed, False otherwise
        """
        if not mime_type:
            return False
        
        # Handle charset and other parameters
        base_type = mime_type.split(";")[0].strip().lower()
        return base_type in allowed_types

    @staticmethod
    def validate_password_strength(password: str, min_length: int = 12) -> tuple[bool, str]:
        """
        Validate password meets security requirements.
        
        Args:
            password: Password to validate
            min_length: Minimum password length (default 12)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"
        
        if len(password) < min_length:
            return False, f"Password must be at least {min_length} characters"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain lowercase letters"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain uppercase letters"
        
        if not re.search(r'\d', password):
            return False, "Password must contain numbers"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain special characters (!@#$%^&* etc)"
        
        return True, ""

    @staticmethod
    def sanitize_text(text: str, remove_html: bool = True) -> str:
        """
        Basic text sanitization (removes/escapes problematic content).
        
        Args:
            text: Text to sanitize
            remove_html: Whether to remove HTML tags (default True)
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        if remove_html:
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', text)
        
        # Escape special characters
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#x27;")
        
        return text

    @staticmethod
    def validate_uuid_format(value: str) -> bool:
        """
        Validate UUID format.
        
        Args:
            value: String to validate as UUID
            
        Returns:
            True if valid UUID format, False otherwise
        """
        if not value or not isinstance(value, str):
            return False
        
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, value.lower()))

    @staticmethod
    def validate_role(role: str, allowed_roles: set[str]) -> bool:
        """
        Validate user role against allowed list.
        
        Args:
            role: Role to validate
            allowed_roles: Set of allowed roles
            
        Returns:
            True if role is allowed, False otherwise
        """
        return role in allowed_roles


class FieldValidator:
    """Validators for specific field types."""

    @staticmethod
    def validate_case_details(details: dict) -> tuple[bool, list[str]]:
        """
        Validate case details structure.
        
        Args:
            details: Dictionary of case details
            
        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []
        
        if not isinstance(details, dict):
            errors.append("case_details must be a dictionary")
            return False, errors
        
        # Check required fields
        if "case_number" in details and details["case_number"]:
            if not InputValidator.validate_case_number(details["case_number"]):
                errors.append("Invalid case number format")
        
        if "date_of_judgment" in details and details["date_of_judgment"]:
            if not InputValidator.validate_date_range(details["date_of_judgment"]):
                errors.append("Invalid judgment date")
        
        return len(errors) == 0, errors

    @staticmethod
    def validate_parties(parties: list) -> tuple[bool, list[str]]:
        """
        Validate parties structure.
        
        Args:
            parties: List of party objects
            
        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []
        
        if not isinstance(parties, list):
            errors.append("parties must be a list")
            return False, errors
        
        if not parties:
            errors.append("At least one party is required")
            return False, errors
        
        for i, party in enumerate(parties):
            if not isinstance(party, dict):
                errors.append(f"Party {i} must be a dictionary")
            elif "name" not in party or not party["name"]:
                errors.append(f"Party {i} must have a name")
        
        return len(errors) == 0, errors
