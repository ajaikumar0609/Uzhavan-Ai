"""Farmer profile (FP-009, API contract §3) 🔒

GET /api/farmer/profile · PUT /api/farmer/profile (partial)
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.auth.deps import CurrentFarmer, get_current_farmer, get_repository
from backend.auth.repository import Repository
from backend.meta.catalog import get_district
from backend.shared.api_errors import api_error, not_found

router = APIRouter(prefix="/api/farmer", tags=["Farmer"])

_LEGACY_LANG = {"tamil": "ta", "english": "en"}


def normalize_language(value: Optional[str]) -> str:
    if not value:
        return "ta"
    v = value.strip().lower()
    return _LEGACY_LANG.get(v, v if v in ("ta", "en") else "ta")


def is_profile_complete(farmer: dict[str, Any]) -> bool:
    return bool(farmer.get("name")) and bool(farmer.get("district_id"))


def _iso(dt) -> Optional[str]:
    if dt is None:
        return None
    return dt.isoformat().replace("+00:00", "Z")


def profile_out(farmer: dict[str, Any]) -> dict[str, Any]:
    return {
        "farmer_id": str(farmer["farmer_id"]),
        "phone": farmer.get("phone"),
        "name": farmer.get("name"),
        "district_id": farmer.get("district_id"),
        "village": farmer.get("village"),
        "preferred_language": normalize_language(farmer.get("preferred_language")),
        "profile_complete": is_profile_complete(farmer),
        "created_at": _iso(farmer.get("created_at")),
        "updated_at": _iso(farmer.get("updated_at")),
    }


class ProfileIn(BaseModel):
    name: Optional[str] = None
    district_id: Optional[str] = None
    village: Optional[str] = None
    preferred_language: Optional[str] = None


@router.get("/profile")
async def get_profile(
    farmer: CurrentFarmer = Depends(get_current_farmer),
    repo: Repository = Depends(get_repository),
) -> dict[str, Any]:
    row = await repo.get_farmer(farmer.farmer_id)
    if row is None:
        raise not_found("Farmer not found")
    return {"data": profile_out(row)}


@router.put("/profile")
async def update_profile(
    body: ProfileIn,
    farmer: CurrentFarmer = Depends(get_current_farmer),
    repo: Repository = Depends(get_repository),
) -> dict[str, Any]:
    sent = body.model_dump(exclude_unset=True)
    fields: dict[str, Any] = {}

    if "name" in sent:
        name = (sent["name"] or "").strip()
        if not 2 <= len(name) <= 100:
            raise api_error(400, "invalid_name", "Name must be 2 to 100 characters")
        fields["name"] = name
    if "district_id" in sent:
        district = get_district(sent["district_id"] or "")
        if district is None:
            raise api_error(400, "invalid_district", "Unknown district_id; see /api/meta/districts")
        fields["district_id"] = district["id"]
        fields["_district_name"] = district["name"]["en"]
    if "village" in sent:
        village = (sent["village"] or "").strip()
        if len(village) > 100:
            raise api_error(400, "invalid_village", "Village must be at most 100 characters")
        fields["village"] = village or None
    if "preferred_language" in sent:
        if sent["preferred_language"] not in ("ta", "en"):
            raise api_error(400, "invalid_language", "preferred_language must be 'ta' or 'en'")
        fields["preferred_language"] = sent["preferred_language"]

    row = await repo.update_farmer(farmer.farmer_id, fields)
    if row is None:
        raise not_found("Farmer not found")
    return {"data": profile_out(row)}
