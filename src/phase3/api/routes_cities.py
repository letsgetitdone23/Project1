from fastapi import APIRouter
from sqlalchemy import select

from src.phase0.data.models import Restaurant
from src.phase0.data.repository import get_session


router = APIRouter()


@router.get("/cities", summary="List selectable city column values")
def list_cities() -> dict:
    with get_session() as session:
        values = list(
            session.scalars(
                select(Restaurant.city)
                .where(Restaurant.city.is_not(None))
                .distinct()
                .order_by(Restaurant.city.asc())
            )
        )
    cities = [v for v in values if isinstance(v, str) and v.strip()]
    return {"cities": cities, "count": len(cities)}

