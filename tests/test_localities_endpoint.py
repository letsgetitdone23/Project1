from fastapi.testclient import TestClient

from src.phase0.app import app


def test_localities_endpoint_returns_list() -> None:
    client = TestClient(app)
    response = client.get("/v1/localities")
    assert response.status_code == 200
    body = response.json()
    assert "localities" in body
    assert isinstance(body["localities"], list)

