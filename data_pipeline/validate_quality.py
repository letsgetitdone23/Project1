from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR / "reports"


@dataclass
class QualityReport:
    total_rows: int
    missing_name: int
    missing_city: int
    rating_out_of_range: int
    cost_missing: int


def run_quality_checks(clean_path: Path) -> Dict:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(clean_path)

    total_rows = len(df)
    missing_name = int(df["name"].isna().sum())
    missing_city = int(df["city"].isna().sum())
    rating_out_of_range = int(
        df["rating"].dropna().map(lambda x: x < 0 or x > 5).sum()
    )
    cost_missing = int(df["avg_cost_for_two"].isna().sum())

    report = QualityReport(
        total_rows=total_rows,
        missing_name=missing_name,
        missing_city=missing_city,
        rating_out_of_range=rating_out_of_range,
        cost_missing=cost_missing,
    )

    payload = asdict(report)
    report_path = REPORTS_DIR / "last_quality_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return payload


if __name__ == "__main__":
    clean_file = PROCESSED_DIR / "restaurants_clean.parquet"
    if not clean_file.exists():
        raise SystemExit(
            f"Clean file not found at {clean_file}. Run transform_restaurants.py first."
        )
    result = run_quality_checks(clean_file)
    print("Quality report:")
    print(json.dumps(result, indent=2))

