"""Weather (FP-010, API contract §4): live Open-Meteo only, never historical, never a fallback value.

Location: farm_id 🔒 (its lat/lon, else its district HQ) › lat+lon › district_id (HQ point).
GET /api/weather/current · /api/weather/forecast?days=1..7 · /api/weather/advisories
Provider failure → 503 service_unavailable. Cache (Redis): current 30 min, forecast 3 h.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from backend.auth.deps import CurrentFarmer, get_optional_farmer, get_redis, get_repository_factory
from backend.knowledge.weather.advisories import evaluate, load_rules
from backend.knowledge.weather.open_meteo import (
    OPEN_METEO_SOURCE_URL, PointWeatherClient, WeatherProviderError,
)
from backend.meta.catalog import get_district, in_tn_bbox
from backend.shared.api_errors import api_error, not_found, service_unavailable, unauthenticated
from backend.shared.envelope import envelope, note

router = APIRouter(prefix="/api/weather", tags=["Weather"])

SOURCE = "Open-Meteo"
NOTE_NO_IMD = note("Official IMD warnings are not integrated. Check IMD / district administration alerts.")
NOTE_MODEL = note("Open-Meteo values are numerical weather model output, not station observations.")
NOTE_IST_DAYS = note("Daily dates are Asia/Kolkata calendar days; observed_at and retrieved_at are UTC.")


@dataclass
class ResolvedLocation:
    name: Optional[str]
    lat: float
    lon: float
    how: str                       # farm | farm_district (its district HQ point) | point | district_hq
    district_id: Optional[str] = None
    crop_id: Optional[str] = None
    crop_stage_id: Optional[str] = None

    def meta(self) -> dict[str, Any]:
        return {"name": self.name, "lat": self.lat, "lon": self.lon, "resolved_from": self.how,
                "district_id": self.district_id}


def get_weather_client(redis=Depends(get_redis)) -> PointWeatherClient:
    return PointWeatherClient(redis_client=redis)


async def resolve_location(
    farm_id: Optional[str] = Query(default=None),
    lat: Optional[float] = Query(default=None),
    lon: Optional[float] = Query(default=None),
    district_id: Optional[str] = Query(default=None),
    farmer: Optional[CurrentFarmer] = Depends(get_optional_farmer),
    repo_factory=Depends(get_repository_factory),
) -> ResolvedLocation:
    if farm_id:
        if farmer is None:
            raise unauthenticated("farm_id requires sign-in")
        repo = await repo_factory()
        farm = await repo.get_farm(farm_id)
        if farm is None or str(farm["farmer_id"]) != farmer.farmer_id:
            raise not_found("Farm not found")
        d = get_district(farm.get("district_id") or "")
        extra = {"district_id": farm.get("district_id"), "crop_id": farm.get("crop_id"),
                 "crop_stage_id": farm.get("crop_stage_id")}
        if farm.get("latitude") is not None and farm.get("longitude") is not None:
            return ResolvedLocation(farm.get("name"), farm["latitude"], farm["longitude"], "farm", **extra)
        if d is None:
            raise api_error(400, "location_required", "The farm has no location or district")
        return ResolvedLocation(d["name"]["en"], d["lat"], d["lon"], "farm_district", **extra)
    if lat is not None or lon is not None:
        if lat is None or lon is None:
            raise api_error(400, "invalid_location", "lat and lon must be given together")
        if not in_tn_bbox(lat, lon):
            raise api_error(400, "location_outside_tamil_nadu",
                            "Location must be inside Tamil Nadu (lat 8.0-13.6, lon 76.2-80.4)")
        return ResolvedLocation(None, lat, lon, "point")
    if district_id:
        d = get_district(district_id)
        if d is None:
            raise api_error(400, "invalid_district", "Unknown district_id; see /api/meta/districts")
        return ResolvedLocation(d["name"]["en"], d["lat"], d["lon"], "district_hq", district_id=district_id)
    raise api_error(400, "location_required", "Give farm_id, lat and lon, or district_id")


def _notes(loc: ResolvedLocation) -> list[dict]:
    n = [NOTE_NO_IMD, NOTE_MODEL]
    if loc.how in ("district_hq", "farm_district"):
        n.append(note("Weather is for the district headquarters town, not your field."))
    return n


@router.get("/current")
async def current(loc: ResolvedLocation = Depends(resolve_location),
                  client: PointWeatherClient = Depends(get_weather_client)) -> dict[str, Any]:
    try:
        res = await client.current(loc.lat, loc.lon)
    except WeatherProviderError:
        raise service_unavailable("Weather provider unavailable") from None
    return envelope(res["data"], source=SOURCE, source_url=OPEN_METEO_SOURCE_URL, kind="current",
                    observed_at=res["observed_at"], retrieved_at=res["retrieved_at"],
                    location=loc.meta(), notes=_notes(loc))


@router.get("/forecast")
async def forecast(days: int = Query(default=7, ge=1, le=7),
                   loc: ResolvedLocation = Depends(resolve_location),
                   client: PointWeatherClient = Depends(get_weather_client)) -> dict[str, Any]:
    try:
        res = await client.daily(loc.lat, loc.lon, days)
    except WeatherProviderError:
        raise service_unavailable("Weather provider unavailable") from None
    notes = _notes(loc) + [NOTE_IST_DAYS,
                           note("Open-Meteo does not report the forecast issue time, so observed_at is null.")]
    return envelope(res["data"], source=SOURCE, source_url=OPEN_METEO_SOURCE_URL, kind="forecast",
                    observed_at=res["observed_at"], retrieved_at=res["retrieved_at"],
                    location=loc.meta(), notes=notes)


@router.get("/advisories")
async def advisories(loc: ResolvedLocation = Depends(resolve_location),
                     client: PointWeatherClient = Depends(get_weather_client)) -> dict[str, Any]:
    try:
        res = await client.daily(loc.lat, loc.lon, 7)
    except WeatherProviderError:
        raise service_unavailable("Weather provider unavailable") from None
    fired = evaluate(load_rules(), res["data"]["daily"], loc.crop_id, loc.crop_stage_id)
    notes = _notes(loc) + [NOTE_IST_DAYS, note("Advisories come only from cited rules in advisory_rules.yaml; "
                                "crop-specific rules need a farm_id with crop and stage.")]
    return envelope(fired, source="UZHAVAN advisory rules on Open-Meteo forecast",
                    source_url=OPEN_METEO_SOURCE_URL, kind="forecast", observed_at=None,
                    retrieved_at=res["retrieved_at"], location=loc.meta(), notes=notes)
