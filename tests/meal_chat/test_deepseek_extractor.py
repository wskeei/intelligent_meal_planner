from types import SimpleNamespace

from intelligent_meal_planner.meal_chat.deepseek_extractor import DeepSeekSlotExtractor


def test_parse_marks_empty_restrictions_reply_as_answered():
    extractor = DeepSeekSlotExtractor.__new__(DeepSeekSlotExtractor)

    class FakeClient:
        def invoke(self, _messages):
            return SimpleNamespace(
                content='{"profile_updates": {}, "preference_updates": {}, "acknowledged_restrictions": false}'
            )

    extractor.client = FakeClient()

    parsed = extractor.parse("没有，都能吃", expected_slot="restrictions")

    assert parsed.acknowledged_restrictions is True
    assert parsed.preference_updates["disliked_foods"] == []


def test_parse_moves_budget_answer_into_preference_updates_when_expected_slot_is_budget():
    extractor = DeepSeekSlotExtractor.__new__(DeepSeekSlotExtractor)

    class FakeClient:
        def invoke(self, _messages):
            return SimpleNamespace(
                content='{"profile_updates": {"budget": "100元"}, "preference_updates": {}, "acknowledged_restrictions": false}'
            )

    extractor.client = FakeClient()

    parsed = extractor.parse("100元吧", expected_slot="budget")

    assert "budget" not in parsed.profile_updates
    assert parsed.preference_updates["budget"] == 100.0


def test_parse_marks_empty_taste_reply_as_answered():
    extractor = DeepSeekSlotExtractor.__new__(DeepSeekSlotExtractor)

    class FakeClient:
        def invoke(self, _messages):
            return SimpleNamespace(
                content='{"profile_updates": {}, "preference_updates": {}, "acknowledged_restrictions": false}'
            )

    extractor.client = FakeClient()

    parsed = extractor.parse("都行", expected_slot="taste")

    assert parsed.preference_updates["preferred_tags"] == []
