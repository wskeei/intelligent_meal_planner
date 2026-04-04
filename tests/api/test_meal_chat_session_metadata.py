def test_create_session_includes_metadata_fields(client, auth_header):
    response = client.post("/api/meal-chat/sessions", headers=auth_header)

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "discovering"
    assert "open_questions" in payload
    assert "known_facts" in payload
    assert "follow_up_plan" in payload
    assert "profile_snapshot" in payload
    assert "preferences_snapshot" in payload
    assert "negotiation_options" in payload

    assert isinstance(payload["open_questions"], list)
    assert isinstance(payload["known_facts"], dict)
    assert payload["follow_up_plan"] is None
    assert isinstance(payload["profile_snapshot"], dict)
    assert isinstance(payload["preferences_snapshot"], dict)
    assert payload["negotiation_options"] == []


def test_create_session_respects_english_locale(client, auth_header):
    response = client.post(
        "/api/meal-chat/sessions",
        headers={**auth_header, "Accept-Language": "en-US,en;q=0.9"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert (
        payload["messages"][0]["content"]
        == "I will first confirm your goal, budget, and food preferences, then organize a realistic daily meal plan within budget."
    )


def test_post_message_session_includes_memory_metadata(
    client, auth_header, monkeypatch
):
    class FakeOrchestrator:
        def advance(self, user, session, user_message: str):
            session.collected_slots = {
                "phase": "discovering",
                "profile": {
                    "gender": "male",
                    "age": 24,
                    "height": 175,
                    "weight": 68,
                    "activity_level": "moderate",
                },
                "preferences": {
                    "health_goal": "lose_weight",
                    "budget": 100.0,
                    "preferred_tags": ["高蛋白"],
                },
                "known_facts": {"budget": 100.0, "health_goal": "lose_weight"},
                "open_questions": ["你更偏好米饭还是面食？"],
                "follow_up_plan": {
                    "questions": ["你更偏好米饭还是面食？"],
                    "assistant_message": "我再确认一下主食偏好。",
                },
                "negotiation_options": [
                    {
                        "key": "budget_cut",
                        "title": "优先控预算",
                        "rationale": "先保证预算可行",
                        "budget": 100.0,
                        "preferred_tags": ["高蛋白"],
                    }
                ],
                "crew_events": [],
            }
            return {
                "status": "discovering",
                "assistant_message": "我再确认一下主食偏好。",
                "meal_plan": None,
                "trace": {},
            }

    monkeypatch.setattr(
        "intelligent_meal_planner.api.services.meal_chat_app._orchestrator",
        FakeOrchestrator(),
    )

    create_response = client.post("/api/meal-chat/sessions", headers=auth_header)
    session_id = create_response.json()["session_id"]
    response = client.post(
        f"/api/meal-chat/sessions/{session_id}/messages",
        headers=auth_header,
        json={"content": "预算 100 元，想减脂"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "discovering"
    assert payload["open_questions"] == ["你更偏好米饭还是面食？"]
    assert payload["known_facts"]["budget"] == 100.0
    assert payload["known_facts"]["health_goal"] == "lose_weight"
    assert (
        payload["follow_up_plan"]["assistant_message"] == "我再确认一下主食偏好。"
    )
    assert payload["profile_snapshot"]["age"] == 24
    assert payload["preferences_snapshot"]["budget"] == 100.0
    assert payload["negotiation_options"][0]["key"] == "budget_cut"
