from __future__ import annotations

from threading import Lock


class MetricsStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._values = {
            "interview_latency": [],
            "ws_disconnect_rate": 0,
            "stt_failure_rate": 0,
            "turn_completion_rate": 0,
            "model_cost_per_interview": {},
            "integrity_event_rate": 0,
        }

    def record_interview_latency(self, latency_ms: float) -> None:
        with self._lock:
            bucket = self._values["interview_latency"]
            bucket.append(float(latency_ms))
            if len(bucket) > 500:
                del bucket[:-500]

    def increment_ws_disconnect(self) -> None:
        with self._lock:
            self._values["ws_disconnect_rate"] += 1

    def increment_stt_failure(self) -> None:
        with self._lock:
            self._values["stt_failure_rate"] += 1

    def increment_turn_completion(self) -> None:
        with self._lock:
            self._values["turn_completion_rate"] += 1

    def add_model_cost(self, session_id: str, cost_usd: float) -> None:
        with self._lock:
            per_session = self._values["model_cost_per_interview"]
            per_session[session_id] = round(float(per_session.get(session_id, 0.0)) + float(cost_usd), 6)

    def increment_integrity_event(self) -> None:
        with self._lock:
            self._values["integrity_event_rate"] += 1

    def snapshot(self) -> dict:
        with self._lock:
            latencies = list(self._values["interview_latency"])
            avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
            return {
                "interview_latency": {"avg_ms": avg_latency, "sample_size": len(latencies)},
                "ws_disconnect_rate": int(self._values["ws_disconnect_rate"]),
                "stt_failure_rate": int(self._values["stt_failure_rate"]),
                "turn_completion_rate": int(self._values["turn_completion_rate"]),
                "model_cost_per_interview": dict(self._values["model_cost_per_interview"]),
                "integrity_event_rate": int(self._values["integrity_event_rate"]),
            }


metrics_store = MetricsStore()
