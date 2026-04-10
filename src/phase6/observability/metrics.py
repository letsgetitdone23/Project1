from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, List


@dataclass
class MetricsState:
    total_requests: int = 0
    success_requests: int = 0
    not_found_requests: int = 0
    fallback_count: int = 0
    llm_failure_count: int = 0
    api_latency_ms: List[float] = field(default_factory=list)
    retrieval_latency_ms: List[float] = field(default_factory=list)
    llm_latency_ms: List[float] = field(default_factory=list)


class InMemoryMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._state = MetricsState()

    def record_request(self) -> None:
        with self._lock:
            self._state.total_requests += 1

    def record_success(self, used_fallback: bool) -> None:
        with self._lock:
            self._state.success_requests += 1
            if used_fallback:
                self._state.fallback_count += 1

    def record_not_found(self) -> None:
        with self._lock:
            self._state.not_found_requests += 1

    def record_llm_failure(self) -> None:
        with self._lock:
            self._state.llm_failure_count += 1

    def record_api_latency(self, value_ms: float) -> None:
        with self._lock:
            self._state.api_latency_ms.append(value_ms)

    def record_retrieval_latency(self, value_ms: float) -> None:
        with self._lock:
            self._state.retrieval_latency_ms.append(value_ms)

    def record_llm_latency(self, value_ms: float) -> None:
        with self._lock:
            self._state.llm_latency_ms.append(value_ms)

    @staticmethod
    def _summary(values: List[float]) -> Dict[str, float]:
        if not values:
            return {"count": 0, "avg_ms": 0.0, "p95_ms": 0.0}
        sorted_values = sorted(values)
        idx = int(0.95 * (len(sorted_values) - 1))
        p95 = sorted_values[idx]
        avg = sum(sorted_values) / len(sorted_values)
        return {"count": len(sorted_values), "avg_ms": round(avg, 2), "p95_ms": round(p95, 2)}

    def snapshot(self) -> Dict:
        with self._lock:
            state = self._state
            fallback_rate = (
                (state.fallback_count / state.success_requests) if state.success_requests else 0.0
            )
            return {
                "totals": {
                    "total_requests": state.total_requests,
                    "success_requests": state.success_requests,
                    "not_found_requests": state.not_found_requests,
                    "fallback_count": state.fallback_count,
                    "llm_failure_count": state.llm_failure_count,
                    "fallback_rate": round(fallback_rate, 4),
                },
                "latency": {
                    "api": self._summary(state.api_latency_ms),
                    "retrieval": self._summary(state.retrieval_latency_ms),
                    "llm": self._summary(state.llm_latency_ms),
                },
            }


metrics_store = InMemoryMetrics()

