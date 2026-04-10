from __future__ import annotations

from typing import List

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ..data.models import Restaurant
from .deterministic_scorer import score_restaurants
from .preference_normalizer import NormalizedPreferences


def retrieve_candidates(
    session: Session,
    prefs: NormalizedPreferences,
    max_candidates: int = 50,
) -> List[Restaurant]:
    """Apply hard filters to get a candidate set."""
    conditions = [Restaurant.city == prefs.city]

    if prefs.min_rating is not None:
        conditions.append(Restaurant.rating >= prefs.min_rating)

    if prefs.budget_band is not None:
        # loose filter on cost band to keep enough candidates
        conditions.append(
            and_(
                Restaurant.avg_cost_for_two >= prefs.budget_band["min"] * 0.5,
                Restaurant.avg_cost_for_two <= prefs.budget_band["max"] * 1.5,
            )
        )

    stmt = (
        select(Restaurant)
        .where(and_(*conditions))
        .limit(max_candidates)
    )
    return list(session.scalars(stmt))


def get_ranked_restaurants(
    session: Session,
    prefs: NormalizedPreferences,
) -> List[tuple[Restaurant, float]]:
    candidates = retrieve_candidates(session, prefs)
    scored = score_restaurants(
        restaurants=candidates,
        user_cuisines=prefs.cuisines,
        budget_band=prefs.budget_band,
    )
    return scored

