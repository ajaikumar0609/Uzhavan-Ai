"""Tests for AUTH_DEMO_MODE (physical-phone showcase demo OTP).

Verifies:
1. Demo phone (9876543210) + demo OTP (123456) with AUTH_DEMO_MODE=true -> PASS
2. Demo phone + wrong OTP (999999) -> FAIL (400 otp_incorrect)
3. Other phone (9123456789) + demo OTP (123456) -> FAIL (does not bypass normal OTP)
4. AUTH_DEMO_MODE=false + demo OTP -> FAIL (normal OTP verification required)
5. Normal OTP flow remains fully intact
6. Valid JWT tokens and session claims generated for demo user
7. Production environment strictly forbids AUTH_DEMO_MODE=true (fail-closed SettingsError)
"""
import pytest
from httpx import AsyncClient

from backend.auth.deps import settings_dep
from backend.auth.tokens import decode_access_token
from backend.conversation.main import app
from backend.shared.settings import Settings, SettingsError
from tests.helpers import bearer, login


def _demo_settings(**kw) -> Settings:
    base = {
        "ENV": "development",
        "JWT_SECRET": "test-secret-key-32chars-minimum!!!",
        "AUTH_DEMO_MODE": True,
        "DEMO_PHONE_NUMBER": "9876543210",
        "DEMO_OTP": "123456",
        "SMS_PROVIDER": "none",
    }
    return Settings(**{**base, **kw})


async def test_demo_phone_and_demo_otp_success(api_client: AsyncClient):
    """1. Demo phone + demo OTP -> PASS without requiring SMS provider."""
    s = _demo_settings(AUTH_DEMO_MODE=True)
    app.dependency_overrides[settings_dep] = lambda: s

    try:
        # Send OTP for demo phone - succeeds even with SMS_PROVIDER=none
        r_send = await api_client.post("/api/auth/send-otp", json={"phone": "9876543210"})
        assert r_send.status_code == 200
        body_send = r_send.json()
        assert body_send["status"] == "sent"
        # Ensure OTP is NEVER exposed in the response
        assert "otp" not in body_send

        # Verify with exact demo OTP (123456)
        r_verify = await api_client.post("/api/auth/verify-otp", json={"phone": "9876543210", "otp": "123456"})
        assert r_verify.status_code == 200
        body = r_verify.json()
        assert "access_token" in body
        assert "refresh_token" in body
        claims = decode_access_token(body["access_token"], secret=s.JWT_SECRET)
        assert claims["phone"] == "9876543210"
        assert claims["typ"] == "access"
    finally:
        app.dependency_overrides.pop(settings_dep, None)


async def test_demo_phone_wrong_otp_fails(api_client: AsyncClient):
    """2. Demo phone + wrong OTP -> FAIL (400 otp_incorrect)."""
    s = _demo_settings(AUTH_DEMO_MODE=True)
    app.dependency_overrides[settings_dep] = lambda: s

    try:
        await api_client.post("/api/auth/send-otp", json={"phone": "9876543210"})
        r = await api_client.post("/api/auth/verify-otp", json={"phone": "9876543210", "otp": "999999"})
        assert r.status_code == 400
        assert r.json()["detail"]["code"] == "otp_incorrect"
    finally:
        app.dependency_overrides.pop(settings_dep, None)


async def test_other_phone_with_demo_otp_fails(api_client: AsyncClient, sms_capture):
    """3. Other phone + demo OTP (123456) -> FAIL (does not bypass normal OTP verification)."""
    s = _demo_settings(AUTH_DEMO_MODE=True)
    app.dependency_overrides[settings_dep] = lambda: s

    try:
        other_phone = "9876542222"
        # 3a. Normal random OTP sent via provider
        r_send = await api_client.post("/api/auth/send-otp", json={"phone": other_phone})
        assert r_send.status_code == 200
        # The captured random OTP is not 123456
        assert sms_capture.last_for(other_phone) != "123456"

        # 3b. Trying to verify other phone with demo OTP 123456 must FAIL
        r_verify = await api_client.post("/api/auth/verify-otp", json={"phone": other_phone, "otp": "123456"})
        assert r_verify.status_code == 400
        assert r_verify.json()["detail"]["code"] == "otp_incorrect"
    finally:
        app.dependency_overrides.pop(settings_dep, None)


async def test_demo_mode_disabled_fails_demo_otp(api_client: AsyncClient, sms_capture):
    """4. AUTH_DEMO_MODE=false + demo OTP -> FAIL (requires real random OTP)."""
    s = _demo_settings(AUTH_DEMO_MODE=False)
    app.dependency_overrides[settings_dep] = lambda: s

    try:
        # When demo mode is false, 9876543210 goes through normal random OTP flow
        r_send = await api_client.post("/api/auth/send-otp", json={"phone": "9876543210"})
        assert r_send.status_code == 200
        real_otp = sms_capture.last_for("9876543210")
        assert real_otp != "123456"

        # Attempting demo OTP 123456 fails
        r_verify = await api_client.post("/api/auth/verify-otp", json={"phone": "9876543210", "otp": "123456"})
        assert r_verify.status_code == 400
        assert r_verify.json()["detail"]["code"] == "otp_incorrect"

        # Verifying with the real captured OTP succeeds
        r_verify_real = await api_client.post("/api/auth/verify-otp", json={"phone": "9876543210", "otp": real_otp})
        assert r_verify_real.status_code == 200
    finally:
        app.dependency_overrides.pop(settings_dep, None)


def test_production_forbids_auth_demo_mode():
    """7. Production environment strictly forbids AUTH_DEMO_MODE=true."""
    with pytest.raises(SettingsError) as exc_info:
        Settings(
            ENV="production",
            JWT_SECRET="production-secret-key-that-is-at-least-32-chars-long",
            DATABASE_URL="postgresql://user:pass@host/db",
            REDIS_URL="redis://host:6379/0",
            CORS_ORIGINS="https://app.uzhavan.ai",
            ALLOW_ANONYMOUS=False,
            AUTH_DEMO_MODE=True,
            SMS_PROVIDER="msg91",
            MSG91_AUTH_KEY="dummy",
            MSG91_TEMPLATE_ID="dummy",
            MSG91_SENDER_ID="dummy",
        ).validate_for_env()

    assert "AUTH_DEMO_MODE: must not be true in production" in str(exc_info.value)
