from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "service" in payload


def test_ready_endpoint():
    response = client.get("/ready")
    assert response.status_code == 200
    payload = response.json()
    assert "checks" in payload
    assert "database" in payload["checks"]

