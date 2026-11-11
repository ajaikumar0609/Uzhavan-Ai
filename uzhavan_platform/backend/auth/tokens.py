"""The ONE JWT implementation (PyJWT, HS256) for issuing and verifying tokens.

Access JWT: claims sub=farmer_id, phone, iat, exp, typ="access", jti; 15 minutes.
Refresh token: opaque random string; only its SHA-256 is stored; 30 days.
Used by the auth routes AND by the /conversation dependency.
"""
from __future__ import annotations

import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt

from backend.shared.settings import get_settings

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_SECONDS = 15 * 60
REFRESH_TOKEN_DAYS = 30


class TokenError(Exception):
    """Invalid, expired or wrong-type token."""


def _secret(secret: Optional[str]) -> str:
    return secret if secret is not None else get_settings().JWT_SECRET


def create_access_token(farmer_id: str, phone: str, secret: Optional[str] = None,
                        ttl_seconds: int = ACCESS_TOKEN_SECONDS) -> str:
    now = int(time.time())
    payload = {
        "sub": str(farmer_id),
        "phone": phone,
        "iat": now,
        "exp": now + ttl_seconds,
        "typ": "access",
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, _secret(secret), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str, secret: Optional[str] = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token, _secret(secret), algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp", "iat"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("invalid") from exc
    if payload.get("typ") != "access":
        raise TokenError("not an access token")
    return payload


def new_refresh_token() -> tuple[str, str]:
    """Returns (raw_token, sha256_hex). Store only the hash."""
    raw = secrets.token_urlsafe(48)
    return raw, hash_refresh_token(raw)


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def refresh_expiry(now: Optional[datetime] = None) -> datetime:
    return (now or datetime.now(timezone.utc)) + timedelta(days=REFRESH_TOKEN_DAYS)
