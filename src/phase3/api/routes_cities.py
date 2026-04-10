from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.phase0.data.models import Restaurant
from src.phase0.data.repository import get_session


router = APIRouter()


@router.get("/cities", summary="List selectable city column values")
def list_cities() -> dict:
    try:
        with get_session() as session:
            values = list(
                session.scalars(
                    select(Restaurant.city)
                    .where(Restaurant.city.is_not(None))
                    .distinct()
                    .order_by(Restaurant.city.asc())
                )
            )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Database is not ready. Ensure DATABASE_URL is valid and the "
                "restaurants table is initialized with data."
            ),
        ) from exc
    # Normalize and deduplicate city labels so frontend dropdowns remain stable.
    cities = sorted(
        {
            v.strip().lower()
            for v in values
            if isinstance(v, str) and v.strip()
        }
    )
    return {"cities": cities, "count": len(cities)}

