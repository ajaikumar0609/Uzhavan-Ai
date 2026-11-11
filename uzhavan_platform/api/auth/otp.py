"""Deprecated shim: the implementation lives in backend/auth/otp.py (FP-008)."""
from backend.auth.otp import (  # noqa: F401
    OTP_EXPIRY_SECONDS, OTP_LENGTH, OTP_MAX_ATTEMPTS, generate_otp, hash_otp, otp_expiry, verify_otp_hash,
)
