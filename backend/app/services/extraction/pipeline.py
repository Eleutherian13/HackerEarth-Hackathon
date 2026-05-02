from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from typing import Any

from app.core.config import settings
from app.models.domain.models import Document, DocumentPage, ExtractedField
from app.models.enums import (
    ExtractionMethod,
    FieldType,
    JobStatus,
    JobType,
    ProcessingStatus,
    VerificationStatus,
)
from app.services.extraction.confidence import confidence_from_evidence, normalize_confidence, rule_based_confidence
from app.services.extraction.llm_client import LLMClient, LLMClientError
from app.services.extraction.prompts import build_extraction_prompt
from app.services.extraction.validators import validate_extraction_schema

MAX_PROMPT_CHARACTERS = 24000


class ExtractionPipelineError(Exception):
    """Raised when structured extraction fails."""


def _safe_json_load(raw_text: str) -> dict[str, Any]:
    cleaned = re.sub(r"```(?:json)?", "", raw_text, flags=re.IGNORECASE).strip()
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first >= 0 and last >= 0 and last > first:
        cleaned = cleaned[first:last + 1]
    return json.loads(cleaned)


def _assemble_document_text(pages: list[DocumentPage]) -> str:
    document_chunks: list[str] = []
    for page in pages:
        page_text = page.raw_text or page.ocr_text or ""
        if not page_text:
            continue
        document_chunks.append(f"--- PAGE {page.page_number} ---\n{page_text}")
    joined = "\n\n".join(document_chunks)
    if len(joined) > MAX_PROMPT_CHARACTERS:
        joined = joined[:MAX_PROMPT_CHARACTERS] + "\n\n[TRUNCATED CONTENT]"
    return joined


def _extract_schema_with_llm(document_text: str) -> dict[str, Any]:
    try:
        raw_output = LLMClient.call_model(build_extraction_prompt(document_text))
        return _safe_json_load(raw_output)
    except LLMClientError:
        raise
    except Exception as exc:
        raise ExtractionPipelineError(f"LLM extraction failed: {str(exc)}")


def _heuristic_fallback_schema(document_text: str) -> dict[str, Any]:
    lines = [line.strip() for line in document_text.splitlines() if line.strip()]
    joined = "\n".join(lines)

    case_number_match = re.search(r"\b[A-Z]{1,5}[\w\-/() ]*\d{1,4}/\d{4}\b", joined)
    judgment_date_match = re.search(r"\b\d{1,2}[\-/\. ]\d{1,2}[\-/\. ]\d{4}\b", joined)
    court_name_match = next((court for court in [
        "Supreme Court",
        "High Court",
        "Court of Appeal",
        "District Court",
        "Family Court",
    ] if court in joined), None)
    petitioner_match = re.search(r"Petitioner[s]*\s*[:\-]\s*([^\n]+)", joined, re.IGNORECASE)
    respondent_match = re.search(r"Respondent[s]*\s*[:\-]\s*([^\n]+)", joined, re.IGNORECASE)

    return {
        "case_details": {
            "case_number": {
                "value": case_number_match.group(0).strip() if case_number_match else None,
                "confidence": 0.85 if case_number_match else 0.0,
                "source_quote": case_number_match.group(0).strip() if case_number_match else "",
                "page": 1,
            },
            "case_title": {
                "value": None,
                "confidence": 0.0,
                "source_quote": "",
                "page": 1,
            },
            "court_name": {
                "value": court_name_match,
                "confidence": 0.8 if court_name_match else 0.0,
                "source_quote": court_name_match or "",
                "page": 1,
            },
            "judgment_date": {
                "value": judgment_date_match.group(0).strip() if judgment_date_match else None,
                "confidence": 0.8 if judgment_date_match else 0.0,
                "source_quote": judgment_date_match.group(0).strip() if judgment_date_match else "",
                "page": 1,
            },
            "judge_bench": {
                "value": None,
                "confidence": 0.0,
                "source_quote": "",
                "page": 1,
            },
        },
        "parties": {
            "petitioners": [
                {
                    "name": petitioner_match.group(1).strip() if petitioner_match else "",
                    "confidence": 0.7 if petitioner_match else 0.0,
                }
            ] if petitioner_match else [],
            "respondents": [
                {
                    "name": respondent_match.group(1).strip() if respondent_match else "",
                    "confidence": 0.7 if respondent_match else 0.0,
                }
            ] if respondent_match else [],
            "counsel": [],
        },
        "operative_directions": [],
        "deadlines": [],
        "compliance_requirements": [],
        "appeal_indicators": {
            "is_appealable": False,
            "appeal_forum": None,
            "limitation_period_days": None,
            "confidence": 0.0,
            "source_quote": "",
            "page": 1,
            "is_inferred": False,
            "inference_rationale": None,
        },
        "costs_and_penalties": {
            "costs_awarded": False,
            "amount": None,
            "penalty_risk": "NONE",
            "contempt_risk": "NONE",
            "source_quote": "",
            "confidence": 0.0,
        },
    }


