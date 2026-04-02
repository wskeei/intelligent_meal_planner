import json
from datetime import date

from intelligent_meal_planner.meal_chat.local_trace import MealChatTraceWriter


def test_trace_writer_appends_jsonl_events(tmp_path):
    writer = MealChatTraceWriter(base_dir=tmp_path)

    writer.write(
        session_id="session001",
        event="turn_processed",
        payload={
            "status": "collecting_preferences",
            "expected_slot": "restrictions",
        },
    )

    log_file = tmp_path / date.today().isoformat() / "session001.jsonl"
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    record = json.loads(lines[0])

    assert record["session_id"] == "session001"
    assert record["event"] == "turn_processed"
    assert record["payload"]["expected_slot"] == "restrictions"
