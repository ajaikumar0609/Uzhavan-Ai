"""FastAPI dependencies shared by the auth, profile, farm and conversation routes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header

from backend.auth.repository import PostgresRepository, Repository
from backend.auth.sms import SmsProvider, build_sms_provider
from backend.auth.tokens import TokenError, decode_access_token
from backend.shared.api_errors import unauthenticated
from backend.shared.db import get_pool, get_redis_client
from backend.shared.settings import Settings, get_settings


def settings_dep() -> Settings:
    return get_settings()


async def get_repository() -> Repository:
    return PostgresRepository(await get_pool())


def get_redis():
    return get_redis_client()


def get_sms_provider(settings: Settings = Depends(settings_dep)) -> Optional[SmsProvider]:
    return build_sms_provider(settings)


@dataclass
class CurrentFarmer:
    farmer_id: str
    phone: str


def _bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise unauthenticated("Authorization header must be: Bearer <token>")
    return token.strip()


def farmer_from_token(token: str, settings: Settings) -> CurrentFarmer:
    try:
        payload = decode_access_token(token, secret=settings.JWT_SECRET)
    except TokenError as exc:
        raise unauthenticated("Token expired" if str(exc) == "expired" else "Invalid token") from None
    return CurrentFarmer(farmer_id=str(payload["sub"]), phone=str(payload.get("phone", "")))


async def get_current_farmer(
    authorization: Optional[str] = Header(default=None),
    settings: Settings = Depends(settings_dep),
) -> CurrentFarmer:
    """Strict: 401 unauthenticated without a valid access token."""
    token = _bearer(authorization)
    if token is None:
        raise unauthenticated()
    return farmer_from_token(token, settings)


def get_repository_factory():
    """The repository factory without opening a DB pool (for routes that need it only sometimes)."""
    return get_repository


async def get_optional_farmer(
    authorization: Optional[str] = Header(default=None),
    settings: Settings = Depends(settings_dep),
) -> Optional[CurrentFarmer]:
    """None without a token; 401 for a malformed/invalid token."""
    token = _bearer(authorization)
    return None if token is None else farmer_from_token(token, settings)
