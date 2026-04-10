from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class LLMRecommendationItem(BaseModel):
    restaurant_id: str = Field(..., min_length=1)
    rank: int = Field(..., ge=1)
    fit_reason: str = Field(..., min_length=1)


class LLMRecommendationPayload(BaseModel):
    summary: str = Field(..., min_length=1)
    recommendations: List[LLMRecommendationItem]

