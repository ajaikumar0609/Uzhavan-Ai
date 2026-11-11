"""Redis-backed OTP send limits (FP-008).

- 60 s resend cooldown per phone (SET NX EX).
- Max 3 sends per phone per rolling hour window (INCR + EXPIRE on first).
Redis unavailable -> the caller returns 503 (fail closed).
"""
from __future__ import annotations

from dataclasses import dataclass

RESEND_COOLDOWN_SECONDS = 60
MAX_OTP_PER_HOUR = 3
WINDOW_SECONDS = 3600


@dataclass
class RateDecision:
    allowed: bool
    retry_after: int = 0
    reason: str = ""


def _cooldown_key(phone: str) -> str:
    return f"otp:cooldown:{phone}"


def _hour_key(phone: str) -> str:
    return f"otp:hour:{phone}"


async def check_and_reserve(redis, phone: str) -> RateDecision:
    """Atomically claim the cooldown slot, then count the send against the hourly cap."""
    got_slot = await redis.set(_cooldown_key(phone), "1", nx=True, ex=RESEND_COOLDOWN_SECONDS)
    if not got_slot:
        ttl = await redis.ttl(_cooldown_key(phone))
        return RateDecision(False, max(int(ttl), 1), "cooldown")
    count = await redis.incr(_hour_key(phone))
    if count == 1:
        await redis.expire(_hour_key(phone), WINDOW_SECONDS)
    if count > MAX_OTP_PER_HOUR:
        ttl = await redis.ttl(_hour_key(phone))
        if ttl is None or int(ttl) < 0:  # key lost its TTL: repair so it can't block forever
            await redis.expire(_hour_key(phone), WINDOW_SECONDS)
            ttl = WINDOW_SECONDS
        return RateDecision(False, max(int(ttl), 1), "hourly_limit")
    return RateDecision(True)
