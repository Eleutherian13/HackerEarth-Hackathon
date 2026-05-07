"""Text cleaner - removes headers, footers, and noise from extracted text"""

import re
from app.core.logging import get_logger

logger = get_logger(__name__)

class TextCleaner:
    def __init__(self):
        self.header_patterns = [
            re.compile(r'^\s*Page\s+\d+\s+of\s+\d+\s*$', re.IGNORECASE),
            re.compile(r'^\s*\d+\s*$'),  # Standalone page number
            re.compile(r'^\s*IN THE .{5,50}\s*$', re.IGNORECASE),
        ]
        
        self.footer_patterns = [
            re.compile(r'\s*Page\s+\d+\s*$', re.IGNORECASE),
            re.compile(r'\s*Downloaded on\s*:.*$', re.IGNORECASE),
        ]
    
    def clean_text(self, raw_text: str, page_number: int, total_pages: int = None) -> str:
        """Clean extracted text"""
        if not raw_text:
            return ""
        
        cleaned = raw_text
        
        # Remove headers
        for pattern in self.header_patterns:
            cleaned = pattern.sub('', cleaned)
        
        # Remove footers
        for pattern in self.footer_patterns:
            cleaned = pattern.sub('', cleaned)
        
        # Remove repeated blank lines
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        
        # Strip
        cleaned = cleaned.strip()
        
        return cleaned
