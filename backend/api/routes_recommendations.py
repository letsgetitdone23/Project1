from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, HTTPException

from ..data.repository import get_session
from ..services.preference_normalizer import normalize_preferences
from ..services.retrieval_engine import get_ranked_restaurants
from .schemas import RecommendationItem, RecommendationRequest, RecommendationResponse


router = APIRouter()


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="Get restaurant recommendations (deterministic only, no LLM yet)",
)
def recommend(request: RecommendationRequest) -> RecommendationResponse:
    normalized = normalize_preferences(
        location=request.location,
        budget=request.budget,
        cuisine=request.cuisine,
        min_rating=request.min_rating,
        additional_preferences=request.additional_preferences,
        top_k=request.top_k,
    )

    with get_session() as session:
        ranked = get_ranked_restaurants(session, normalized)

    if not ranked:
        raise HTTPException(
            status_code=404,
            detail="No restaurants found matching the given preferences.",
        )

    top = ranked[: normalized.top_k]
    items: List[RecommendationItem] = []
    for restaurant, score in top:
        cuisines = (
            [c.strip() for c in restaurant.cuisines.split(",") if c.strip()]
            if restaurant.cuisines
            else None
        )
        explanation = (
            f"Score {score:.2f} based on rating, cuisine match, and budget fit."
        )
        items.append(
            RecommendationItem(
                name=restaurant.name,
                cuisine=cuisines,
                rating=restaurant.rating,
                estimated_cost_for_two=restaurant.avg_cost_for_two,
                city=restaurant.city,
                locality=restaurant.locality or None,
                explanation=explanation,
            )
        )

    return RecommendationResponse(
        request_id=str(uuid.uuid4()),
        used_fallback=True,  # deterministic engine; LLM will flip this later
        recommendations=items,
    )

