from __future__ import annotations

import uuid
from typing import List, Optional

from src.phase0.data.models import Restaurant
from src.phase2.api.schemas import RecommendationItem, RecommendationResponse


def compose_recommendation_response(
    *,
    ranked_items: List[tuple[Restaurant, float, str]],
    used_fallback: bool,
    timing_ms: float,
    summary: Optional[str] = None,
) -> RecommendationResponse:
    recommendations: List[RecommendationItem] = []
    for restaurant, _score, explanation in ranked_items:
        cuisines = [c.strip() for c in (restaurant.cuisines or "").split(",") if c.strip()]
        recommendations.append(
            RecommendationItem(
                name=restaurant.name,
                cuisine=cuisines or None,
                rating=restaurant.rating,
                estimated_cost_for_two=restaurant.avg_cost_for_two,
                city=restaurant.city,
                locality=restaurant.locality or None,
                explanation=explanation,
            )
        )

    return RecommendationResponse(
        request_id=str(uuid.uuid4()),
        used_fallback=used_fallback,
        timing_ms=round(max(timing_ms, 0.0), 2),
        summary=summary,
        recommendations=recommendations,
    )

