from __future__ import annotations

from typing import Dict, List

from src.phase0.data.models import Restaurant

from .llm_types import LLMRecommendationPayload


def apply_grounded_llm_ranking(
    *,
    llm_payload: LLMRecommendationPayload,
    ranked_candidates: List[tuple[Restaurant, float]],
    top_k: int,
) -> list[tuple[Restaurant, float, str]]:
    candidate_by_id: Dict[str, tuple[Restaurant, float]] = {
        restaurant.id: (restaurant, score) for restaurant, score in ranked_candidates
    }

    final_items: list[tuple[Restaurant, float, str]] = []
    seen_ids = set()
    for rec in sorted(llm_payload.recommendations, key=lambda r: r.rank):
        if rec.restaurant_id not in candidate_by_id:
            raise ValueError("LLM produced unknown restaurant_id.")
        if rec.restaurant_id in seen_ids:
            continue
        seen_ids.add(rec.restaurant_id)
        restaurant, score = candidate_by_id[rec.restaurant_id]
        final_items.append((restaurant, score, rec.fit_reason))
        if len(final_items) >= top_k:
            break

    # backfill from deterministic order if LLM returned fewer than top_k
    if len(final_items) < top_k:
        selected = {item[0].id for item in final_items}
        for restaurant, score in ranked_candidates:
            if restaurant.id in selected:
                continue
            final_items.append(
                (
                    restaurant,
                    score,
                    f"Score {score:.2f} based on rating, cuisine match, and budget fit.",
                )
            )
            if len(final_items) >= top_k:
                break

    return final_items

