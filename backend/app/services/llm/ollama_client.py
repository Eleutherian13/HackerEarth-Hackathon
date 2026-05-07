"""Ollama LLM Client - Complete local LLM integration with httpx"""

import json
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import get_logger
from datetime import datetime

logger = get_logger(__name__)

# Load configuration from settings
OLLAMA_BASE_URL = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = getattr(settings, 'OLLAMA_MODEL', 'llama3.2')
OLLAMA_TIMEOUT = getattr(settings, 'OLLAMA_TIMEOUT', 120)
OLLAMA_TEMPERATURE = getattr(settings, 'OLLAMA_TEMPERATURE', 0.0)
OLLAMA_MAX_TOKENS = getattr(settings, 'OLLAMA_MAX_TOKENS', 4096)

# ─── EXTRACTION PROMPT ──────────────────────────

EXTRACTION_SYSTEM_PROMPT = """You are a legal document analyzer for Indian court judgments.
Extract structured information from the judgment text.

Output ONLY valid JSON with this exact structure - no explanations, no markdown:
{
  "case_details": {
    "case_number": "extracted value or NOT_FOUND",
    "case_title": "extracted value or NOT_FOUND",
    "court_name": "extracted value or NOT_FOUND",
    "judgment_date": "YYYY-MM-DD or NOT_FOUND"
  },
  "parties": {
    "petitioners": ["name1", "name2"],
    "respondents": ["name1", "name2"]
  },
  "operative_directions": ["direction 1", "direction 2"],
  "deadlines": ["deadline description"],
  "compliance_requirements": ["requirement 1", "requirement 2"]
}"""


class OllamaClientError(Exception):
    """Exception raised when Ollama client encounters an error."""
    pass


