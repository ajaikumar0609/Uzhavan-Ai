"""Helpers shared by API tests."""
from __future__ import annotations

from httpx import AsyncClient

from tests.fakes import CapturingSmsProvider


async def login(client: AsyncClient, sms: CapturingSmsProvider, phone: str = "9876543210") -> dict:
    """Run send-otp + verify-otp and return the verify response body."""
    r = await client.post("/api/auth/send-otp", json={"phone": phone})
    assert r.status_code == 200, r.text
    r = await client.post("/api/auth/verify-otp", json={"phone": phone, "otp": sms.last_for(phone)})
    assert r.status_code == 200, r.text
    return r.json()


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
