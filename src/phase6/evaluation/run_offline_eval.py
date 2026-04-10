from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.phase0.app import app


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BENCHMARK_FILE = PROJECT_ROOT / "src" / "phase6" / "evaluation" / "benchmark_profiles.json"
REPORT_FILE = PROJECT_ROOT / "data" / "reports" / "offline_eval_report.json"


def run() -> dict:
    profiles = json.loads(BENCHMARK_FILE.read_text(encoding="utf-8"))
    client = TestClient(app)

    results = []
    for profile in profiles:
        response = client.post("/v1/recommendations", json=profile["input"])
        body = {}
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text}

        results.append(
            {
                "name": profile["name"],
                "status_code": response.status_code,
                "used_fallback": body.get("used_fallback"),
                "timing_ms": body.get("timing_ms"),
                "recommendation_count": len(body.get("recommendations", []))
                if isinstance(body, dict)
                else 0,
            }
        )

    payload = {"profiles": results}
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

