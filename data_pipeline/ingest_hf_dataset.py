import os
from pathlib import Path

from datasets import load_dataset
from dotenv import load_dotenv


load_dotenv()

HF_DATASET_NAME = os.getenv("HF_DATASET_NAME", "ManikaSaini/zomato-restaurant-recommendation")
HF_DATASET_SPLIT = os.getenv("HF_DATASET_SPLIT", "train")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def fetch_and_store_raw() -> Path:
    """Fetch latest dataset snapshot from Hugging Face and store as parquet."""
    ensure_dirs()
    ds = load_dataset(HF_DATASET_NAME, split=HF_DATASET_SPLIT)
    output_path = RAW_DIR / "zomato_raw.parquet"
    ds.to_parquet(str(output_path))
    return output_path


if __name__ == "__main__":
    path = fetch_and_store_raw()
    print(f"Saved raw dataset to {path}")

