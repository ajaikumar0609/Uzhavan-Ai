"""Pluggable OTP delivery (FP-008).

- DevLogSmsProvider: logs the OTP; only selected when ENV=development AND OTP_DEV_LOG=true.
- NoDeliveryProvider: development/test without OTP_DEV_LOG; delivers nowhere, logs nothing.
- Msg91SmsProvider / TwilioSmsProvider: stubs. They read credentials from settings and raise
  SmsNotConfigured when absent. No external SMS API is called by this code yet.
- Production with no working provider -> None -> the route returns 503 otp_delivery_not_configured.
"""
from __future__ import annotations

import logging
from typing import Optional, Protocol

from backend.shared.settings import Settings

logger = logging.getLogger("uzhavan.auth.otp")


class SmsNotConfigured(Exception):
    pass


class SmsProvider(Protocol):
    name: str

    async def send_otp(self, phone: str, otp: str) -> None: ...


class DevLogSmsProvider:
    name = "dev-log"

    async def send_otp(self, phone: str, otp: str) -> None:
        # Selected only when ENV=development and OTP_DEV_LOG=true (see get_sms_provider).
        logger.warning("[DEV OTP] phone=%s otp=%s (ENV=development, OTP_DEV_LOG=true)", phone, otp)


class NoDeliveryProvider:
    """Development/test without OTP_DEV_LOG: the OTP is stored hashed but not delivered or logged."""
    name = "none"

    async def send_otp(self, phone: str, otp: str) -> None:
        return None


class Msg91SmsProvider:
    name = "msg91"

    def __init__(self, settings: Settings) -> None:
        if not (settings.MSG91_AUTH_KEY and settings.MSG91_TEMPLATE_ID):
            raise SmsNotConfigured("MSG91_AUTH_KEY and MSG91_TEMPLATE_ID are required")
        self._auth_key = settings.MSG91_AUTH_KEY
        self._template_id = settings.MSG91_TEMPLATE_ID
        self._sender_id = settings.MSG91_SENDER_ID

    async def send_otp(self, phone: str, otp: str) -> None:
        # Integration intentionally not wired: no external API call until an operator
        # supplies credentials and the integration is reviewed.
        raise SmsNotConfigured("MSG91 integration not implemented yet")


class TwilioSmsProvider:
    name = "twilio"

    def __init__(self, settings: Settings) -> None:
        if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM_NUMBER):
            raise SmsNotConfigured("TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER are required")
        self._sid = settings.TWILIO_ACCOUNT_SID
        self._token = settings.TWILIO_AUTH_TOKEN
        self._from = settings.TWILIO_FROM_NUMBER

    async def send_otp(self, phone: str, otp: str) -> None:
        raise SmsNotConfigured("Twilio integration not implemented yet")


def build_sms_provider(settings: Settings) -> Optional[SmsProvider]:
    """Return the configured provider, or None when OTP delivery is not possible."""
    try:
        if settings.SMS_PROVIDER == "msg91":
            return Msg91SmsProvider(settings)
        if settings.SMS_PROVIDER == "twilio":
            return TwilioSmsProvider(settings)
    except SmsNotConfigured:
        return None
    if settings.otp_dev_log_enabled:
        return DevLogSmsProvider()
    if settings.ENV in ("development", "test"):
        return NoDeliveryProvider()
    return None  # production without a provider
