from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, confloat, conint


class RecommendationRequest(BaseModel):
    location: str = Field(..., description="City or location, e.g. Bangalore")
    budget: Optional[confloat(gt=0)] = Field(
        default=None,
        description="Approx budget (cost for two) as a numeric value",
    )
    cuisine: Optional[List[str]] = Field(default=None, description="Preferred cuisines")
    min_rating: Optional[confloat(ge=0.0, le=5.0)] = Field(default=None)
    additional_preferences: Optional[List[str]] = Field(default=None)
    top_k: Optional[conint(gt=0, le=500)] = Field(
        default=None,
        description="Optional max recommendations to return; if omitted, all ranked matches are returned.",
    )


class RecommendationItem(BaseModel):
    name: str
    cuisine: Optional[List[str]] = None
    rating: Optional[float] = None
    estimated_cost_for_two: Optional[float] = None
    city: str
    locality: Optional[str] = None
    explanation: str


class RecommendationResponse(BaseModel):
    request_id: str
    used_fallback: bool
    timing_ms: float
    summary: Optional[str] = None
    recommendations: List[RecommendationItem]

