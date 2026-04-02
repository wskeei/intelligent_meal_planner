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


def test_parse_keeps_confidence_and_missing_fields():
    extractor = DeepSeekSlotExtractor.__new__(DeepSeekSlotExtractor)

    class FakeClient:
        def invoke(self, _messages):
            return SimpleNamespace(
                content='{"profile_updates": {}, "preference_updates": {"health_goal": "lose_weight"}, "acknowledged_restrictions": false, "confidence": 0.72, "missing_fields": ["budget", "unknown_field"]}'
            )

    extractor.client = FakeClient()

    parsed = extractor.parse("想减脂", expected_slot=None)

    assert parsed.confidence == 0.72
    assert parsed.missing_fields == ["budget"]


def test_parse_normalizes_confidence_missing_and_contradictions():
    extractor = DeepSeekSlotExtractor.__new__(DeepSeekSlotExtractor)

    class FakeClient:
        def invoke(self, _messages):
            return SimpleNamespace(
                content=(
                    '{"profile_updates": {}, "preference_updates": {"health_goal": "减脂"}, '
                    '"acknowledged_restrictions": false, "confidence": 0.66, '
                    '"missing_fields": ["budget"], "contradiction_fields": ["health_goal"]}'
                )
            )

    extractor.client = FakeClient()

    parsed = extractor.parse("最近想减脂，但预算还没想好", expected_slot=None)

    assert parsed.confidence == 0.66
    assert parsed.missing_fields == ["budget"]
    assert parsed.contradiction_fields == ["health_goal"]
