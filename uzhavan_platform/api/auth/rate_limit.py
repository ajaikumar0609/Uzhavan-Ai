"""Deprecated shim: the implementation lives in backend/auth/rate_limit.py (FP-008)."""
from backend.auth.rate_limit import (  # noqa: F401
    MAX_OTP_PER_HOUR, RESEND_COOLDOWN_SECONDS, WINDOW_SECONDS, RateDecision, check_and_reserve,
)

MAX_OTP_REQUESTS = MAX_OTP_PER_HOUR
