from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, conint, confloat


class RecommendationRequest(BaseModel):
    location: str = Field(..., description="City or location, e.g. Bangalore")
    budget: Optional[str] = Field(
        default=None,
        description="Budget band identifier, e.g. low/medium/high",
    )
    cuisine: Optional[List[str]] = Field(
        default=None,
        description="Preferred cuisines, e.g. ['Italian', 'Chinese']",
    )
    min_rating: Optional[confloat(ge=0.0, le=5.0)] = Field(
        default=None, description="Minimum acceptable rating (0-5)"
    )
    additional_preferences: Optional[List[str]] = Field(
        default=None, description="Free-form preferences like 'family-friendly'"
    )
    top_k: conint(gt=0, le=50) = Field(
        default=5, description="Number of recommendations to return"
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
    recommendations: List[RecommendationItem]

