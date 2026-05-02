from datetime import date
from types import SimpleNamespace

from app.services.action_plan.rule_engine import derive_action_plan_items
from app.models.enums import ActionType, Priority


class TestActionPlanRuleEngine:
    def test_derive_action_plan_items_from_compliance_field(self):
        field = SimpleNamespace(
            id='field-1',
            field_type=SimpleNamespace(name='COMPLIANCE_OBLIGATION', value='COMPLIANCE_OBLIGATION'),
            normalized_value='2026-01-15',
            value='Ensure compliance with the order by the deadline.',
            source_quotes=[{'text': 'Submit compliance report', 'page': 2}],
            source_page_ids=[2],
        )

        items = derive_action_plan_items([field])

        assert len(items) == 1
        item = items[0]
        assert item['item_type'] == ActionType.COMPLIANCE
        assert item['priority'] == Priority.HIGH
        assert item['title'].startswith('Review Compliance Obligation')
        assert item['due_date'] == date(2026, 1, 15)
        assert item['source_evidence']['quotes'][0]['text'] == 'Submit compliance report'

    def test_derive_action_plan_items_from_appeal_clue(self):
        field = SimpleNamespace(
            id='field-2',
            field_type=SimpleNamespace(name='APPEAL_CLUE', value='APPEAL_CLUE'),
            normalized_value=None,
            value='Possible grounds for appeal are present in the findings.',
            source_quotes=[{'text': 'grounds for appeal', 'page': 5}],
            source_page_ids=[5],
        )

        items = derive_action_plan_items([field])

        assert len(items) == 1
        item = items[0]
        assert item['item_type'] == ActionType.APPEAL_CONSIDERATION
        assert item['priority'] == Priority.MEDIUM
        assert item['description'].startswith('Review the judgment')
        assert item['source_evidence']['field_type'] == 'APPEAL_CLUE'
