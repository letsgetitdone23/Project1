from pathlib import Path

import pandas as pd

from backend.data.models import Restaurant
from backend.data.repository import get_session, init_db


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"


def load_clean_to_db(clean_path: Path) -> None:
    init_db()
    df = pd.read_parquet(clean_path)

    with get_session() as session:
        for _, row in df.iterrows():
            restaurant = session.get(Restaurant, str(row["id"]))
            if restaurant is None:
                restaurant = Restaurant(id=str(row["id"]))
                session.add(restaurant)

            restaurant.name = str(row["name"])
            restaurant.city = str(row["city"])
            restaurant.locality = str(row.get("locality") or "")
            restaurant.cuisines = str(row.get("cuisines") or "")
            restaurant.avg_cost_for_two = (
                float(row["avg_cost_for_two"]) if row.get("avg_cost_for_two") is not None else None
            )
            restaurant.rating = (
                float(row["rating"]) if row.get("rating") is not None else None
            )
            restaurant.votes = (
                int(row["votes"]) if row.get("votes") is not None else None
            )
            restaurant.features = ""  # placeholder for future tags


if __name__ == "__main__":
    clean_file = PROCESSED_DIR / "restaurants_clean.parquet"
    if not clean_file.exists():
        raise SystemExit(
            f"Clean file not found at {clean_file}. Run transform_restaurants.py first."
        )
    load_clean_to_db(clean_file)
    print("Loaded clean restaurants into database.")

