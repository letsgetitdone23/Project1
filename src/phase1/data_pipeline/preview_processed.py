from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_FILE = PROJECT_ROOT / "data" / "processed" / "restaurants_clean.parquet"


def main() -> None:
    if not PROCESSED_FILE.exists():
        raise SystemExit(f"Processed file not found: {PROCESSED_FILE}")

    df = pd.read_parquet(PROCESSED_FILE)
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()

