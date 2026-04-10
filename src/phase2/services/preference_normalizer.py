from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class NormalizedPreferences:
    city: str
    budget_band: Optional[Dict[str, float]]
    cuisines: List[str]
    min_rating: float
    tags: List[str]
    top_k: Optional[int]


def normalize_preferences(
    *,
    location: str,
    budget: Optional[float],
    cuisine: Optional[List[str]],
    min_rating: Optional[float],
    additional_preferences: Optional[List[str]],
    top_k: Optional[int],
) -> NormalizedPreferences:
    band = None
    if budget is not None:
        # User provides target cost-for-two; search in a tolerance band.
        amount = float(budget)
        tolerance = max(200.0, amount * 0.35)
        band = {"min": max(0.0, amount - tolerance), "max": amount + tolerance}

    cuisines = sorted({c.strip().title() for c in (cuisine or []) if c.strip()})
    tags = [t.strip().lower().replace(" ", "_") for t in (additional_preferences or []) if t.strip()]

    return NormalizedPreferences(
        city=location.strip().lower(),
        budget_band=band,
        cuisines=cuisines,
        min_rating=min_rating if min_rating is not None else 3.5,
        tags=tags,
        top_k=top_k,
    )

