"""Unit tests for OTP send limits (backend/auth/rate_limit.py) using fakeredis."""

import pytest

from backend.auth.rate_limit import MAX_OTP_PER_HOUR, check_and_reserve

PHONE = "9876543210"


async def _clear_cooldown(redis):
    await redis.delete(f"otp:cooldown:{PHONE}")


async def test_first_request_allowed(fake_redis):
    d = await check_and_reserve(fake_redis, PHONE)
    assert d.allowed and d.retry_after == 0


async def test_resend_within_cooldown_blocked(fake_redis):
    await check_and_reserve(fake_redis, PHONE)
    d = await check_and_reserve(fake_redis, PHONE)
    assert not d.allowed and d.reason == "cooldown"
    assert 0 < d.retry_after <= 60


async def test_third_request_allowed_fourth_blocked(fake_redis):
    for _ in range(MAX_OTP_PER_HOUR):
        await _clear_cooldown(fake_redis)
        assert (await check_and_reserve(fake_redis, PHONE)).allowed
    await _clear_cooldown(fake_redis)
    d = await check_and_reserve(fake_redis, PHONE)
    assert not d.allowed and d.reason == "hourly_limit"
    assert 3000 < d.retry_after <= 3600


async def test_first_request_sets_hour_window(fake_redis):
    await check_and_reserve(fake_redis, PHONE)
    assert 0 < await fake_redis.ttl(f"otp:hour:{PHONE}") <= 3600
