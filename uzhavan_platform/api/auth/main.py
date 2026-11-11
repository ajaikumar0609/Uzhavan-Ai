"""UZHAVAN AI — standalone auth service (legacy entry point, kept for compatibility).

Since FP-008 the auth, profile, farm and meta routes are mounted on the MAIN app
(backend/conversation/main.py, port 8000). This module serves the very same routers,
so there is one implementation. Prefer the main app.
"""
from __future__ import annotations

import sys

from backend.shared.settings import SettingsError, get_settings

try:
    settings = get_settings()
except SettingsError as _exc:
    print(f"\nUZHAVAN auth start-up refused. {_exc}\n", file=sys.stderr, flush=True)
    raise SystemExit(1) from None

from contextlib import asynccontextmanager  # noqa: E402

from fastapi import FastAPI  # noqa: E402

from backend.conversation.routes.auth import router as auth_router  # noqa: E402
from backend.conversation.routes.farms import router as farms_router  # noqa: E402
from backend.conversation.routes.meta import router as meta_router  # noqa: E402
from backend.conversation.routes.profile import router as profile_router  # noqa: E402
from backend.shared.db import close_all  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_all()


app = FastAPI(title="UZHAVAN AI — Auth Service (legacy)", version="0.6.0", lifespan=lifespan)
for r in (meta_router, auth_router, profile_router, farms_router):
    app.include_router(r)


@app.get("/health", tags=["Ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
