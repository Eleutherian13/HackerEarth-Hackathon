from __future__ import annotations

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal

class HighlightCoordinates(BaseModel):
    x: float
    y: float
    width: float
    height: float

class SourceQuote(BaseModel):
    value: str = Field(..., description="Exact excerpt from the document text")
    page: int = Field(..., description="Page number where the quote appears")
    highlight_coordinates: Optional[HighlightCoordinates] = Field(
        None,
        description="Optional PDF highlight coordinates for preview rendering",
    )

class CaseDetailItem(BaseModel):
    value: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_quote: Optional[str] = None
    page: Optional[int] = None

class PartyName(BaseModel):
    name: str
    confidence: float = Field(..., ge=0.0, le=1.0)

class CounselEntry(BaseModel):
    name: str
    party: str
    confidence: float = Field(..., ge=0.0, le=1.0)

class OperativeDirection(BaseModel):
    direction_type: Literal['MANDATORY_ORDER', 'DIRECTIVE', 'OBSERVATION', 'DECLARATION']
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_quote: str
    page: int
    deadline_days: Optional[int] = None
    deadline_date: Optional[str] = None
    deadline_explicit: bool
    responsible_entity: Optional[str] = None
    compliance_indicator: Optional[str] = None
    is_inferred: bool = False
    inference_rationale: Optional[str] = None
    highlight_coordinates: Optional[HighlightCoordinates] = None

class DeadlineEntry(BaseModel):
    description: str
    due_date: Optional[str] = None
    timeframe: str
    is_explicit: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_quote: str
    page: int
    is_inferred: bool = False
    inference_rationale: Optional[str] = None

class ComplianceRequirement(BaseModel):
    requirement: str
    action_needed: str
    is_mandatory: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_quote: str
    page: int
    is_inferred: bool = False
    inference_rationale: Optional[str] = None

class AppealIndicators(BaseModel):
    is_appealable: bool
    appeal_forum: Optional[str] = None
    limitation_period_days: Optional[int] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_quote: str
    page: int
    is_inferred: bool = False
    inference_rationale: Optional[str] = None

class CostsAndPenalties(BaseModel):
    costs_awarded: bool
    amount: Optional[str] = None
    penalty_risk: Literal['NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    contempt_risk: Literal['NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    source_quote: str
    confidence: float = Field(..., ge=0.0, le=1.0)

class Parties(BaseModel):
    petitioners: List[PartyName] = Field(default_factory=list)
    respondents: List[PartyName] = Field(default_factory=list)
    counsel: List[CounselEntry] = Field(default_factory=list)

class ExtractionSchema(BaseModel):
    case_details: dict[str, CaseDetailItem]
    parties: Parties
    operative_directions: List[OperativeDirection] = Field(default_factory=list)
    deadlines: List[DeadlineEntry] = Field(default_factory=list)
    compliance_requirements: List[ComplianceRequirement] = Field(default_factory=list)
    appeal_indicators: AppealIndicators
    costs_and_penalties: CostsAndPenalties

    @validator('case_details')
    def require_case_detail_keys(cls, value):
        expected_keys = {
            'case_number',
            'case_title',
            'court_name',
            'judgment_date',
            'judge_bench',
        }
        missing = expected_keys - set(value.keys())
        if missing:
            raise ValueError(f'Missing case detail fields: {sorted(missing)}')
        return value
