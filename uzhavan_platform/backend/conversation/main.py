"""
UZHAVAN AI — Conversation API (single app on :8000, API contract M-06 §0)

FastAPI application entry point.
Session Engine: transport, auth, session, SSE. The Cognitive Engine owns reasoning.
Also mounts auth (FP-008), farmer profile + farms (FP-009) and meta routers.

Settings are validated at import (FP-007): the app refuses to start on missing/unsafe config.

Run:
  .venv/bin/uvicorn backend.conversation.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from backend.shared.settings import SettingsError, get_settings

try:
    settings = get_settings()
except SettingsError as _exc:
    print(f"\nUZHAVAN start-up refused. {_exc}\n", file=sys.stderr, flush=True)
    raise SystemExit(1) from None

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from backend.conversation.routes.auth import router as auth_router  # noqa: E402
from backend.conversation.routes.conversation import router as conversation_router  # noqa: E402
from backend.conversation.routes.diary import router as diary_router  # noqa: E402
from backend.conversation.routes.disease_scan import router as disease_scan_router  # noqa: E402
from backend.conversation.routes.farms import router as farms_router  # noqa: E402
from backend.conversation.routes.health import router as health_router  # noqa: E402
from backend.conversation.routes.market import router as market_router  # noqa: E402
from backend.conversation.routes.meta import router as meta_router  # noqa: E402
from backend.conversation.routes.profile import router as profile_router  # noqa: E402
from backend.conversation.routes.satellite import router as satellite_router  # noqa: E402
from backend.conversation.routes.schemes import router as schemes_router  # noqa: E402
from backend.conversation.routes.soil import router as soil_router  # noqa: E402
from backend.conversation.routes.voice import router as voice_router  # noqa: E402
from backend.conversation.routes.weather import router as weather_router  # noqa: E402
from backend.shared.db import close_all  # noqa: E402
from backend.shared.models.version import PlatformVersion  # noqa: E402

logger = logging.getLogger("uzhavan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.warning("UZHAVAN starting: ENV=%s, anonymous=%s, OTP dev log=%s",
                   settings.ENV, settings.allow_anonymous, settings.otp_dev_log_enabled)
    yield
    await close_all()


app = FastAPI(
    title="UZHAVAN AI",
    description="AI Operating System for Tamil Nadu Farmers",
    version=PlatformVersion.current().ai_version,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    lifespan=lifespan,
)

# CORS: origins from CORS_ORIGINS (FP-007 AC-6); PUT/PATCH/DELETE allowed for profile/farms.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["Retry-After"],
)


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
    """500 without a stack trace (API contract §0)."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": {"code": "internal_error", "message": {"en": "Something went wrong", "ta": None}}},
    )


app.include_router(health_router, tags=["Platform"])
app.include_router(conversation_router, tags=["Conversation"])
app.include_router(voice_router, tags=["Voice"])
app.include_router(disease_scan_router)
app.include_router(meta_router)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(farms_router)
app.include_router(diary_router)
app.include_router(weather_router)
app.include_router(market_router)
app.include_router(schemes_router)
app.include_router(soil_router)
app.include_router(satellite_router)
