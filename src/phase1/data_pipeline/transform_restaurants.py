from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from dotenv import load_dotenv


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"


@dataclass
class ColumnMapping:
    id: str
    name: str
    city: str
    locality: Optional[str]
    cuisines: str
    cost_for_two: str
    rating: str
    votes: Optional[str]


def infer_column_mapping(df: pd.DataFrame) -> ColumnMapping:
    cols_lower: Dict[str, str] = {c.lower().strip(): c for c in df.columns}

    def pick(options) -> str:
        for opt in options:
            if opt.lower() in cols_lower:
                return cols_lower[opt.lower()]
        raise KeyError(f"None of {options} found in columns: {list(df.columns)}")

    def pick_optional(options) -> Optional[str]:
        try:
            return pick(options)
        except KeyError:
            return None

    return ColumnMapping(
        id=pick(["id", "restaurant id", "rest_id", "url"]),
        name=pick(["name", "restaurant name", "restaurant"]),
        city=pick(["city", "cityname", "listed_in(city)"]),
        locality=pick_optional(["locality", "address", "location"]),
        cuisines=pick(["cuisines", "cuisine"]),
        cost_for_two=pick(
            [
                "approx cost(for two people)",
                "approx_cost(for two people)",
                "cost for two",
                "average cost for two",
            ]
        ),
        rating=pick(["rating", "aggregate rating", "rating(out of 5)", "rate"]),
        votes=pick_optional(["votes", "rating votes"]),
    )


def normalize_cuisines(value: str) -> str:
    if not isinstance(value, str):
        return ""
    parts = [p.strip() for p in value.split(",") if p.strip()]
    return ", ".join(sorted(set(parts), key=str.lower))


def coerce_float(value) -> Optional[float]:
    try:
        text = str(value).replace(",", "").strip()
        if "/" in text:
            text = text.split("/")[0].strip()
        if text in {"NEW", "-", "nan", "NaN", ""}:
            return None
        return float(text)
    except Exception:
        return None


def coerce_int(value) -> Optional[int]:
    try:
        return int(str(value).replace(",", "").strip())
    except Exception:
        return None


def transform_raw_to_restaurants(raw_path: Path) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(raw_path)
    mapping = infer_column_mapping(df)
    transformed = pd.DataFrame()

    if mapping.id.lower() == "url":
        transformed["id"] = df[mapping.id].astype(str).map(
            lambda x: hashlib.md5(x.encode("utf-8")).hexdigest()
        )
    else:
        transformed["id"] = df[mapping.id].astype(str)

    transformed["name"] = df[mapping.name].astype(str)
    transformed["city"] = df[mapping.city].astype(str).str.strip().str.lower()
    transformed["locality"] = (
        df[mapping.locality].astype(str).str.strip() if mapping.locality else ""
    )
    transformed["cuisines"] = df[mapping.cuisines].map(normalize_cuisines)
    transformed["avg_cost_for_two"] = df[mapping.cost_for_two].map(coerce_float)
    transformed["rating"] = df[mapping.rating].map(coerce_float)
    transformed["votes"] = df[mapping.votes].map(coerce_int) if mapping.votes else None

    transformed["dedupe_key"] = (
        transformed["name"].str.lower()
        + "|"
        + transformed["city"]
        + "|"
        + transformed["locality"].fillna("").str.lower()
    )
    transformed = transformed.sort_values("rating", ascending=False)
    transformed = transformed.drop_duplicates(subset=["dedupe_key"]).drop(columns=["dedupe_key"])
    transformed["last_updated_at"] = datetime.utcnow().isoformat()

    output_path = PROCESSED_DIR / "restaurants_clean.parquet"
    transformed.to_parquet(output_path, index=False)
    return output_path

