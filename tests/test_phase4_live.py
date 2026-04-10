from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi.testclient import TestClient

from src.phase0.app import app
from src.phase2.services.preference_normalizer import normalize_preferences
from src.phase4.services.llm_orchestrator import call_groq_recommendation
from src.phase4.services.prompt_builder import build_messages


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def test_prompt_builder_creates_messages() -> None:
    prefs = normalize_preferences(
        location="Bangalore",
        budget=1200,
        cuisine=["Italian"],
        min_rating=4.0,
        additional_preferences=["family-friendly"],
        top_k=3,
    )
    messages = build_messages(preferences=prefs, ranked_candidates=[], top_k=3)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_groq_live_connection_returns_structured_output() -> None:
    messages = [
        {
            "role": "system",
            "content": (
                "Return strict JSON with keys summary and recommendations. "
                "recommendations must contain restaurant_id, rank, fit_reason."
            ),
        },
        {
            "role": "user",
            "content": (
                '{"preferences":{"top_k":1},"candidates":['
                '{"restaurant_id":"r1","name":"A","city":"bangalore","cuisines":["Italian"],'
                '"rating":4.4,"avg_cost_for_two":1200,"deterministic_score":0.9},'
                '{"restaurant_id":"r2","name":"B","city":"bangalore","cuisines":["Chinese"],'
                '"rating":4.2,"avg_cost_for_two":1000,"deterministic_score":0.8}'
                ']}'
            ),
        },
    ]

    payload = call_groq_recommendation(messages=messages, timeout_seconds=30)
    assert payload.summary.strip() != ""
    assert len(payload.recommendations) >= 1
    assert payload.recommendations[0].restaurant_id in {"r1", "r2"}


def test_recommendations_endpoint_live_response_shape() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/recommendations",
        json={
            "location": "Bangalore",
            "budget": 1200,
            "cuisine": ["Italian"],
            "min_rating": 4.0,
            "additional_preferences": ["family-friendly"],
            "top_k": 3,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "request_id" in body
    assert "used_fallback" in body
    assert isinstance(body.get("recommendations"), list)


def test_recommendations_endpoint_second_profile() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/recommendations",
        json={
            "location": "Bangalore",
            "budget": 2200,
            "cuisine": ["North Indian", "Chinese"],
            "min_rating": 3.8,
            "additional_preferences": ["quick service"],
            "top_k": 2,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["recommendations"]) <= 2

