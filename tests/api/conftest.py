import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from intelligent_meal_planner.api.main import app
from intelligent_meal_planner.db.database import Base, get_db


@pytest.fixture()
def client(tmp_path):
    db_file = tmp_path / "auth-profile.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_header(client):
    register_payload = {
        "username": "planner_user",
        "email": "planner@example.com",
        "password": "secret123",
        "age": 24,
        "gender": "male",
        "height": 175,
        "weight": 68,
        "activity_level": "moderate",
        "health_goal": "healthy",
    }
    client.post("/api/auth/register", json=register_payload)
    token_response = client.post(
        "/api/auth/token",
        data={"username": "planner_user", "password": "secret123"},
    )
    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
