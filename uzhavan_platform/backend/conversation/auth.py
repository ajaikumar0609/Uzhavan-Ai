"""
JWT authentication for the Conversation API.

Uses the single JWT implementation in backend/auth/tokens.py, so access tokens issued
by /api/auth/verify-otp and /api/auth/refresh are accepted here.
Without a token, returns "anonymous" only when ALLOW_ANONYMOUS is true
(default true in development/test, forced false in production by the settings module).
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header

from backend.auth.deps import _bearer, farmer_from_token, settings_dep
from backend.auth.tokens import create_access_token
from backend.shared.api_errors import unauthenticated
from backend.shared.settings import Settings

ANONYMOUS_FARMER_ID = "anonymous"


async def get_farmer_id(
    authorization: Optional[str] = Header(default=None),
    settings: Settings = Depends(settings_dep),
) -> str:
    """FastAPI dependency. Returns farmer_id from the access JWT, or 'anonymous' if allowed.
    Raises 401 if a token is present but invalid, or absent while anonymous access is off."""
    token = _bearer(authorization)
    if token is None:
        if settings.allow_anonymous:
            return ANONYMOUS_FARMER_ID
        raise unauthenticated("Authorization header required")
    return farmer_from_token(token, settings).farmer_id


def create_token(farmer_id: str, district: str | None = None, phone: str = "") -> str:
    """Issue an access token (tests and tooling). `district` is accepted for backward
    compatibility and ignored: the profile is the source of truth for the district."""
    return create_access_token(farmer_id, phone)
