def test_create_session_returns_first_assistant_message(client, auth_header, monkeypatch):
    fake_response = {
        "session_id": "session001",
        "status": "collecting_profile",
        "messages": [
            {
                "role": "assistant",
                "content": "告诉我一下你的年龄。",
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
    assert response.json()["messages"][0]["role"] == "assistant"


def test_send_message_returns_budget_rejected_status(client, auth_header, monkeypatch):
    fake_response = {
        "session_id": "session001",
        "status": "budget_rejected",
        "messages": [
            {
                "role": "assistant",
                "content": "按你当前的需求，这个预算过低，需要适当提高预算后我再为你正式配餐。",
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
        json={"content": "预算 30 元"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "budget_rejected"
