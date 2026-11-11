"""Farms (FP-009, API contract §3) 🔒 own farms only; max 5 per farmer.

GET /api/farms · POST /api/farms · PUT /api/farms/{farm_id} (partial) · DELETE /api/farms/{farm_id}
Another farmer's farm is reported as 404 not_found (no existence leak).
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from backend.auth.deps import CurrentFarmer, get_current_farmer, get_repository
from backend.auth.repository import FARM_COLUMNS, Repository
from backend.conversation.routes.profile import _iso
from backend.meta.catalog import (
    CROP_IDS, CROP_STAGE_IDS, IRRIGATION_TYPE_IDS, SEASON_IDS, get_district, in_tn_bbox,
)
from backend.shared.api_errors import api_error, not_found

router = APIRouter(prefix="/api/farms", tags=["Farms"])

MAX_FARMS = 5
MAX_AREA_HA = 10000.0


class FarmIn(BaseModel):
    name: Optional[str] = None
    district_id: Optional[str] = None
    village: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    boundary_geojson: Optional[dict[str, Any]] = None
    area_ha: Optional[float] = None
    crop_id: Optional[str] = None
    crop_stage_id: Optional[str] = None
    season_id: Optional[str] = None
    irrigation_type_id: Optional[str] = None


def farm_out(f: dict[str, Any]) -> dict[str, Any]:
    return {
        "farm_id": str(f["farm_id"]),
        "name": f["name"],
        "district_id": f["district_id"],
        "village": f.get("village"),
        "latitude": f.get("latitude"),
        "longitude": f.get("longitude"),
        "area_ha": f.get("area_ha"),
        "crop_id": f.get("crop_id"),
        "crop_stage_id": f.get("crop_stage_id"),
        "season_id": f.get("season_id"),
        "irrigation_type_id": f.get("irrigation_type_id"),
        "boundary_geojson": f.get("boundary_geojson"),
        "created_at": _iso(f.get("created_at")),
        "updated_at": _iso(f.get("updated_at")),
    }


def _validate(merged: dict[str, Any]) -> None:
    name = merged.get("name")
    if not name or not 1 <= len(name) <= 100:
        raise api_error(400, "invalid_name", "Farm name must be 1 to 100 characters")
    if get_district(merged.get("district_id") or "") is None:
        raise api_error(400, "invalid_district", "Unknown district_id; see /api/meta/districts")
    village = merged.get("village")
    if village is not None and len(village) > 100:
        raise api_error(400, "invalid_village", "Village must be at most 100 characters")
    lat, lon = merged.get("latitude"), merged.get("longitude")
    if (lat is None) != (lon is None):
        raise api_error(400, "invalid_location", "latitude and longitude must be given together")
    if lat is not None and not in_tn_bbox(lat, lon):
        raise api_error(400, "location_outside_tamil_nadu",
                        "Location must be inside Tamil Nadu (lat 8.0-13.6, lon 76.2-80.4)")
    area = merged.get("area_ha")
    if area is not None and not 0 < area <= MAX_AREA_HA:
        raise api_error(400, "invalid_area", "area_ha must be greater than 0 and at most 10000")
    geo = merged.get("boundary_geojson")
    if geo is not None and not (isinstance(geo, dict) and geo.get("type") in ("Polygon", "MultiPolygon", "Feature")):
        raise api_error(400, "invalid_boundary", "boundary_geojson must be a GeoJSON Polygon, MultiPolygon or Feature")
    for key, allowed, code in (
        ("crop_id", CROP_IDS, "invalid_crop"),
        ("crop_stage_id", CROP_STAGE_IDS, "invalid_crop_stage"),
        ("season_id", SEASON_IDS, "invalid_season"),
        ("irrigation_type_id", IRRIGATION_TYPE_IDS, "invalid_irrigation_type"),
    ):
        if merged.get(key) is not None and merged[key] not in allowed:
            raise api_error(400, code, f"Unknown {key}; see /api/meta")


def _clean(sent: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in sent.items() if k in FARM_COLUMNS}
    for k in ("name", "village"):
        if isinstance(out.get(k), str):
            out[k] = out[k].strip() or None
    return out


async def _owned_farm(repo: Repository, farm_id: str, farmer: CurrentFarmer) -> dict[str, Any]:
    farm = await repo.get_farm(farm_id)
    if farm is None or str(farm["farmer_id"]) != farmer.farmer_id:
        raise not_found("Farm not found")
    return farm


@router.get("")
async def list_farms(
    farmer: CurrentFarmer = Depends(get_current_farmer),
    repo: Repository = Depends(get_repository),
) -> dict[str, Any]:
    return {"data": [farm_out(f) for f in await repo.list_farms(farmer.farmer_id)]}


@router.post("", status_code=201)
async def create_farm(
    body: FarmIn,
    farmer: CurrentFarmer = Depends(get_current_farmer),
    repo: Repository = Depends(get_repository),
) -> dict[str, Any]:
    fields = _clean(body.model_dump(exclude_unset=True))
    _validate(fields)
    if await repo.count_farms(farmer.farmer_id) >= MAX_FARMS:
        raise api_error(409, "farm_limit_reached", f"A farmer can register at most {MAX_FARMS} farms")
    farm = await repo.create_farm(farmer.farmer_id, fields)
    return farm_out(farm)


@router.put("/{farm_id}")
async def update_farm(
    farm_id: str,
    body: FarmIn,
    farmer: CurrentFarmer = Depends(get_current_farmer),
    repo: Repository = Depends(get_repository),
) -> dict[str, Any]:
    current = await _owned_farm(repo, farm_id, farmer)
    changes = _clean(body.model_dump(exclude_unset=True))
    merged = {k: current.get(k) for k in FARM_COLUMNS} | changes
    _validate(merged)
    farm = await repo.update_farm(farm_id, changes)
    if farm is None:
        raise not_found("Farm not found")
    return farm_out(farm)


@router.delete("/{farm_id}", status_code=204)
async def delete_farm(
    farm_id: str,
    farmer: CurrentFarmer = Depends(get_current_farmer),
    repo: Repository = Depends(get_repository),
) -> Response:
    await _owned_farm(repo, farm_id, farmer)
    await repo.delete_farm(farm_id)
    return Response(status_code=204)
