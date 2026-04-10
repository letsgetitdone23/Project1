from fastapi.testclient import TestClient

from src.phase0.app import app


def test_home_ui_page_loads() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "AI-Powered Restaurant Recommendation" in response.text
    assert "Get Recommendations" in response.text

