"""
PlatformMetrics — in-memory counters for GET /metrics.

Updated after every conversation turn.
Exposed at GET /metrics as a structured response.
"""
from __future__ import annotations

from pydantic import BaseModel


class PlatformMetrics:
    def __init__(self) -> None:
        self.total_requests: int = 0
        self.total_latency_ms: int = 0
        self.fallback_count: int = 0
        self.grounding_blocked: int = 0
        self.safety_blocked: int = 0
        self.intent_counts: dict[str, int] = {}
        self.agent_usage: dict[str, int] = {}
        self.cache_hit_count: int = 0
        self._confidence_sum: float = 0.0

    def record(
        self,
        intent: str,
        latency_ms: int,
        is_fallback: bool,
        grounding_passed: bool,
        safety_passed: bool,
        confidence: float,
        tools_used: list[str],
        cache_hits: int = 0,
    ) -> None:
        self.total_requests += 1
        self.total_latency_ms += latency_ms
        self._confidence_sum += confidence
        self.cache_hit_count += cache_hits

        if is_fallback:
            self.fallback_count += 1
        if not grounding_passed:
            self.grounding_blocked += 1
        if not safety_passed and grounding_passed:
            self.safety_blocked += 1

        self.intent_counts[intent] = self.intent_counts.get(intent, 0) + 1
        for tool in tools_used:
            self.agent_usage[tool] = self.agent_usage.get(tool, 0) + 1

    def snapshot(self) -> "MetricsSnapshot":
        n = max(self.total_requests, 1)
        return MetricsSnapshot(
            total_requests=self.total_requests,
            avg_latency_ms=round(self.total_latency_ms / n),
            fallback_rate=round(self.fallback_count / n, 3),
            grounding_block_rate=round(self.grounding_blocked / n, 3),
            safety_block_rate=round(self.safety_blocked / n, 3),
            avg_confidence=round(self._confidence_sum / n, 3),
            cache_hit_count=self.cache_hit_count,
            intent_distribution=dict(self.intent_counts),
            agent_usage=dict(self.agent_usage),
        )


class MetricsSnapshot(BaseModel):
    total_requests: int
    avg_latency_ms: int
    fallback_rate: float
    grounding_block_rate: float
    safety_block_rate: float
    avg_confidence: float
    cache_hit_count: int
    intent_distribution: dict[str, int]
    agent_usage: dict[str, int]


# Module-level singleton
_metrics = PlatformMetrics()


def get_metrics() -> PlatformMetrics:
    return _metrics
