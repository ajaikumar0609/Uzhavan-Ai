"""
Token-bucket rate limiter per farmer_id.
20 requests/minute, 100 requests/24h.
In-memory for Phase F. Redis-backed in production.
"""
from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, status

from backend.shared.exceptions import RateLimitError

_PER_MINUTE = int(20)
_PER_DAY = int(100)

# {farmer_id: [(timestamp, count)]}  — sliding window buckets
_minute_buckets: dict[str, list[float]] = defaultdict(list)
_day_buckets: dict[str, list[float]] = defaultdict(list)


def _clean_window(timestamps: list[float], window_s: float) -> list[float]:
    cutoff = time.monotonic() - window_s
    return [t for t in timestamps if t > cutoff]


def check_rate_limit(farmer_id: str) -> None:
    """
    Raises HTTPException(429) if farmer_id exceeds rate limits.
    Call at the start of every conversation endpoint handler.
    """
    now = time.monotonic()

    # Per-minute window
    _minute_buckets[farmer_id] = _clean_window(_minute_buckets[farmer_id], 60)
    if len(_minute_buckets[farmer_id]) >= _PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {_PER_MINUTE} requests/minute",
            headers={"Retry-After": "60"},
        )

    # Per-day window
    _day_buckets[farmer_id] = _clean_window(_day_buckets[farmer_id], 86400)
    if len(_day_buckets[farmer_id]) >= _PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily limit exceeded: {_PER_DAY} requests/day",
            headers={"Retry-After": "86400"},
        )

    _minute_buckets[farmer_id].append(now)
    _day_buckets[farmer_id].append(now)
