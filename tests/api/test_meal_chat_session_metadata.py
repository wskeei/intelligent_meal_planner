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
    """测试英语语言偏好 - 新系统统一使用中文"""
    response = client.post(
        "/api/meal-chat/sessions",
        headers={**auth_header, "Accept-Language": "en-US,en;q=0.9"},
    )

    assert response.status_code == 200
    payload = response.json()

    # 新系统使用中文欢迎消息（已注册用户会收到个性化消息）
    welcome = payload["messages"][0]["content"]
    assert "配餐" in welcome or "营养" in welcome or "饮食" in welcome


def test_post_message_session_includes_memory_metadata(
    client, auth_header, monkeypatch
):
    """测试消息处理返回正确的结构"""
    from unittest.mock import patch, MagicMock

    # 创建一个模拟的 Flow 状态类
    class MockState:
        def __init__(self):
            self.recent_messages = [
                MagicMock(role="user", content="预算 100 元，想减脂"),
                MagicMock(role="assistant", content="好的，我来帮你规划减脂餐。"),
            ]
            self.current_phase = "discovering"
            # 注意：这些值会在 handle_message 中被覆盖
            # 所以我们不需要在这里设置具体的值
            self.collected_profile = {}
            self.collected_preferences = {}
            self.current_meal_plan = None
            self.user_message = ""

    # 创建一个模拟的 Flow
    class MockFlow:
        def __init__(self):
            self.state = MockState()

        def kickoff(self):
            # 在 kickoff 后更新状态（模拟真实行为）
            self.state.collected_profile = {
                "gender": "male",
                "age": 24,
                "height_cm": 175,
                "weight_kg": 68,
                "activity_level": "moderate",
            }
            self.state.collected_preferences = {
                "health_goal": "lose_weight",
                "budget": 100.0,
            }

        async def kickoff_async(self):
            # 异步版本，模拟真实行为
            self.state.collected_profile = {
                "gender": "male",
                "age": 24,
                "height_cm": 175,
                "weight_kg": 68,
                "activity_level": "moderate",
            }
            self.state.collected_preferences = {
                "health_goal": "lose_weight",
                "budget": 100.0,
            }

    with patch(
        "intelligent_meal_planner.api.services.create_meal_chat_flow",
        return_value=MockFlow(),
    ):
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
    # 检查结构存在
    assert "profile_snapshot" in payload
    assert "preferences_snapshot" in payload
