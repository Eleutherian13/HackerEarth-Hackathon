from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

CASE_NUMBER_PATTERN = re.compile(r'^[A-Za-z]+[-/\s]\d+[/-]\d{4}$')
KNOWN_COURTS = {
    'Supreme Court',
    'High Court',
    'Court of Appeal',
    'District Court',
    'Family Court',
}

DATE_FORMATS = [
    '%d %B %Y',
    '%d %b %Y',
    '%Y-%m-%d',
    '%d/%m/%Y',
    '%m/%d/%Y',
    '%d.%m.%Y',
]


def parse_date(value: str) -> Optional[datetime]:
    normalized = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue

    match = re.search(r'(?P<day>\d{1,2})[\-/\.\s](?P<month>\d{1,2})[\-/\.\s](?P<year>\d{4})', normalized)
    if match:
        try:
            return datetime(
                int(match.group('year')),
                int(match.group('month')),
                int(match.group('day')),
            )
        except ValueError:
            return None

    return None


def validate_case_number(case_number: str) -> bool:
    return bool(case_number and CASE_NUMBER_PATTERN.match(case_number.strip()))


def validate_date_string(value: str) -> bool:
    date = parse_date(value)
    if not date:
        return False
    return 1900 <= date.year <= datetime.utcnow().year


def validate_deadline_date(deadline_date: Optional[str], deadline_explicit: bool) -> bool:
    if deadline_explicit and not deadline_date:
        return False
    if deadline_date:
        return validate_date_string(deadline_date)
    return True


def validate_court_name(court_name: str) -> bool:
    if not court_name:
        return False
    return court_name in KNOWN_COURTS or len(court_name) > 3


def validate_direction(direction: dict) -> bool:
    if direction.get('deadline_explicit') and not direction.get('deadline_date'):
        return False
    if direction.get('direction_type') not in {'MANDATORY_ORDER', 'DIRECTIVE', 'OBSERVATION', 'DECLARATION'}:
        return False
    if not direction.get('description'):
        return False
    return True


def validate_extraction_schema(schema: dict) -> None:
    if not schema.get('case_details'):
        raise ValueError('Missing case_details')

    case_number = schema['case_details'].get('case_number', {}).get('value')
    if case_number and not validate_case_number(case_number):
        raise ValueError('Invalid case number format')

    judgment_date = schema['case_details'].get('judgment_date', {}).get('value')
    if judgment_date and not validate_date_string(judgment_date):
        raise ValueError('Invalid judgment date')

    for direction in schema.get('operative_directions', []):
        if not validate_direction(direction):
            raise ValueError('Invalid operative direction definition')

    for deadline in schema.get('deadlines', []):
        if not validate_deadline_date(deadline.get('due_date'), deadline.get('is_explicit')):
            raise ValueError('Invalid deadline definition')
