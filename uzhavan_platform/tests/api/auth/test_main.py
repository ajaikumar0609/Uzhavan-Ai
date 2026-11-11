"""Auth API endpoint tests on the MAIN app (in-memory repository, fakeredis)."""

from datetime import datetime, timedelta, timezone

from backend.auth.otp import hash_otp, otp_expiry
from tests.helpers import bearer, login

PHONE = "9876543210"


async def test_send_otp_success(api_client, sms_capture):
    resp = await api_client.post("/api/auth/send-otp", json={"phone": PHONE})
    assert resp.status_code == 200
    assert resp.json() == {"status": "sent", "expires_in": 300, "resend_after": 60}
    assert sms_capture.last_for(PHONE) is not None


async def test_send_otp_invalid_phone(api_client):
    for bad in ("12345", "5876543210", "98765432101", "98765abcde"):
        resp = await api_client.post("/api/auth/send-otp", json={"phone": bad})
        assert resp.status_code == 400
        assert resp.json()["detail"]["code"] == "invalid_phone"


async def test_send_otp_rate_limited(api_client):
    await api_client.post("/api/auth/send-otp", json={"phone": PHONE})
    resp = await api_client.post("/api/auth/send-otp", json={"phone": PHONE})
    assert resp.status_code == 429
    assert resp.json()["detail"]["code"] == "rate_limited"
    assert int(resp.headers["Retry-After"]) > 0


async def test_verify_otp_success(api_client, sms_capture):
    body = await login(api_client, sms_capture, PHONE)
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 900
    assert body["is_new_farmer"] is True
    assert body["profile_complete"] is False
    assert body["access_token"] and body["refresh_token"]


async def test_verify_otp_wrong(api_client, sms_capture):
    await api_client.post("/api/auth/send-otp", json={"phone": PHONE})
    wrong = "000000" if sms_capture.last_for(PHONE) != "000000" else "111111"
    resp = await api_client.post("/api/auth/verify-otp", json={"phone": PHONE, "otp": wrong})
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "otp_incorrect"


async def test_verify_otp_expired(api_client, memory_repo):
    past = datetime.now(timezone.utc) - timedelta(minutes=10)
    await memory_repo.save_otp(PHONE, hash_otp("123456", PHONE), past)
    resp = await api_client.post("/api/auth/verify-otp", json={"phone": PHONE, "otp": "123456"})
    assert resp.status_code == 410
    assert resp.json()["detail"]["code"] == "otp_expired"


async def test_verify_otp_no_otp_found(api_client):
    resp = await api_client.post("/api/auth/verify-otp", json={"phone": PHONE, "otp": "123456"})
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "otp_not_found"


async def test_verify_otp_attempts_exceeded(api_client, memory_repo):
    await memory_repo.save_otp(PHONE, hash_otp("123456", PHONE), otp_expiry())
    for _ in range(5):
        r = await api_client.post("/api/auth/verify-otp", json={"phone": PHONE, "otp": "000000"})
        assert r.json()["detail"]["code"] == "otp_incorrect"
    # Even the right OTP is refused after 5 failed attempts.
    r = await api_client.post("/api/auth/verify-otp", json={"phone": PHONE, "otp": "123456"})
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "otp_attempts_exceeded"


async def test_profile_no_token(api_client):
    resp = await api_client.get("/api/farmer/profile")
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "unauthenticated"


async def test_profile_invalid_token(api_client):
    resp = await api_client.get("/api/farmer/profile", headers=bearer("invalid.jwt.token"))
    assert resp.status_code == 401


async def test_profile_success(api_client, sms_capture):
    tokens = await login(api_client, sms_capture, PHONE)
    resp = await api_client.get("/api/farmer/profile", headers=bearer(tokens["access_token"]))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["phone"] == PHONE
    assert data["name"] is None and data["profile_complete"] is False