class OllamaClient:
    """Complete Ollama client for legal document processing"""
    
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.timeout = OLLAMA_TIMEOUT
        
        if not self._check_connection():
            logger.warning(f"Cannot connect to Ollama at {self.base_url}")
    
    def _check_connection(self) -> bool:
        """Check if Ollama is running and model exists"""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    model_names = [m.get('name', '') for m in models]
                    
                    if self.model in model_names or any(self.model in m for m in model_names):
                        logger.info(f"✓ Ollama connected. Model available: {self.model}")
                        return True
                    else:
                        logger.warning(f"Model {self.model} not found. Available: {model_names}")
                        return False
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
            return False
    
    def generate(self, prompt: str, system_prompt: str = None, 
                 temperature: float = 0.0, max_tokens: int = 4096) -> Dict[str, Any]:
        """Generate response from Ollama synchronously"""
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                logger.info(f"Sending request to Ollama ({self.model})...")
                
                response = client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"Ollama error: {response.status_code}")
                    raise RuntimeError(f"Ollama generation failed: {response.text[:500]}")
                
                result = response.json()
                output = result.get("response", "")
                
                logger.info(f"Ollama response received ({len(output)} chars)")
                
                return {
                    "content": output,
                    "metadata": {
                        "model": self.model,
                        "tokens_generated": result.get("eval_count", 0)
                    }
                }
                
        except httpx.TimeoutException:
            logger.error("Ollama timeout")
            raise RuntimeError("Ollama generation timed out")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise
    
    def extract_from_judgment(self, document_text: str) -> Dict:
        """
        Extract structured fields from a court judgment.
        This is a wrapper for backward compatibility.
        
        Returns format: flat string values
        """
        result = self.extract_fields(document_text, page_count=1)
        return result
    
    def extract_fields(self, document_text: str, page_count: int = 1) -> Dict:
        """
        Extract structured fields from a court judgment.
        MAIN extraction function - returns properly formatted data.
        
        Args:
            document_text: Combined text from all document pages
            page_count: Total number of pages (for reference)
            
        Returns:
            Dictionary with structured fields matching extractor expectations:
            {
                "case_details": {
                    "case_number": {"value": "...", "confidence": 0.9, ...},
                    "case_title": {"value": "...", "confidence": 0.85, ...},
                    ...
                },
                "parties": {
                    "petitioners": [{"value": "...", "confidence": 0.9}, ...],
                    "respondents": [...]
                },
                "operative_directions": [{"description": "...", "confidence": 0.8, ...}],
                "deadlines": [{"due_date": "...", "confidence": 0.85, ...}],
                "compliance_requirements": [{"requirement": "...", "confidence": 0.8, ...}],
                "appeal_indicators": {...},
                "costs_and_penalties": {...}
            }
        """
        
        logger.info("Starting legal field extraction from judgment text...")
        logger.info(f"Document length: {len(document_text)} characters, {page_count} pages")
        
        # Trim extremely long documents to fit context
        max_chars = 8000
        if len(document_text) > max_chars:
            logger.info(f"Trimming document from {len(document_text)} to {max_chars} chars")
            first_part = document_text[:max_chars // 2]
            last_part = document_text[-(max_chars // 2):]
            document_text = first_part + "\n...[middle section omitted]...\n" + last_part
        
        extraction_prompt = f"""Extract STRUCTURED legal information from this Indian court judgment.

COURT JUDGMENT TEXT:
{document_text}

CRITICAL INSTRUCTIONS:
1. Output ONLY valid JSON - no explanations, no markdown
2. For each field, include both the value AND confidence (0.0-1.0)
3. For strings: always wrap in {{\"value\": \"...\", \"confidence\": 0.X}}
4. For lists: use {{\"description\": \"...\", \"confidence\": 0.X}} format
5. Use \"NOT_FOUND\" if field cannot be extracted
6. Confidence: Use 0.9+ for clear extractions, 0.6-0.8 for inferred, <0.6 for uncertain

JSON STRUCTURE:
{{
  "case_details": {{
    "case_number": {{"value": "extracted_value", "confidence": 0.9, "source_quote": "..."}},
    "case_title": {{"value": "extracted_value", "confidence": 0.85, "source_quote": "..."}},
    "court_name": {{"value": "extracted_value", "confidence": 0.9, "source_quote": "..."}},
    "judgment_date": {{"value": "YYYY-MM-DD", "confidence": 0.95, "source_quote": "..."}}
  }},
  "parties": {{
    "petitioners": [{{"value": "name1", "confidence": 0.95, "role": "..."}}],
    "respondents": [{{"value": "name1", "confidence": 0.95, "role": "..."}}]
  }},
  "operative_directions": [{{
    "description": "detailed directive",
    "confidence": 0.85,
    "source_quote": "...",
    "deadline_days": 30,
    "deadline_date": "YYYY-MM-DD"
  }}],
  "deadlines": [{{
    "due_date": "YYYY-MM-DD",
    "confidence": 0.9,
    "source_quote": "...",
    "timeframe_text": "30 days from",
    "is_explicit": true
  }}],
  "compliance_requirements": [{{
    "requirement": "what must be done",
    "confidence": 0.8,
    "source_quote": "...",
    "action_needed": "specific action",
    "is_mandatory": true
  }}],
  "appeal_indicators": {{
    "is_appealable": true,
    "confidence": 0.75,
    "appeal_forum": "High Court/Supreme Court",
    "limitation_period_days": 30,
    "source_quote": "..."
  }},
  "costs_and_penalties": {{
    "costs_awarded": false,
    "confidence": 0.8,
    "amount": "amount_if_any",
    "penalty_risk": "NONE/LOW/MEDIUM/HIGH",
    "contempt_risk": "NONE/LOW/MEDIUM/HIGH",
    "source_quote": "..."
  }}
}}

Extract now:"""
        
        try:
            result = self.generate(
                prompt=extraction_prompt,
                system_prompt=EXTRACTION_SYSTEM_PROMPT,
                temperature=OLLAMA_TEMPERATURE,
                max_tokens=OLLAMA_MAX_TOKENS
            )
            
            # Parse JSON from response
            content = result['content'].strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                lines = content.split('\n')
                lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                content = '\n'.join(lines)
            
            # Try to parse JSON
            try:
                extraction = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Ollama: {e}")
                logger.debug(f"Raw output: {content[:500]}")
                # Return fallback structure
                extraction = self._get_fallback_extraction()
            
            # Add metadata
            extraction['_metadata'] = {
                'model': self.model,
                'extraction_timestamp': str(datetime.now()),
                'document_length_chars': len(document_text),
                'page_count': page_count,
                'tokens_generated': result['metadata'].get('tokens_generated', 0),
                'parser': 'ollama_extract_fields'
            }
            
            logger.info("✓ Field extraction completed successfully")
            return extraction
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise
    
    def _get_fallback_extraction(self) -> Dict:
        """Return fallback extraction structure when parsing fails."""
        return {
            "case_details": {
                "case_number": {"value": "NOT_FOUND", "confidence": 0.0},
                "case_title": {"value": "NOT_FOUND", "confidence": 0.0},
                "court_name": {"value": "NOT_FOUND", "confidence": 0.0},
                "judgment_date": {"value": "NOT_FOUND", "confidence": 0.0}
            },
            "parties": {
                "petitioners": [],
                "respondents": []
            },
            "operative_directions": [],
            "deadlines": [],
            "compliance_requirements": [],
            "appeal_indicators": {
                "is_appealable": False,
                "confidence": 0.0
            },
            "costs_and_penalties": {
                "costs_awarded": False,
                "confidence": 0.0
            }
        }
    
    def health_check(self) -> dict:
        """Check Ollama health"""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                models = response.json().get('models', [])
                return {
                    "status": "healthy",
                    "ollama_url": self.base_url,
                    "model": self.model,
                    "model_available": any(self.model in m.get('name', '') for m in models),
                    "available_models": [m.get('name', '') for m in models[:5]]
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Singleton
_ollama_client = None

def get_ollama_client() -> OllamaClient:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client
