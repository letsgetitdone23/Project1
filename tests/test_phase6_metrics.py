from fastapi.testclient import TestClient

from src.phase0.app import app


def test_metrics_endpoint_exists() -> None:
    client = TestClient(app)
    response = client.get("/v1/metrics")
    assert response.status_code == 200
    body = response.json()
    assert "totals" in body
    assert "latency" in body


def test_metrics_change_after_request() -> None:
    client = TestClient(app)
    before = client.get("/v1/metrics").json()
    _ = client.post(
        "/v1/recommendations",
        json={
            "location": "nonexistent-city-xyz",
            "budget": 2200,
            "cuisine": ["Italian"],
            "min_rating": 4.9,
            "top_k": 1,
        },
    )
    after = client.get("/v1/metrics").json()
    assert after["totals"]["total_requests"] >= before["totals"]["total_requests"] + 1

