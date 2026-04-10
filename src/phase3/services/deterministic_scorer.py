from __future__ import annotations

from typing import Iterable, List, Optional

from src.phase0.data.models import Restaurant


def _cuisine_overlap_score(user_cuisines: List[str], restaurant_cuisines: Optional[str]) -> float:
    if not user_cuisines or not restaurant_cuisines:
        return 0.0
    items = [c.strip().title() for c in restaurant_cuisines.split(",") if c.strip()]
    if not items:
        return 0.0
    matches = len(set(items).intersection(set(user_cuisines)))
    return matches / len(set(items))


def _budget_fit_score(avg_cost_for_two: Optional[float], budget_band: Optional[dict]) -> float:
    if avg_cost_for_two is None or not budget_band:
        return 0.0
    min_cost = budget_band["min"]
    max_cost = budget_band["max"]
    if avg_cost_for_two < min_cost or avg_cost_for_two > max_cost:
        return 0.0
    center = (min_cost + max_cost) / 2
    half_span = max((max_cost - min_cost) / 2, 1)
    return max(0.0, 1.0 - abs(avg_cost_for_two - center) / half_span)


def score_restaurants(
    *,
    restaurants: Iterable[Restaurant],
    user_cuisines: List[str],
    budget_band: Optional[dict],
) -> List[tuple[Restaurant, float]]:
    scored: List[tuple[Restaurant, float]] = []
    for restaurant in restaurants:
        rating_score = (restaurant.rating or 0.0) / 5.0
        cuisine_score = _cuisine_overlap_score(user_cuisines, restaurant.cuisines)
        budget_score = _budget_fit_score(restaurant.avg_cost_for_two, budget_band)
        score = 0.4 * rating_score + 0.3 * cuisine_score + 0.3 * budget_score
        scored.append((restaurant, score))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored

