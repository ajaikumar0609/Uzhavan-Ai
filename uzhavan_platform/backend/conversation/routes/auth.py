"""Auth routes (FP-008, API contract §2).

POST /api/auth/send-otp · POST /api/auth/verify-otp · POST /api/auth/refresh · POST /api/auth/logout 🔒
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel

from backend.auth.deps import (
    CurrentFarmer, get_current_farmer, get_redis, get_repository, get_sms_provider, settings_dep,
)
from backend.auth.otp import OTP_EXPIRY_SECONDS, OTP_MAX_ATTEMPTS, generate_otp, hash_otp, otp_expiry, verify_otp_hash
from backend.auth.rate_limit import RESEND_COOLDOWN_SECONDS, check_and_reserve
from backend.auth.repository import Repository
from backend.auth.sms import SmsNotConfigured, SmsProvider
from backend.auth.tokens import (
    ACCESS_TOKEN_SECONDS, create_access_token, hash_refresh_token, new_refresh_token, refresh_expiry,
)
from backend.conversation.routes.profile import is_profile_complete
from backend.shared.api_errors import api_error, service_unavailable, unauthenticated
from backend.shared.settings import Settings

logger = logging.getLogger("uzhavan.auth")
router = APIRouter(prefix="/api/auth", tags=["Auth"])

PHONE_RE = re.compile(r"^[6-9]\d{9}$")
OTP_RE = re.compile(r"^\d{6}$")


class SendOtpIn(BaseModel):
    phone: str


class SendOtpOut(BaseModel):
    status: str
    expires_in: int
    resend_after: int


class VerifyOtpIn(BaseModel):
    phone: str
    otp: str


class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_SECONDS


class VerifyOtpOut(TokenPairOut):
    is_new_farmer: bool
    profile_complete: bool


class RefreshIn(BaseModel):
    refresh_token: str


def _check_phone(phone: str) -> str:
    phone = phone.strip()
    if not PHONE_RE.match(phone):
        raise api_error(400, "invalid_phone", "Enter a valid 10-digit Indian mobile number")
    return phone


def _client_meta(request: Request) -> tuple[Optional[str], Optional[str]]:
    ua = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    return (ua[:500] if ua else None), ip


@router.post("/send-otp", response_model=SendOtpOut)
async def send_otp(
    body: SendOtpIn,
    repo: Repository = Depends(get_repository),
    redis=Depends(get_redis),
    sms: Optional[SmsProvider] = Depends(get_sms_provider),
    settings: Settings = Depends(settings_dep),
) -> SendOtpOut:
    phone = _check_phone(body.phone)
    is_demo = settings.AUTH_DEMO_MODE and phone == settings.DEMO_PHONE_NUMBER

    if not is_demo:
        # Fail closed before generating anything: production without an SMS provider.
        if sms is None:
            raise api_error(503, "otp_delivery_not_configured", "OTP delivery is not configured")

        try:
            decision = await check_and_reserve(redis, phone)
        except Exception as exc:  # Redis down -> no rate limiting -> refuse
            logger.error("OTP rate limiter unavailable: %s", type(exc).__name__)
            raise service_unavailable("Rate limiter unavailable") from None
        if not decision.allowed:
            raise api_error(
                429, "rate_limited",
                "Please wait before requesting another OTP" if decision.reason == "cooldown"
                else "Too many OTP requests. Try again later",
                headers={"Retry-After": str(decision.retry_after)},
            )

        otp = generate_otp()
        await repo.save_otp(phone, hash_otp(otp, phone), otp_expiry())
        try:
            await sms.send_otp(phone, otp)
        except SmsNotConfigured:
            raise api_error(503, "otp_delivery_not_configured", "OTP delivery is not configured") from None
    else:
        # Demo mode: save fixed demo OTP hash, bypass SMS provider, do not expose OTP in response.
        otp = settings.DEMO_OTP
        await repo.save_otp(phone, hash_otp(otp, phone), otp_expiry())
        logger.info("Demo OTP configured for %s (SMS delivery bypassed)", phone)

    return SendOtpOut(status="sent", expires_in=OTP_EXPIRY_SECONDS, resend_after=RESEND_COOLDOWN_SECONDS)


async def _issue_tokens(repo: Repository, farmer: dict, request: Request) -> tuple[str, str]:
    access = create_access_token(farmer["farmer_id"], farmer["phone"])
    raw, token_hash = new_refresh_token()
    ua, ip = _client_meta(request)
    await repo.save_refresh_token(farmer["farmer_id"], token_hash, refresh_expiry(), ua, ip)
    return access, raw


@router.post("/verify-otp", response_model=VerifyOtpOut)
async def verify_otp(
    body: VerifyOtpIn,
    request: Request,
    repo: Repository = Depends(get_repository),
    settings: Settings = Depends(settings_dep),
) -> VerifyOtpOut:
    phone = _check_phone(body.phone)
    otp = body.otp.strip()
    is_demo = settings.AUTH_DEMO_MODE and phone == settings.DEMO_PHONE_NUMBER

    if is_demo:
        if not OTP_RE.match(otp) or otp != settings.DEMO_OTP:
            raise api_error(400, "otp_incorrect", "Incorrect OTP")

        record = await repo.get_latest_otp(phone)
        if record is not None:
            await repo.mark_otp_verified(record["id"])

        farmer, is_new = await repo.upsert_farmer_by_phone(phone)
        access, refresh = await _issue_tokens(repo, farmer, request)
        return VerifyOtpOut(
            access_token=access,
            refresh_token=refresh,
            is_new_farmer=is_new,
            profile_complete=is_profile_complete(farmer),
        )

    record = await repo.get_latest_otp(phone)
    if record is None:
        raise api_error(404, "otp_not_found", "No OTP was requested for this number")

    expires_at = record["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        raise api_error(410, "otp_expired", "The OTP has expired. Request a new one")

    if record["attempts"] >= OTP_MAX_ATTEMPTS:
        raise api_error(400, "otp_attempts_exceeded", "Too many incorrect attempts. Request a new OTP")
    if await repo.consume_otp_attempt(record["id"]) is None:
        raise api_error(400, "otp_attempts_exceeded", "Too many incorrect attempts. Request a new OTP")

    if not OTP_RE.match(otp) or not verify_otp_hash(otp, phone, record["otp_hash"]):
        raise api_error(400, "otp_incorrect", "Incorrect OTP")

    await repo.mark_otp_verified(record["id"])
    farmer, is_new = await repo.upsert_farmer_by_phone(phone)
    access, refresh = await _issue_tokens(repo, farmer, request)
    return VerifyOtpOut(
        access_token=access,
        refresh_token=refresh,
        is_new_farmer=is_new,
        profile_complete=is_profile_complete(farmer),
    )


@router.post("/refresh", response_model=TokenPairOut)
async def refresh(
    body: RefreshIn,
    request: Request,
    repo: Repository = Depends(get_repository),
) -> TokenPairOut:
    raw_new, new_hash = new_refresh_token()
    ua, ip = _client_meta(request)
    status, farmer = await repo.rotate_refresh_token(
        hash_refresh_token(body.refresh_token), new_hash, refresh_expiry(), ua, ip,
    )
    if status == "reused":
        logger.warning("Refresh token reuse detected; all tokens of the farmer revoked")
        raise unauthenticated("Refresh token reuse detected; please sign in again")
    if status != "ok" or farmer is None:
        raise unauthenticated("Invalid or expired refresh token")
    access = create_access_token(farmer["farmer_id"], farmer["phone"])
    return TokenPairOut(access_token=access, refresh_token=raw_new)


@router.post("/logout", status_code=204)
async def logout(
    body: RefreshIn,
    farmer: CurrentFarmer = Depends(get_current_farmer),
    repo: Repository = Depends(get_repository),
) -> Response:
    await repo.revoke_refresh_token(farmer.farmer_id, hash_refresh_token(body.refresh_token))
    return Response(status_code=204)
