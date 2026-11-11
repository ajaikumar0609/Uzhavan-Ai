"""Deprecated shim: the single JWT implementation lives in backend/auth/tokens.py (FP-008)."""
from backend.auth.tokens import (  # noqa: F401
    ACCESS_TOKEN_SECONDS, JWT_ALGORITHM, REFRESH_TOKEN_DAYS, TokenError, create_access_token,
    decode_access_token, hash_refresh_token, new_refresh_token,
)
