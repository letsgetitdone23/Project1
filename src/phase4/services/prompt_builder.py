from __future__ import annotations

import json
from typing import Any, Dict, List

from src.phase0.data.models import Restaurant
from src.phase2.services.preference_normalizer import NormalizedPreferences


def _restaurant_to_prompt_item(restaurant: Restaurant, score: float) -> Dict[str, Any]:
    cuisines = [c.strip() for c in (restaurant.cuisines or "").split(",") if c.strip()]
    return {
        "restaurant_id": restaurant.id,
        "name": restaurant.name,
        "city": restaurant.city,
        "locality": restaurant.locality or "",
        "cuisines": cuisines,
        "rating": restaurant.rating,
        "avg_cost_for_two": restaurant.avg_cost_for_two,
        "deterministic_score": round(score, 4),
    }


def build_messages(
    *,
    preferences: NormalizedPreferences,
    ranked_candidates: List[tuple[Restaurant, float]],
    top_k: int,
) -> List[Dict[str, str]]:
    prompt_candidates = [_restaurant_to_prompt_item(r, s) for r, s in ranked_candidates]
    user_context = {
        "preferences": {
            "city": preferences.city,
            "budget_band": preferences.budget_band,
            "cuisines": preferences.cuisines,
            "min_rating": preferences.min_rating,
            "tags": preferences.tags,
            "top_k": top_k,
        },
        "candidates": prompt_candidates,
    }

    system_prompt = (
        "You are a restaurant recommendation analyst. "
        "Use ONLY the given candidate restaurants and do not invent any new restaurant.\n"
        "Return STRICT JSON with keys: summary, recommendations.\n"
        "Each recommendations item must include: restaurant_id, rank, fit_reason.\n"
        "Ranks must start from 1 and be unique. Keep fit_reason concise and user-friendly."
    )

    user_prompt = (
        "Rank the best restaurants for this user and explain each choice.\n"
        f"Return top {top_k} entries.\n\n"
        f"Input JSON:\n{json.dumps(user_context, ensure_ascii=True)}"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

