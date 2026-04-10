from fastapi import APIRouter

from src.phase6.observability.metrics import metrics_store


router = APIRouter()


@router.get("/metrics", summary="In-memory service metrics")
def get_metrics() -> dict:
    return metrics_store.snapshot()

