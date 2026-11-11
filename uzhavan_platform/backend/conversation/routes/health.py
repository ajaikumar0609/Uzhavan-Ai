"""
GET /health — liveness check
GET /metrics — platform metrics snapshot
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from backend.session.metrics import MetricsSnapshot, get_metrics
from backend.shared.models.version import PlatformVersion

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: dict[str, str]


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=PlatformVersion.current().model_dump(),
    )


@router.get("/metrics", response_model=MetricsSnapshot)
async def metrics() -> MetricsSnapshot:
    return get_metrics().snapshot()


@router.get("/health/config")
async def health_config() -> dict:
    """FP-007 AC-9: which features are configured, as booleans only. 404 in production."""
    from pathlib import Path

    from backend.shared.api_errors import not_found
    from backend.shared.db import database_reachable, redis_reachable
    from backend.shared.settings import PROJECT_ROOT, get_settings

    s = get_settings()
    if s.is_production:
        raise not_found()
    chroma = Path(s.CHROMA_PATH)
    if not chroma.is_absolute():
        chroma = PROJECT_ROOT / chroma
    llm_set = s.LLM_PROVIDER == "ollama"   # the only (local) provider
    return {
        "env": s.ENV,
        "llm_provider_set": llm_set,
        "database_reachable": await database_reachable(),
        "redis_reachable": await redis_reachable(),
        "chroma_present": chroma.exists(),
        "disease_service_url_set": bool(s.DISEASE_SERVICE_URL),
    }
