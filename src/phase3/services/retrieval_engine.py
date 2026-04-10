from __future__ import annotations

from typing import List

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from src.phase0.data.models import Restaurant
from src.phase2.services.preference_normalizer import NormalizedPreferences
from src.phase3.services.deterministic_scorer import score_restaurants

RELAXED_LOCATION_INPUTS = {"bangalore", "bengaluru"}


def _base_conditions(prefs: NormalizedPreferences) -> list:
    conditions = []
    if prefs.min_rating is not None:
        conditions.append(Restaurant.rating >= prefs.min_rating)
    if prefs.budget_band is not None:
        conditions.append(
            and_(
                Restaurant.avg_cost_for_two >= prefs.budget_band["min"],
                Restaurant.avg_cost_for_two <= prefs.budget_band["max"],
            )
        )
    return conditions


def retrieve_candidates(session: Session, prefs: NormalizedPreferences, max_candidates: int = 50) -> List[Restaurant]:
    base_conditions = _base_conditions(prefs)

    # Primary: strict city match
    strict_conditions = [Restaurant.city == prefs.city, *base_conditions]
    stmt = select(Restaurant).where(and_(*strict_conditions)).limit(max_candidates)
    strict_results = list(session.scalars(stmt))
    if strict_results:
        return strict_results

    # Fallback: some datasets store locality in the "city" field.
    # If strict city has no matches, relax location filter to city/locality contains.
    relaxed_location = or_(
        Restaurant.city.ilike(f"%{prefs.city}%"),
        Restaurant.locality.ilike(f"%{prefs.city}%"),
    )
    relaxed_conditions = [relaxed_location, *base_conditions]
    relaxed_stmt = select(Restaurant).where(and_(*relaxed_conditions)).limit(max_candidates)
    relaxed_results = list(session.scalars(relaxed_stmt))
    if relaxed_results:
        return relaxed_results

    # Final fallback: only for known city-level queries where dataset stores localities.
    if prefs.city in RELAXED_LOCATION_INPUTS:
        broad_stmt = select(Restaurant).where(and_(*base_conditions)).limit(max_candidates)
        return list(session.scalars(broad_stmt))

    return []


def get_ranked_restaurants(session: Session, prefs: NormalizedPreferences) -> List[tuple[Restaurant, float]]:
    candidates = retrieve_candidates(session, prefs)
    return score_restaurants(
        restaurants=candidates,
        user_cuisines=prefs.cuisines,
        budget_band=prefs.budget_band,
    )

