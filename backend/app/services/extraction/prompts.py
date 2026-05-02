from __future__ import annotations

STRUCTURE_STAGE_PROMPT = '''
You are analyzing a court judgment document. First, identify key structural elements with their page locations.
Return your findings in JSON format with section names and page numbers only.

Focus on these sections:
- Case heading and case details
- Court name and bench information
- Judgment date and order dates
- Parties and counsel sections
- Operative directions, orders, and conclusions
- Deadlines, compliance, and appeal information
- Costs, penalties, and contempt references

Do NOT infer missing values. Use only the text provided.
'''

EXTRACTION_STAGE_PROMPT = '''
From the identified sections, extract the following fields into structured JSON.
For every field, provide the exact quote from the text that supports the extraction, including page number and coordinates when available.

Fields:
- case_number
- case_title
- court_name
- judgment_date
- judge_bench
- petitioners
- respondents
- counsel
- operative_directions
- deadlines
- compliance_requirements
- appeal_indicators
- costs_and_penalties

Use only the text present in the document. If a field is not found, set its value to null or an empty list as appropriate.
'''

DIRECTION_ANALYSIS_PROMPT = '''
Analyze all operative directions from the judgment text.
For each direction, determine:
- whether it is mandatory or advisory
- whether there is an explicit deadline
- who is responsible for acting
- what consequences are stated for non-compliance

Output each direction as a JSON object with fields: direction_type, description, confidence, source_quote, page, deadline_days, deadline_date, deadline_explicit, responsible_entity, compliance_indicator.
If the direction is ambiguous, set is_inferred=true and include inference_rationale.
'''

LEGAL_ASSESSMENT_PROMPT = '''
Based ONLY on what is explicitly stated in the judgment text, assess the following:
- appealability
- appeal forum or jurisdiction
- any limitation period in days
- risk levels for costs or contempt

Do not use any external legal knowledge. If information is not explicitly found in the text, set values to "NOT_FOUND_IN_TEXT" or null where appropriate.
'''

FULL_EXTRACTION_PROMPT = '''
Stage 1: Identify structure
{structure_stage}

Stage 2: Extract details
{extraction_stage}

Stage 3: Direction analysis
{direction_stage}

Stage 4: Legal assessment
{legal_stage}
'''.format(
    structure_stage=STRUCTURE_STAGE_PROMPT,
    extraction_stage=EXTRACTION_STAGE_PROMPT,
    direction_stage=DIRECTION_ANALYSIS_PROMPT,
    legal_stage=LEGAL_ASSESSMENT_PROMPT,
)

def build_extraction_prompt(document_text: str) -> str:
    return f"{FULL_EXTRACTION_PROMPT}\n\nDocument text:\n{document_text}"
