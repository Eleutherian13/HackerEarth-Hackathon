import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from app.models.enums import ActionType, Priority
from app.services.action_plan.appeal_handler import extract_appeal_items
from app.services.action_plan.quality_checks import validate_action_plan_items
from app.services.action_plan.rule_engine import derive_action_plan_items

FIXTURE_PATH = Path(__file__).resolve().parent.parent / 'fixtures' / 'expected_action_plan.json'


def build_field(field_id: str, field_type: str, value: str, quote_text: str, page: int):
    return SimpleNamespace(
        id=field_id,
        field_type=SimpleNamespace(name=field_type, value=field_type),
        normalized_value=value,
        value=value,
        source_quotes=[{'text': quote_text, 'page': page}],
        source_page_ids=[page],
    )


def test_generate_action_plan_items_matches_fixture():
    fields = [
        build_field(
            'field-1',
            'OPERATIVE_DIRECTION',
            'Submit compliance report within 14 days.',
            'Submit compliance report',
            2,
        ),
        build_field(
            'field-2',
            'APPEAL_CLUE',
            'Appealable via High Court; limitation period 15 days.',
            'Appealable via High Court; limitation period 15 days',
            5,
        ),
        build_field(
            'field-3',
            'JUDGMENT_DATE',
            '2025-12-31',
            'Dated 31 December 2025',
            1,
        ),
    ]

    plan_items = derive_action_plan_items(fields)
    plan_items.extend(extract_appeal_items(fields))

    fixture = json.loads(FIXTURE_PATH.read_text())
    assert len(plan_items) == len(fixture)

    first_item = plan_items[0]
    assert first_item['item_type'] == ActionType.COMPLIANCE
    assert first_item['priority'] == Priority.HIGH
    assert first_item['due_date'] == date(2026, 1, 14)
    assert first_item['source_evidence']['field_ids'] == ['field-1']

    second_item = plan_items[1]
    assert second_item['item_type'] == ActionType.APPEAL_CONSIDERATION
    assert second_item['priority'] == Priority.HIGH
    assert second_item['source_evidence']['field_ids'] == ['field-2']

    warnings = validate_action_plan_items(plan_items)
    assert isinstance(warnings, list)
    assert len(warnings) == 0
