"""Government schemes (FP-012, API contract §6). Source text only; missing fields stay null."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from backend.auth.deps import CurrentFarmer, get_current_farmer, get_repository
from backend.auth.repository import Repository
from backend.knowledge.scheme.eligibility import contexts, evaluate
from backend.knowledge.scheme.store import SchemeStore, get_scheme_store
from backend.meta.catalog import CROP_IDS
from backend.shared.api_errors import api_error, not_found
from backend.shared.envelope import envelope, iso_date, note

router = APIRouter(prefix="/api/schemes", tags=["Schemes"])

SOURCE = "Official scheme portals (TNAGRISNET, AED TN, Govt. of India scheme sites), catalogued 2026-09-24"


def _bi(en: Optional[str], ta: Optional[str]) -> Optional[dict[str, Optional[str]]]:
    return None if en is None and ta is None else {"en": en, "ta": ta}


def summary(s: dict[str, Any]) -> dict[str, Any]:
    return {"scheme_id": s["scheme_id"], "name": {"en": s["name"], "ta": s.get("tamil_name")},
            "authority": s.get("authority"), "level": s.get("level"), "active": s.get("active"),
            "crops": s.get("crops"), "official_url": s.get("official_url")}


def detail(s: dict[str, Any]) -> dict[str, Any]:
    return summary(s) | {
        "state": s.get("state"),
        "crop_applicability": s.get("crop_applicability"),
        "description": _bi(s.get("description"), s.get("description_ta")),
        "eligibility_text": _bi(s.get("eligibility"), s.get("eligibility_ta")),
        "benefits": _bi(s.get("benefit"), None),
        "application_method": _bi(s.get("application_method"), None),
        "required_documents": _bi(s.get("documents_required"), s.get("required_documents_ta")),
        "components": s.get("components"),
        "source_documents": s.get("source_documents"),
        "source_go_file": s.get("source_go_file"),
        "date_checked": iso_date(s.get("date_checked")),
        "last_updated_on_source": s.get("last_updated_on_source"),
    }


@router.get("")
async def list_schemes(
    q: Optional[str] = Query(default=None, max_length=100),
    level: Optional[str] = None,
    crop_id: Optional[str] = None,
    active: Optional[bool] = None,
    store: SchemeStore = Depends(get_scheme_store),
) -> dict[str, Any]:
    if level is not None and level not in ("central", "state"):
        raise api_error(400, "invalid_level", "level must be central or state")
    if crop_id is not None and crop_id not in CROP_IDS:
        raise api_error(400, "invalid_crop", "Unknown crop_id; see /api/meta/crops")
    rows = await store.list(q.strip() if q else None, level, crop_id, active)
    notes = [note("Scheme details are copied from official sources; check the official site before applying.")]
    if crop_id:
        notes.append(note("The crop filter only matches schemes whose source names the crop explicitly."))
    return envelope([summary(s) for s in rows], source=SOURCE, source_url=None, kind="reference", notes=notes)


@router.get("/{scheme_id}")
async def get_scheme(scheme_id: str, store: SchemeStore = Depends(get_scheme_store)) -> dict[str, Any]:
    s = await store.get(scheme_id)
    if s is None:
        raise not_found("Scheme not found")
    return envelope(detail(s), source=SOURCE, source_url=s.get("official_url"), kind="reference",
                    observed_at=None, notes=[note(f"Checked against the source on {iso_date(s.get('date_checked'))}.")])


@router.get("/{scheme_id}/eligibility")
async def eligibility(
    scheme_id: str,
    farm_id: Optional[str] = None,
    farmer: CurrentFarmer = Depends(get_current_farmer),
    store: SchemeStore = Depends(get_scheme_store),
    repo: Repository = Depends(get_repository),
) -> dict[str, Any]:
    s = await store.get(scheme_id)
    if s is None:
        raise not_found("Scheme not found")
    profile = await repo.get_farmer(farmer.farmer_id)
    farms = await repo.list_farms(farmer.farmer_id)
    if farm_id is not None:
        farms = [f for f in farms if str(f["farm_id"]) == farm_id]
        if not farms:
            raise not_found("Farm not found")
    result = evaluate(s, contexts(profile, farms))
    return envelope(result, source="UZHAVAN eligibility rules (eligibility_rules.yaml) on official criteria",
                    source_url=result["criteria_source_url"], kind="reference")
