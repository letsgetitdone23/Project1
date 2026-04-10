from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.phase0.app import app
from src.phase4.services.llm_types import LLMRecommendationItem, LLMRecommendationPayload


def test_phase5_response_includes_metadata_on_llm_success(monkeypatch) -> None:
    fake_restaurant = SimpleNamespace(
        id="r1",
        name="Test Resto",
        cuisines="Italian, Continental",
        rating=4.5,
        avg_cost_for_two=1200.0,
        city="bangalore",
        locality="Indiranagar",
    )

    def fake_llm(*, messages, model=None, timeout_seconds=20):  # noqa: ANN001
        return LLMRecommendationPayload(
            summary="Top picks for your profile.",
            recommendations=[
                LLMRecommendationItem(restaurant_id="c6206e6f72ec0f6f08ec13a62044f5cf", rank=1, fit_reason="Great match."),
            ],
        )

    monkeypatch.setattr(
        "src.phase3.api.routes_recommendations.get_ranked_restaurants",
        lambda session, prefs: [(fake_restaurant, 0.91)],
    )
    monkeypatch.setattr("src.phase3.api.routes_recommendations.call_groq_recommendation", fake_llm)
    monkeypatch.setattr(
        "src.phase3.api.routes_recommendations.apply_grounded_llm_ranking",
        lambda *, llm_payload, ranked_candidates, top_k: [
            (ranked_candidates[0][0], ranked_candidates[0][1], "Great match.")
        ],
    )

    client = TestClient(app)
    response = client.post(
        "/v1/recommendations",
        json={
            "location": "Bangalore",
            "budget": 1200,
            "cuisine": ["Italian"],
            "min_rating": 4.0,
            "top_k": 1,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["used_fallback"] is False
    assert isinstance(body["timing_ms"], (int, float))
    assert body["summary"] == "Top picks for your profile."


def test_phase5_response_fallback_metadata(monkeypatch) -> None:
    from src.phase4.services.llm_orchestrator import LLMOrchestrationError

    fake_restaurant = SimpleNamespace(
        id="r2",
        name="Fallback Resto",
        cuisines="Italian",
        rating=4.2,
        avg_cost_for_two=900.0,
        city="bangalore",
        locality="Koramangala",
    )

    def fail_llm(*, messages, model=None, timeout_seconds=20):  # noqa: ANN001
        raise LLMOrchestrationError("forced failure")

    monkeypatch.setattr(
        "src.phase3.api.routes_recommendations.get_ranked_restaurants",
        lambda session, prefs: [(fake_restaurant, 0.82)],
    )
    monkeypatch.setattr("src.phase3.api.routes_recommendations.call_groq_recommendation", fail_llm)

    client = TestClient(app)
    response = client.post(
        "/v1/recommendations",
        json={
            "location": "Bangalore",
            "budget": 1000,
            "cuisine": ["Italian"],
            "min_rating": 4.0,
            "top_k": 2,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["used_fallback"] is True
    assert body["summary"] is None
    assert len(body["recommendations"]) <= 2


def test_phase5_no_results_returns_empty_200() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/recommendations",
        json={
            "location": "nonexistent-city-xyz",
            "budget": 2200,
            "cuisine": ["Italian"],
            "min_rating": 4.9,
            "top_k": 2,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"] == []
    assert body["used_fallback"] is True
    assert isinstance(body.get("summary"), str) and body["summary"]

