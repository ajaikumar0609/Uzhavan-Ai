"""Satellite status (API contract §11). No predictions are served while available is false."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.shared.envelope import envelope, note

router = APIRouter(prefix="/api/satellite", tags=["Satellite"])

SATELLITE_STATUS: dict[str, Any] = {
    "available": False,
    "reason": "under_validation",
    "gates": {
        "licence": False,
        "units": False,
        "geography_scope": "Cauvery Delta only",
        "independent_evaluation": "baseline only (val, 14 plots)",
    },
}


@router.get("/status")
async def satellite_status() -> dict[str, Any]:
    return envelope(
        SATELLITE_STATUS,
        source="UZHAVAN model registry",
        source_url=None,
        kind="reference",
        notes=[note("Satellite crop predictions are not served until every gate passes.")],
    )
