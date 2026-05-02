from __future__ import annotations

from typing import Optional


def normalize_confidence(value: float) -> float:
    return max(0.0, min(1.0, value))


def confidence_from_evidence(
    direct_quote: bool = False,
    standard_phrase: bool = False,
    inferred: bool = False,
    ambiguity: Optional[float] = None,
) -> float:
    if direct_quote:
        score = 0.97
    elif standard_phrase:
        score = 0.90
    elif inferred:
        score = 0.78
    else:
        score = 0.60

    if ambiguity is not None:
        score = score - ambiguity

    return normalize_confidence(score)


def rule_based_confidence(source_quote: str, field_type: str, explicit: bool = False) -> float:
    quote = source_quote.lower()
    if explicit and any(keyword in quote for keyword in ['ordered', 'directed', 'shall', 'must', 'is required']):
        return normalize_confidence(0.96)
    if any(keyword in quote for keyword in ['may', 'should', 'recommend', 'advise']):
        return normalize_confidence(0.82)
    if any(keyword in quote for keyword in ['is appealed', 'appealable', 'appeal']):
        return normalize_confidence(0.88)
    return normalize_confidence(0.75)


def confidence_range_label(score: float) -> str:
    score = normalize_confidence(score)
    if score >= 0.95:
        return 'Direct quote'
    if score >= 0.85:
        return 'High confidence'
    if score >= 0.70:
        return 'Medium confidence'
    if score >= 0.50:
        return 'Low confidence'
    return 'Review required'
