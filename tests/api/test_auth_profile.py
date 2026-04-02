def test_me_returns_full_profile(client, auth_header):
    response = client.get("/api/auth/me", headers=auth_header)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "planner_user"
    assert data["gender"] == "male"
    assert data["height"] == 175
    assert data["weight"] == 68
    assert data["activity_level"] == "moderate"
    assert data["health_goal"] == "healthy"


def test_patch_profile_updates_fields(client, auth_header):
    payload = {
        "age": 25,
        "weight": 70,
        "activity_level": "active",
        "health_goal": "gain_muscle",
    }

    response = client.patch(
        "/api/auth/me/profile",
        json=payload,
        headers=auth_header,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["age"] == 25
    assert data["weight"] == 70
    assert data["activity_level"] == "active"
    assert data["health_goal"] == "gain_muscle"
