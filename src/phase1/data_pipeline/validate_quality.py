from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
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
    report = QualityReport(
        total_rows=len(df),
        missing_name=int(df["name"].isna().sum()),
        missing_city=int(df["city"].isna().sum()),
        rating_out_of_range=int(df["rating"].dropna().map(lambda x: x < 0 or x > 5).sum()),
        cost_missing=int(df["avg_cost_for_two"].isna().sum()),
    )
    payload = asdict(report)
    with (REPORTS_DIR / "last_quality_report.json").open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return payload

