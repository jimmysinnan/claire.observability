from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_auth_guard_on_metrics() -> None:
    response = client.get("/api/v1/metrics")
    assert response.status_code == 401
