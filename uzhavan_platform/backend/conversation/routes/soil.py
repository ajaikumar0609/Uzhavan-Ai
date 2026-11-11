"""Soil (FP-014, API contract §7).

GET /api/soil?farm_id=|district_id=  → regional (reference) · nutrient_status (reference, SHC shares)
                                        · estimated (SoilGrids, with caveats) · measured (farmer's tests)
POST /api/soil/tests 🔒 · GET /api/soil/tests?farm_id= 🔒
Estimates are never labelled measured; measured = farmer-entered lab results only.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.auth.deps import (
    CurrentFarmer, get_current_farmer, get_optional_farmer, get_repository, get_repository_factory, settings_dep,
)
from backend.auth.repository import Repository
from backend.knowledge.soil.service import soil_reference
from backend.knowledge.soil.tests_store import (
    RANGES, VALUE_FIELDS, SoilTestStore, get_soil_test_store, get_soil_test_store_factory,
)
from backend.meta.catalog import get_district
from backend.shared.api_errors import api_error, not_found, unauthenticated
from backend.shared.envelope import envelope, iso_date, iso_utc, note
from backend.shared.settings import Settings

router = APIRouter(prefix="/api/soil", tags=["Soil"])
_IST = timezone(timedelta(hours=5, minutes=30))


class SoilTestIn(BaseModel):
    farm_id: str
    sample_date: date
    lab_name: Optional[str] = None
    ph: Optional[float] = None
    ec_ds_m: Optional[float] = None
    oc_pct: Optional[float] = None
    n_kg_ha: Optional[float] = None
    p_kg_ha: Optional[float] = None
    k_kg_ha: Optional[float] = None
    s_ppm: Optional[float] = None
    zn_ppm: Optional[float] = None
    fe_ppm: Optional[float] = None
    cu_ppm: Optional[float] = None
    mn_ppm: Optional[float] = None
    b_ppm: Optional[float] = None


def soil_test_out(t: dict[str, Any]) -> dict[str, Any]:
    return {"test_id": t["test_id"], "farm_id": t["farm_id"], "sample_date": iso_date(t["sample_date"]),
            "lab_name": t.get("lab_name"), **{k: t.get(k) for k in VALUE_FIELDS},
            "kind": "measured", "source": "farmer-entered lab result", "created_at": iso_utc(t.get("created_at"))}


def _data_dir(settings: Settings) -> str:
    return str(settings.data_dir / "04_soil" / "processed")


async def _owned_farm(repo: Repository, farm_id: str, farmer: CurrentFarmer) -> dict[str, Any]:
    farm = await repo.get_farm(farm_id)
    if farm is None or str(farm["farmer_id"]) != farmer.farmer_id:
        raise not_found("Farm not found")
    return farm


@router.get("")
async def soil(
    farm_id: Optional[str] = None,
    district_id: Optional[str] = None,
    farmer: Optional[CurrentFarmer] = Depends(get_optional_farmer),
    repo_factory=Depends(get_repository_factory),
    tests_factory=Depends(get_soil_test_store_factory),
    settings: Settings = Depends(settings_dep),
) -> dict[str, Any]:
    measured: list[dict[str, Any]] = []
    if farm_id:
        if farmer is None:
            raise unauthenticated("farm_id requires sign-in")
        farm = await _owned_farm(await repo_factory(), farm_id, farmer)
        district_id = farm.get("district_id")
        measured = [soil_test_out(t) for t in await (await tests_factory()).list_for_farm(farm_id)]
    if not district_id:
        raise api_error(400, "location_required", "Give farm_id or district_id")
    d = get_district(district_id)
    if d is None:
        raise api_error(400, "invalid_district", "Unknown district_id; see /api/meta/districts")
    ref = soil_reference(_data_dir(settings))
    data = {"regional": ref.regional(district_id), "nutrient_status": ref.nutrient_status(district_id),
            "estimated": ref.estimated(district_id), "measured": measured}
    notes = [note("regional, nutrient_status and estimated describe the whole district, not your field. "
                  "Only 'measured' holds your own soil test results."),
             note("Each section carries its own kind and source; a missing section is null.")]
    return envelope(data, source="Tamil Mannvalam; Soil Health Card dashboard; ISRIC SoilGrids 2.0; farmer soil tests",
                    source_url=None, kind="reference",
                    location={"name": d["name"]["en"], "lat": d["lat"], "lon": d["lon"], "district_id": district_id},
                    notes=notes)


def _validate(body: SoilTestIn) -> dict[str, Any]:
    today = datetime.now(_IST).date()
    if body.sample_date > today or body.sample_date.year < 1990:
        raise api_error(400, "invalid_sample_date", "sample_date must be a past date (1990 or later)")
    lab = body.lab_name.strip() if body.lab_name else None
    if lab is not None and len(lab) > 100:
        raise api_error(400, "invalid_lab_name", "lab_name must be at most 100 characters")
    values = {k: getattr(body, k) for k in VALUE_FIELDS}
    if all(v is None for v in values.values()):
        raise api_error(400, "no_values", "Enter at least one soil test value")
    for k, v in values.items():
        lo, hi = RANGES[k]
        if v is not None and not lo <= v <= hi:
            raise api_error(400, "value_out_of_range", f"{k} must be between {lo:g} and {hi:g}")
    return {"sample_date": body.sample_date, "lab_name": lab or None, **values}


@router.post("/tests", status_code=201)
async def add_test(
    body: SoilTestIn,
    farmer: CurrentFarmer = Depends(get_current_farmer),
    repo: Repository = Depends(get_repository),
    store: SoilTestStore = Depends(get_soil_test_store),
) -> dict[str, Any]:
    fields = _validate(body)
    await _owned_farm(repo, body.farm_id, farmer)
    return {"data": soil_test_out(await store.add(farmer.farmer_id, body.farm_id, fields))}


@router.get("/tests")
async def list_tests(
    farm_id: str = Query(...),
    farmer: CurrentFarmer = Depends(get_current_farmer),
    repo: Repository = Depends(get_repository),
    store: SoilTestStore = Depends(get_soil_test_store),
) -> dict[str, Any]:
    await _owned_farm(repo, farm_id, farmer)
    return {"data": [soil_test_out(t) for t in await store.list_for_farm(farm_id)]}
