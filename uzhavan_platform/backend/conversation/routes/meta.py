"""Reference data (API contract §1): GET /api/meta/districts · /api/meta/crops · /api/meta/enums"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from backend.meta import catalog

router = APIRouter(prefix="/api/meta", tags=["Meta"])


def _envelope(data: Any, source: str, source_url: str | None, notes: list[dict] | None = None) -> dict[str, Any]:
    return {
        "data": data,
        "meta": {
            "source": source,
            "source_url": source_url,
            "kind": "reference",
            "retrieved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "observed_at": None,
            "location": None,
            "notes": notes or [],
        },
    }


@router.get("/districts")
async def districts() -> dict[str, Any]:
    src = catalog.district_source()
    return _envelope(
        catalog.districts(),
        source="GeoNames (district HQ coordinates); Tamil Mannvalam, TN Dept of Agriculture (Tamil names)",
        source_url=src["coordinates_url"],
        notes=[
            {"en": "Coordinates are the district headquarters town, not the district centre.", "ta": None},
            {"en": f"Tamil names: {src['tamil_names_url']}", "ta": None},
        ],
    )


@router.get("/crops")
async def crops() -> dict[str, Any]:
    return _envelope(catalog.CROPS, source="UZHAVAN reference list", source_url=None)


@router.get("/enums")
async def enums() -> dict[str, Any]:
    return _envelope(catalog.enums(), source="UZHAVAN reference list", source_url=None)
