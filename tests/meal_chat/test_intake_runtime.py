from intelligent_meal_planner.meal_chat.intake_runtime import IntakeRuntime
from intelligent_meal_planner.meal_chat.session_schema import ConversationMemory


def test_intake_runtime_keeps_asking_until_required_fields_are_complete():
    runtime = IntakeRuntime(extractor=None)
    memory = ConversationMemory(phase="discovering")

    result = runtime.run_turn("我最近想减脂", memory)

    assert result.phase == "discovering"
    assert result.ready_for_crew is False
    assert "预算" in result.assistant_message
