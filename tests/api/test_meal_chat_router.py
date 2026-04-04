def test_create_session_returns_first_assistant_message(
    client, auth_header, monkeypatch
):
    fake_response = {
        "session_id": "session001",
        "status": "discovering",
        "messages": [
            {
                "role": "assistant",
                "content": "我会先了解你的目标、预算和口味偏好。",
            }
        ],
        "meal_plan": None,
    }
    monkeypatch.setattr(
        "intelligent_meal_planner.api.routers.meal_chat.meal_chat_app.start_session",
        lambda db, user: fake_response,
    )

    response = client.post("/api/meal-chat/sessions", headers=auth_header)

    assert response.status_code == 200
    assert response.json()["status"] == "discovering"


def test_send_message_accepts_negotiating_status(client, auth_header, monkeypatch):
    fake_response = {
        "session_id": "session001",
        "status": "negotiating",
        "messages": [
            {
                "role": "assistant",
                "content": "当前预算偏紧，我先给你两个方向。",
            }
        ],
        "meal_plan": None,
    }
    monkeypatch.setattr(
        "intelligent_meal_planner.api.routers.meal_chat.meal_chat_app.handle_message",
        lambda db, user, session_id, content: fake_response,
    )

    response = client.post(
        "/api/meal-chat/sessions/session001/messages",
        headers=auth_header,
        json={"content": "预算 100 元"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "negotiating"


def test_send_message_accepts_discovering_clarification_status(
    client, auth_header, monkeypatch
):
    fake_response = {
        "session_id": "session001",
        "status": "discovering",
        "messages": [
            {
                "role": "assistant",
                "content": "我先确认一下预算，这样后面的方案会更准。",
            }
        ],
        "meal_plan": None,
    }
    monkeypatch.setattr(
        "intelligent_meal_planner.api.routers.meal_chat.meal_chat_app.handle_message",
        lambda db, user, session_id, content: fake_response,
    )

    response = client.post(
        "/api/meal-chat/sessions/session001/messages",
        headers=auth_header,
        json={"content": "最近想减脂"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "discovering"


def test_send_message_accepts_dual_plan_payload(client, auth_header, monkeypatch):
    fake_response = {
        "session_id": "session001",
        "status": "finalized",
        "messages": [
            {
                "role": "assistant",
                "content": "我给你整理了两套方案。",
            }
        ],
        "meal_plan": {
            "primary": {
                "id": "plan001",
                "created_at": "2026-04-02T10:00:00",
                "meals": [],
                "nutrition": {
                    "total_calories": 1800,
                    "total_protein": 120,
                    "total_carbs": 180,
                    "total_fat": 55,
                    "total_price": 120,
                    "calories_achievement": 100,
                    "protein_achievement": 100,
                    "budget_usage": 100,
                },
                "target": {
                    "health_goal": "lose_weight",
                    "target_calories": 1800,
                    "target_protein": 120,
                    "target_carbs": 180,
                    "target_fat": 55,
                    "max_budget": 120,
                    "disliked_foods": [],
                    "preferred_tags": [],
                },
                "score": 10,
            },
            "alternatives": [
                {
                    "option_key": "budget_cut",
                    "title": "保守减脂",
                    "rationale": "优先控制预算。",
                    "meal_plan": {
                        "id": "plan001",
                        "created_at": "2026-04-02T10:00:00",
                        "meals": [],
                        "nutrition": {
                            "total_calories": 1800,
                            "total_protein": 120,
                            "total_carbs": 180,
                            "total_fat": 55,
                            "total_price": 120,
                            "calories_achievement": 100,
                            "protein_achievement": 100,
                            "budget_usage": 100,
                        },
                        "target": {
                            "health_goal": "lose_weight",
                            "target_calories": 1800,
                            "target_protein": 120,
                            "target_carbs": 180,
                            "target_fat": 55,
                            "max_budget": 120,
                            "disliked_foods": [],
                            "preferred_tags": [],
                        },
                        "score": 10,
                    },
                }
            ],
        },
    }
    monkeypatch.setattr(
        "intelligent_meal_planner.api.routers.meal_chat.meal_chat_app.handle_message",
        lambda db, user, session_id, content: fake_response,
    )

    response = client.post(
        "/api/meal-chat/sessions/session001/messages",
        headers=auth_header,
        json={"content": "那直接给我方案吧"},
    )

    assert response.status_code == 200
    assert "alternatives" in response.json()["meal_plan"]


def test_send_message_returns_visible_crew_events(client, auth_header, monkeypatch):
    fake_response = {
        "session_id": "session001",
        "status": "finalized",
        "messages": [
            {"role": "assistant", "content": "多智能体协作已完成，我给你整理好了方案。"}
        ],
        "meal_plan": {"id": "plan001", "meals": [], "nutrition": {}, "target": {}, "score": 10},
        "crew_trace": [
            {"agent": "需求审查专员", "status": "completed", "message": "需求已确认"},
            {"agent": "DQN 配餐师", "status": "completed", "message": "DQN 配餐完成"},
        ],
    }
    monkeypatch.setattr(
        "intelligent_meal_planner.api.routers.meal_chat.meal_chat_app.handle_message",
        lambda db, user, session_id, content: fake_response,
    )

    response = client.post(
        "/api/meal-chat/sessions/session001/messages",
        headers=auth_header,
        json={"content": "给我方案"},
    )

    assert response.status_code == 200
    assert len(response.json()["crew_trace"]) == 2
