from __future__ import annotations

from time import perf_counter

from fastapi import APIRouter, HTTPException

from src.phase0.data.repository import get_session
from src.phase2.api.schemas import RecommendationRequest, RecommendationResponse
from src.phase2.services.preference_normalizer import normalize_preferences
from src.phase3.services.retrieval_engine import get_ranked_restaurants
from src.phase4.services.llm_orchestrator import LLMOrchestrationError, call_groq_recommendation
from src.phase4.services.prompt_builder import build_messages
from src.phase4.services.ranking_adapter import apply_grounded_llm_ranking
from src.phase5.services.response_composer import compose_recommendation_response
from src.phase6.observability.logger import log_event
from src.phase6.observability.metrics import metrics_store


router = APIRouter()
MODEL_CANDIDATE_COUNT = 40


@router.post("/recommendations", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest) -> RecommendationResponse:
    start = perf_counter()
    metrics_store.record_request()
    normalized = normalize_preferences(
        location=request.location,
        budget=request.budget,
        cuisine=request.cuisine,
        min_rating=request.min_rating,
        additional_preferences=request.additional_preferences,
        top_k=request.top_k,
    )

    retrieval_start = perf_counter()
    with get_session() as session:
        ranked = get_ranked_restaurants(session, normalized)
    retrieval_ms = (perf_counter() - retrieval_start) * 1000
    metrics_store.record_retrieval_latency(retrieval_ms)

    if not ranked:
        metrics_store.record_not_found()
        elapsed_ms = (perf_counter() - start) * 1000
        metrics_store.record_api_latency(elapsed_ms)
        log_event(
            "recommendation_not_found",
            {"city": normalized.city, "top_k": normalized.top_k, "timing_ms": round(elapsed_ms, 2)},
        )
        raise HTTPException(status_code=404, detail="No restaurants found matching the given preferences.")

    effective_top_k = normalized.top_k if normalized.top_k is not None else len(ranked)
    effective_top_k = max(1, min(effective_top_k, len(ranked)))
    model_candidate_count = min(len(ranked), max(MODEL_CANDIDATE_COUNT, effective_top_k))

    used_fallback = False
    final_ranked: list[tuple] = []
    llm_summary: str | None = None
    try:
        messages = build_messages(
            preferences=normalized,
            ranked_candidates=ranked[:model_candidate_count],
            top_k=effective_top_k,
        )
        llm_start = perf_counter()
        llm_payload = call_groq_recommendation(messages=messages)
        llm_ms = (perf_counter() - llm_start) * 1000
        metrics_store.record_llm_latency(llm_ms)
        llm_summary = llm_payload.summary
        final_ranked = apply_grounded_llm_ranking(
            llm_payload=llm_payload,
            ranked_candidates=ranked,
            top_k=effective_top_k,
        )
    except (LLMOrchestrationError, ValueError):
        used_fallback = True
        metrics_store.record_llm_failure()
        final_ranked = [
            (
                restaurant,
                score,
                f"Score {score:.2f} based on rating, cuisine match, and budget fit.",
            )
            for restaurant, score in ranked[:effective_top_k]
        ]
    elapsed_ms = (perf_counter() - start) * 1000
    metrics_store.record_api_latency(elapsed_ms)
    metrics_store.record_success(used_fallback=used_fallback)
    log_event(
        "recommendation_served",
        {
            "city": normalized.city,
            "top_k": effective_top_k,
            "used_fallback": used_fallback,
            "timing_ms": round(elapsed_ms, 2),
            "retrieval_ms": round(retrieval_ms, 2),
            "result_count": len(final_ranked),
        },
    )
    return compose_recommendation_response(
        ranked_items=final_ranked,
        used_fallback=used_fallback,
        timing_ms=elapsed_ms,
        summary=llm_summary if not used_fallback else None,
    )