def _get_source_quote(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": item.get("source_quote") or item.get("quote") or str(item.get("value") or ""),
        "page": item.get("page") or 1,
        "bbox": item.get("highlight_coordinates") if item.get("highlight_coordinates") else None,
    }


def _build_extracted_fields(schema: dict[str, Any], pages: list[DocumentPage]) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []

    details = schema.get("case_details", {})
    if details:
        for key, field_type in [
            ("case_number", FieldType.CASE_NUMBER),
            ("case_title", FieldType.CASE_TITLE),
            ("court_name", FieldType.COURT_NAME),
            ("judgment_date", FieldType.JUDGMENT_DATE),
            ("judge_bench", FieldType.BENCH_INFO),
        ]:
            entry = details.get(key, {})
            value = (entry.get("value") or "").strip()
            if value:
                fields.append(
                    {
                        "field_type": field_type,
                        "value": value,
                        "normalized_value": value,
                        "confidence_score": normalize_confidence(entry.get("confidence", 0.6)),
                        "is_inferred": bool(entry.get("value") and bool(entry.get("source_quote") is False)),
                        "inference_rationale": None,
                        "source_page_ids": [entry.get("page")] if entry.get("page") else [],
                        "source_quotes": [_get_source_quote(entry)],
                    }
                )

    parties = schema.get("parties", {})
    petitioners = parties.get("petitioners", [])
    respondents = parties.get("respondents", [])
    if petitioners or respondents:
        summary_items: list[str] = []
        for petitioner in petitioners:
            name = (petitioner.get("name") or "").strip()
            if name:
                fields.append(
                    {
                        "field_type": FieldType.PETITIONER,
                        "value": name,
                        "normalized_value": name,
                        "confidence_score": normalize_confidence(petitioner.get("confidence", 0.6)),
                        "is_inferred": False,
                        "inference_rationale": None,
                        "source_page_ids": [],
                        "source_quotes": [],
                    }
                )
                summary_items.append(f"Petitioner: {name}")
        for respondent in respondents:
            name = (respondent.get("name") or "").strip()
            if name:
                fields.append(
                    {
                        "field_type": FieldType.RESPONDENT,
                        "value": name,
                        "normalized_value": name,
                        "confidence_score": normalize_confidence(respondent.get("confidence", 0.6)),
                        "is_inferred": False,
                        "inference_rationale": None,
                        "source_page_ids": [],
                        "source_quotes": [],
                    }
                )
                summary_items.append(f"Respondent: {name}")
        if summary_items:
            fields.append(
                {
                    "field_type": FieldType.PARTIES,
                    "value": "; ".join(summary_items),
                    "normalized_value": "; ".join(summary_items),
                    "confidence_score": 0.8,
                    "is_inferred": False,
                    "inference_rationale": None,
                    "source_page_ids": [],
                    "source_quotes": [],
                }
            )

    for item in schema.get("operative_directions", []):
        description = (item.get("description") or "").strip()
        if not description:
            continue
        quote = _get_source_quote(item)
        fields.append(
            {
                "field_type": FieldType.OPERATIVE_DIRECTION,
                "value": description,
                "normalized_value": description,
                "confidence_score": normalize_confidence(item.get("confidence", 0.65)),
                "is_inferred": item.get("is_inferred", False),
                "inference_rationale": item.get("inference_rationale"),
                "source_page_ids": [quote["page"]] if quote["page"] else [],
                "source_quotes": [quote],
            }
        )

    for item in schema.get("deadlines", []):
        description = (item.get("description") or "").strip()
        if not description:
            continue
        quote = _get_source_quote(item)
        value = description
        if item.get("due_date"):
            value = f"{description} (due {item.get('due_date')})"
        fields.append(
            {
                "field_type": FieldType.DEADLINE,
                "value": value,
                "normalized_value": value,
                "confidence_score": normalize_confidence(item.get("confidence", 0.65)),
                "is_inferred": item.get("is_inferred", False),
                "inference_rationale": item.get("inference_rationale"),
                "source_page_ids": [quote["page"]] if quote["page"] else [],
                "source_quotes": [quote],
            }
        )

    compliance_items = schema.get("compliance_requirements", [])
    if compliance_items:
        for item in compliance_items:
            requirement = (item.get("requirement") or "").strip()
            if not requirement:
                continue
            quote = _get_source_quote(item)
            fields.append(
                {
                    "field_type": FieldType.COMPLIANCE_OBLIGATION,
                    "value": requirement,
                    "normalized_value": requirement,
                    "confidence_score": normalize_confidence(item.get("confidence", 0.65)),
                    "is_inferred": item.get("is_inferred", False),
                    "inference_rationale": item.get("inference_rationale"),
                    "source_page_ids": [quote["page"]] if quote["page"] else [],
                    "source_quotes": [quote],
                }
            )

    appeal = schema.get("appeal_indicators", {})
    if appeal:
        value = "Appealable" if appeal.get("is_appealable") else "Not appealable"
        if appeal.get("appeal_forum"):
            value = f"{value} via {appeal.get('appeal_forum')}"
        if appeal.get("limitation_period_days") is not None:
            value = f"{value}; limitation period {appeal.get('limitation_period_days')} days"
        quote = _get_source_quote(appeal)
        fields.append(
            {
                "field_type": FieldType.APPEAL_CLUE,
                "value": value,
                "normalized_value": value,
                "confidence_score": normalize_confidence(appeal.get("confidence", 0.65)),
                "is_inferred": appeal.get("is_inferred", False),
                "inference_rationale": appeal.get("inference_rationale"),
                "source_page_ids": [quote["page"]] if quote["page"] else [],
                "source_quotes": [quote],
            }
        )

    costs = schema.get("costs_and_penalties", {})
    if costs:
        summary = []
        if costs.get("costs_awarded"):
            summary.append("Costs awarded")
        if costs.get("amount"):
            summary.append(f"Amount: {costs.get('amount')}")
        summary.append(f"Penalty risk: {costs.get('penalty_risk')}")
        summary.append(f"Contempt risk: {costs.get('contempt_risk')}")
        quote = _get_source_quote(costs)
        fields.append(
            {
                "field_type": FieldType.COST_ORDER,
                "value": "; ".join(summary),
                "normalized_value": "; ".join(summary),
                "confidence_score": normalize_confidence(costs.get("confidence", 0.6)),
                "is_inferred": False,
                "inference_rationale": None,
                "source_page_ids": [quote["page"]] if quote["page"] else [],
                "source_quotes": [quote],
            }
        )
        fields.append(
            {
                "field_type": FieldType.PENALTY_RISK,
                "value": costs.get("penalty_risk", "NONE"),
                "normalized_value": costs.get("penalty_risk", "NONE"),
                "confidence_score": normalize_confidence(costs.get("confidence", 0.6)),
                "is_inferred": False,
                "inference_rationale": None,
                "source_page_ids": [quote["page"]] if quote["page"] else [],
                "source_quotes": [quote],
            }
        )

    return fields


