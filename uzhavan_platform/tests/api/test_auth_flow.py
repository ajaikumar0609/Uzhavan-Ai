"""FP-008: full OTP flow, refresh rotation, reuse revocation, logout, rate limits,
production fail-closed OTP delivery, dev-only OTP logging, shared JWT with /conversation."""

import logging

import pytest

from backend.auth.deps import settings_dep
from backend.auth.sms import DevLogSmsProvider, NoDeliveryProvider, build_sms_provider
from backend.auth.tokens import create_access_token, decode_access_token
from backend.conversation.auth import get_farmer_id
from backend.shared.settings import Settings
from tests.helpers import bearer, login

PHONE = "9123456780"


def _settings(**kw) -> Settings:
    base = {"ENV": "test", "JWT_SECRET": "test-secret-key-32chars-minimum!!!"}
    return Settings(**{**base, **kw})


async def test_full_flow_send_verify_refresh_reuse_logout(api_client, sms_capture, memory_repo, fake_redis):
    tokens = await login(api_client, sms_capture, PHONE)
    claims = decode_access_token(tokens["access_token"])
    assert claims["typ"] == "access" and claims["phone"] == PHONE
    assert claims["exp"] - claims["iat"] == 900
    farmer_id = claims["sub"]

    # OTP is stored hashed, never in plaintext.
    stored = memory_repo.otps[-1]
    assert stored["otp_hash"] != sms_capture.last_for(PHONE) and len(stored["otp_hash"]) == 64
    assert stored["verified"] is True

    # Refresh rotates both tokens.
    r1 = await api_client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r1.status_code == 200
    rotated = r1.json()
    assert rotated["refresh_token"] != tokens["refresh_token"]
    assert decode_access_token(rotated["access_token"])["sub"] == farmer_id

    # Reusing the old (revoked) refresh token -> 401 and ALL the farmer's tokens are revoked.
    r2 = await api_client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r2.status_code == 401
    r3 = await api_client.post("/api/auth/refresh", json={"refresh_token": rotated["refresh_token"]})
    assert r3.status_code == 401

    # Sign in again; logout revokes the refresh token.
    await fake_redis.delete(f"otp:cooldown:{PHONE}")  # skip the 60 s resend cooldown
    fresh = await login(api_client, sms_capture, PHONE)
    assert fresh["is_new_farmer"] is False
    lo = await api_client.post("/api/auth/logout", json={"refresh_token": fresh["refresh_token"]},
                               headers=bearer(fresh["access_token"]))
    assert lo.status_code == 204
    r4 = await api_client.post("/api/auth/refresh", json={"refresh_token": fresh["refresh_token"]})
    assert r4.status_code == 401


async def test_logout_requires_token(api_client):
    r = await api_client.post("/api/auth/logout", json={"refresh_token": "x"})
    assert r.status_code == 401


async def test_refresh_with_unknown_token(api_client):
    r = await api_client.post("/api/auth/refresh", json={"refresh_token": "nope"})
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "unauthenticated"


async def test_hourly_limit_via_api(api_client, fake_redis):
    for _ in range(3):
        await fake_redis.delete(f"otp:cooldown:{PHONE}")
        assert (await api_client.post("/api/auth/send-otp", json={"phone": PHONE})).status_code == 200
    await fake_redis.delete(f"otp:cooldown:{PHONE}")
    r = await api_client.post("/api/auth/send-otp", json={"phone": PHONE})
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) > 60


async def test_cooldown_via_api(api_client):
    assert (await api_client.post("/api/auth/send-otp", json={"phone": PHONE})).status_code == 200
    r = await api_client.post("/api/auth/send-otp", json={"phone": PHONE})
    assert r.status_code == 429 and 0 < int(r.headers["Retry-After"]) <= 60


async def test_production_without_sms_provider_returns_503_and_logs_nothing(
    api_client, memory_repo, caplog,
):
    from backend.auth.deps import get_sms_provider
    from backend.conversation.main import app

    prod = _settings(ENV="production", JWT_SECRET="p" * 48, DATABASE_URL="postgresql://x",
                     REDIS_URL="redis://x", CORS_ORIGINS="https://a", ALLOW_ANONYMOUS=False)
    app.dependency_overrides[settings_dep] = lambda: prod
    app.dependency_overrides.pop(get_sms_provider)  # use the real provider selection
    caplog.set_level(logging.DEBUG)
    r = await api_client.post("/api/auth/send-otp", json={"phone": PHONE})
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == "otp_delivery_not_configured"
    assert memory_repo.otps == []  # nothing generated or stored
    import re
    app_records = [rec for rec in caplog.records if rec.name.startswith("uzhavan")]
    assert not any("otp" in rec.getMessage().lower() for rec in app_records)
    assert not any(re.search(r"\b\d{6}\b", rec.getMessage()) for rec in caplog.records)


def test_provider_selection_matrix():
    assert isinstance(build_sms_provider(_settings(ENV="development", OTP_DEV_LOG=True)), DevLogSmsProvider)
    assert isinstance(build_sms_provider(_settings(ENV="development", OTP_DEV_LOG=False)), NoDeliveryProvider)
    assert isinstance(build_sms_provider(_settings(ENV="test", OTP_DEV_LOG=True)), NoDeliveryProvider)
    assert build_sms_provider(_settings(ENV="production")) is None
    # Stub providers without credentials are "not configured".
    assert build_sms_provider(_settings(ENV="production", SMS_PROVIDER="msg91")) is None
    assert build_sms_provider(_settings(ENV="production", SMS_PROVIDER="twilio")) is None


async def test_dev_log_provider_logs_only_in_dev(caplog):
    caplog.set_level(logging.DEBUG)
    await NoDeliveryProvider().send_otp(PHONE, "424242")
    assert "424242" not in caplog.text
    await DevLogSmsProvider().send_otp(PHONE, "424242")
    assert "424242" in caplog.text


async def test_access_token_accepted_by_conversation_dependency(api_client, sms_capture):
    tokens = await login(api_client, sms_capture, PHONE)
    fid = await get_farmer_id(authorization=f"Bearer {tokens['access_token']}", settings=_settings())
    assert fid == decode_access_token(tokens["access_token"])["sub"]


async def test_conversation_dependency_rejects_bad_token_and_anonymous_in_production():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as e:
        await get_farmer_id(authorization="Bearer junk", settings=_settings())
    assert e.value.status_code == 401
    prod = _settings(ENV="production", ALLOW_ANONYMOUS=False)
    with pytest.raises(HTTPException):
        await get_farmer_id(authorization=None, settings=prod)
    assert await get_farmer_id(authorization=None, settings=_settings()) == "anonymous"


def test_token_signed_with_other_secret_rejected():
    from backend.auth.tokens import TokenError
    tok = create_access_token("f1", PHONE, secret="other-secret-" * 4)
    with pytest.raises(TokenError):
        decode_access_token(tok)
