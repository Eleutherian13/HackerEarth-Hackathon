"""
Department matcher for action plan item assignment.
Maps extracted entities and keywords to government departments.
"""

import logging
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class DepartmentMatcher:
    """
    Matches text to Indian government departments.
    Uses keyword matching and pattern analysis.
    """
    
    # Comprehensive keyword mapping for Indian government departments
    DEPARTMENT_KEYWORDS = {
        "Ministry of Law and Justice": [
            "law department", "legal affairs", "solicitor general", "attorney general",
            "advocate general", "ministry of law", "law ministry", "legal opinion",
            "government counsel", "standing counsel", "justice", "judicial", "court",
            "legal", "legislation", "constitutional", "supreme court", "high court"
        ],
        "Department of Revenue": [
            "revenue department", "income tax", "tax department", "customs", "excise",
            "gst", "goods and services tax", "cbdt", "cbic", "enforcement directorate",
            "financial", "economic affairs", "tax", "tariff", "duties", "assessment"
        ],
        "Ministry of Home Affairs": [
            "home department", "home ministry", "mha", "internal security", "police",
            "law and order", "cbi", "nia", "intelligence bureau", "national security",
            "public order", "safety", "security", "investigation", "border", "terrorism"
        ],
        "Ministry of Health and Family Welfare": [
            "health department", "medical", "hospital", "pharmacy", "drug controller",
            "public health", "clinical establishment", "food and drug administration",
            "wellness", "disease", "vaccination", "epidemiology", "healthcare", "patient"
        ],
        "Ministry of Education": [
            "education department", "school", "university", "college", "ugc", "aicte",
            "cbse", "kendriya vidyalaya", "navodaya vidyalaya", "learning", "student",
            "faculty", "curriculum", "examination", "grant", "scholarship", "institution"
        ],
        "Ministry of Environment, Forest and Climate Change": [
            "environment", "forest", "wildlife", "pollution", "ngt", "cpcb", "spcb",
            "environmental clearance", "climate change", "biodiversity", "conservation",
            "sustainability", "emissions", "air quality", "water quality", "protected area"
        ],
        "Ministry of Labour and Employment": [
            "labour department", "labor department", "employment", "worker", "trade union",
            "industrial dispute", "minimum wage", "epf", "esi", "factory", "workplace",
            "wages", "working conditions", "occupational safety", "skill development"
        ],
        "Ministry of Finance": [
            "finance department", "ministry of finance", "economic affairs", "expenditure",
            "financial services", "banking", "insurance", "pension", "fiscal", "budget",
            "audit", "accounts", "payment", "monetary", "economic"
        ],
        "Ministry of Road Transport and Highways": [
            "road transport", "highways", "motor vehicles", "national highways authority",
            "nhai", "transport department", "vehicles", "traffic", "vehicle registration",
            "driving", "road safety", "transportation"
        ],
        "Ministry of Railways": [
            "railways", "railway board", "railway ministry", "railway department", "railway",
            "train", "station", "rail network", "passenger", "freight"
        ],
        "Ministry of External Affairs": [
            "external affairs", "foreign ministry", "diplomacy", "ambassador", "consulate",
            "embassy", "international relations", "foreign policy", "bilateral", "treaty"
        ],
        "Ministry of Commerce and Industry": [
            "commerce", "industry", "trade", "exports", "imports", "business", "investment",
            "market", "commercial", "industrial policy", "sector", "enterprise"
        ],
        "Ministry of Information and Broadcasting": [
            "information", "broadcasting", "media", "press", "publication", "news",
            "entertainment", "cinema", "television", "digital", "communication"
        ],
        "Ministry of Defence": [
            "defence", "defense", "military", "armed forces", "security forces", "army",
            "navy", "air force", "war", "combat", "defence acquisition"
        ],
        "Ministry of Agricultural and Farmers Welfare": [
            "agriculture", "farming", "farmer", "crop", "irrigation", "soil", "farming",
            "agricultural", "seeds", "fertilizer", "pesticide", "agricultural extension"
        ],
    }
    
    def match_department(self, text: str) -> Tuple[Optional[str], float]:
        """
        Match text against department keywords.
        
        Args:
            text: Text to match (usually extracted entity or description)
            
        Returns:
            Tuple of (department_name, confidence) or (None, 0.0)
        """
        if not text or not text.strip():
            return None, 0.0
        
        text_lower = text.lower().strip()
        best_match = None
        best_score = 0.0
        
        for dept_name, keywords in self.DEPARTMENT_KEYWORDS.items():
            for keyword in keywords:
                # Exact keyword match gets high score
                if keyword == text_lower:
                    return dept_name, 0.95
                
                # Substring match
                if keyword in text_lower:
                    score = len(keyword) / len(text_lower)  # Longer keyword match = higher score
                    if score > best_score:
                        best_score = score
                        best_match = dept_name
            
            # Also check if any keyword appears in text
            keyword_matches = sum(1 for kw in keywords if kw in text_lower)
            if keyword_matches > 0:
                # Multiple keyword matches increase confidence
                score = min(0.85, 0.6 + (keyword_matches * 0.1))
                if score > best_score:
                    best_score = score
                    best_match = dept_name
        
        return best_match, best_score if best_score >= 0.4 else 0.0
    
    def get_all_departments(self) -> list[str]:
        """
        Get list of all known departments.
        
        Returns:
            List of department names
        """
        return list(self.DEPARTMENT_KEYWORDS.keys())
    
    def match_responsible_entity(self, entity_text: str) -> Tuple[Optional[str], float]:
        """
        Match responsible entity text to department.
        Handles variations like "Ministry of Law", "Law Ministry", "Law Dept", etc.
        
        Args:
            entity_text: Responsible entity text from extraction
            
        Returns:
            Tuple of (department_name, confidence) or (None, 0.0)
        """
        if not entity_text:
            return None, 0.0
        
        # First try direct match
        dept, score = self.match_department(entity_text)
        if score >= 0.7:
            return dept, score
        
        # Try normalizing "Ministry of X" or "X Ministry" patterns
        text_normalized = entity_text.lower().strip()
        
        # Remove common prefixes/suffixes
        text_normalized = re.sub(r'^(ministry of|department of|the|state|union)\s+', '', text_normalized)
        text_normalized = re.sub(r'\s+(ministry|department|govt|government|office)$', '', text_normalized)
        
        # Try again with normalized text
        if text_normalized != entity_text.lower():
            dept, score = self.match_department(text_normalized)
            if score >= 0.6:
                return dept, score
        
        # If still no match, try partial matching
        for keyword_pair in entity_text.lower().split():
            dept, score = self.match_department(keyword_pair)
            if score >= 0.8:
                return dept, score
        
        return None, 0.0
    
    def suggest_departments(self, text: str, limit: int = 3) -> list[Tuple[str, float]]:
        """
        Suggest top N departments for text.
        
        Args:
            text: Text to match
            limit: Maximum number of suggestions
            
        Returns:
            List of (department_name, confidence) tuples, sorted by confidence descending
        """
        if not text or not text.strip():
            return []
        
        text_lower = text.lower()
        scores = {}
        
        for dept_name, keywords in self.DEPARTMENT_KEYWORDS.items():
            max_score = 0.0
            for keyword in keywords:
                if keyword in text_lower:
                    score = len(keyword) / len(text_lower)
                    max_score = max(max_score, score)
            
            if max_score > 0:
                scores[dept_name] = max_score
        
        # Sort by score descending
        sorted_depts = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Filter by minimum confidence and return top N
        return [(dept, score) for dept, score in sorted_depts[:limit] if score >= 0.4]


# Singleton instance
_matcher_instance = None


def get_department_matcher() -> DepartmentMatcher:
    """Get or create department matcher singleton."""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = DepartmentMatcher()
    return _matcher_instance
