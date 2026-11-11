"""OTP generation and HMAC-SHA256 hashing (FP-008).

- 6 digits from `secrets` (CSPRNG). There is no universal or test OTP.
- Stored as HMAC-SHA256(server_key, "phone:otp"), never in plaintext.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

OTP_EXPIRY_SECONDS = 300   # 5 minutes
OTP_LENGTH = 6
OTP_MAX_ATTEMPTS = 5


def generate_otp() -> str:
    return f"{secrets.randbelow(10 ** OTP_LENGTH):0{OTP_LENGTH}d}"


def _key(key: Optional[bytes]) -> bytes:
    if key is not None:
        return key
    from backend.shared.settings import get_settings
    return get_settings().otp_hmac_key


def hash_otp(otp: str, phone: str, key: Optional[bytes] = None) -> str:
    """HMAC-SHA256 hex digest (64 chars) keyed with the server OTP key."""
    return hmac.new(_key(key), f"{phone}:{otp}".encode(), hashlib.sha256).hexdigest()


def verify_otp_hash(candidate: str, phone: str, stored_hash: str, key: Optional[bytes] = None) -> bool:
    return hmac.compare_digest(hash_otp(candidate, phone, key), stored_hash)


def otp_expiry(now: Optional[datetime] = None) -> datetime:
    return (now or datetime.now(timezone.utc)) + timedelta(seconds=OTP_EXPIRY_SECONDS)