def _create_field_record(db: Any, document: Document, payload: dict[str, Any]) -> ExtractedField:
    field = ExtractedField(
        id=uuid.uuid4(),
        document_id=document.id,
        field_type=payload["field_type"],
        value=payload["value"],
        normalized_value=payload.get("normalized_value"),
        confidence_score=payload["confidence_score"],
        extraction_method=ExtractionMethod.LLM_INFERRED,
        is_inferred=payload.get("is_inferred", False),
        inference_rationale=payload.get("inference_rationale"),
        source_page_ids=payload.get("source_page_ids", []),
        source_quotes=payload.get("source_quotes", []),
        verification_status=VerificationStatus.UNVERIFIED,
        verified_by_user_id=None,
        verified_at=None,
        edit_history=[],
        reviewer_comments=None,
    )
    db.add(field)
    return field


def perform_structured_extraction(db: Any, document: Document, pages: list[DocumentPage]) -> dict[str, Any] | None:
    if not pages:
        raise ExtractionPipelineError("No document pages available for structured extraction")

    document_text = _assemble_document_text(pages)
    try:
        schema = _extract_schema_with_llm(document_text)
        validate_extraction_schema(schema)
    except Exception:
        schema = _heuristic_fallback_schema(document_text)

    extracted_fields = _build_extracted_fields(schema, pages)
    if not extracted_fields:
        raise ExtractionPipelineError("Structured extraction returned no fields")

    # Remove any previous extracted fields so reprocessing remains idempotent.
    db.query(ExtractedField).filter(ExtractedField.document_id == document.id).delete(synchronize_session=False)
    db.flush()

    created = 0
    for payload in extracted_fields:
        _create_field_record(db, document, payload)
        created += 1

    db.commit()
    return {
        "fields_created": created,
        "extraction_method": ExtractionMethod.LLM_INFERRED.value,
        "confidence_average": sum(item["confidence_score"] for item in extracted_fields) / max(created, 1),
    }
