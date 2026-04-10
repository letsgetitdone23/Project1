from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


_BUDGET_SYNONYMS: Dict[str, str] = {
    "low": "low",
    "cheap": "low",
    "budget": "low",
    "medium": "medium",
    "mid": "medium",
    "midrange": "medium",
    "high": "high",
    "expensive": "high",
    "premium": "high",
}


_CITY_FIXES: Dict[str, str] = {
    "banglore": "bangalore",
    "new delhi": "delhi",
}


_TAG_NORMALIZATION: Dict[str, str] = {
    "family-friendly": "family_friendly",
    "family friendly": "family_friendly",
    "kid friendly": "family_friendly",
    "quick service": "quick_service",
    "fast": "quick_service",
}


@dataclass
class NormalizedPreferences:
    city: str
    budget_band: Optional[Dict[str, float]]
    cuisines: List[str]
    min_rating: float
    tags: List[str]
    top_k: int


def _normalize_city(raw: str) -> str:
    value = raw.strip().lower()
    if value in _CITY_FIXES:
        value = _CITY_FIXES[value]
    return value


def _normalize_budget(budget: Optional[str]) -> Optional[str]:
    if not budget:
        return None
    key = budget.strip().lower()
    return _BUDGET_SYNONYMS.get(key)


def _budget_to_band(label: Optional[str]) -> Optional[Dict[str, float]]:
    if label == "low":
        return {"min": 0, "max": 600}
    if label == "medium":
        return {"min": 600, "max": 1500}
    if label == "high":
        return {"min": 1500, "max": 10000}
    return None


def _normalize_cuisines(cuisines: Optional[List[str]]) -> List[str]:
    if not cuisines:
        return []
    return sorted({c.strip().title() for c in cuisines if c.strip()})


def _normalize_tags(tags: Optional[List[str]]) -> List[str]:
    if not tags:
        return []
    normalized: List[str] = []
    for raw in tags:
        key = raw.strip().lower()
        if key in _TAG_NORMALIZATION:
            normalized.append(_TAG_NORMALIZATION[key])
        else:
            normalized.append(key.replace(" ", "_"))
    # preserve order but deduplicate
    seen = set()
    result: List[str] = []
    for t in normalized:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


def normalize_preferences(
    *,
    location: str,
    budget: Optional[str],
    cuisine: Optional[List[str]],
    min_rating: Optional[float],
    additional_preferences: Optional[List[str]],
    top_k: int,
) -> NormalizedPreferences:
    city = _normalize_city(location)
    budget_label = _normalize_budget(budget)
    budget_band = _budget_to_band(budget_label)

    cuisines = _normalize_cuisines(cuisine)
    tags = _normalize_tags(additional_preferences)
    rating = min_rating if min_rating is not None else 3.5

    return NormalizedPreferences(
        city=city,
        budget_band=budget_band,
        cuisines=cuisines,
        min_rating=rating,
        tags=tags,
        top_k=top_k,
    )

