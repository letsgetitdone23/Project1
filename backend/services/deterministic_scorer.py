from __future__ import annotations

from typing import Iterable, List, Optional

from ..data.models import Restaurant


def _cuisine_overlap_score(
    user_cuisines: List[str],
    restaurant_cuisines: Optional[str],
) -> float:
    if not user_cuisines or not restaurant_cuisines:
        return 0.0
    items = [c.strip().title() for c in restaurant_cuisines.split(",") if c.strip()]
    rest_set = {c for c in items}
    if not rest_set:
        return 0.0
    matches = len(rest_set.intersection(set(user_cuisines)))
    return matches / len(rest_set)


def _budget_fit_score(
    avg_cost_for_two: Optional[float],
    budget_band: Optional[dict],
) -> float:
    if avg_cost_for_two is None or not budget_band:
        return 0.0
    min_cost = budget_band["min"]
    max_cost = budget_band["max"]
    if avg_cost_for_two < min_cost or avg_cost_for_two > max_cost:
        return 0.0
    if max_cost == min_cost:
        return 1.0
    # closer to band center -> higher score
    center = (min_cost + max_cost) / 2
    dist = abs(avg_cost_for_two - center)
    half_span = (max_cost - min_cost) / 2
    return max(0.0, 1.0 - dist / half_span)


def score_restaurants(
    *,
    restaurants: Iterable[Restaurant],
    user_cuisines: List[str],
    budget_band: Optional[dict],
) -> List[tuple[Restaurant, float]]:
    """Compute a simple weighted deterministic score for each restaurant."""

    results: List[tuple[Restaurant, float]] = []
    for r in restaurants:
        rating_score = (r.rating or 0.0) / 5.0
        cuisine_score = _cuisine_overlap_score(user_cuisines, r.cuisines)
        budget_score = _budget_fit_score(r.avg_cost_for_two, budget_band)

        # weights: rating 0.4, cuisine 0.3, budget 0.3
        score = 0.4 * rating_score + 0.3 * cuisine_score + 0.3 * budget_score
        results.append((r, score))

    results.sort(key=lambda pair: pair[1], reverse=True)
    return results

