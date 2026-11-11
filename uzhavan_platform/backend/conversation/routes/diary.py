"""Diary (API contract §8) 🔒

GET /api/diary?limit=50 · POST /api/diary
`question` and `scan` entries are written automatically by /conversation and /api/disease/scan;
clients may only POST note | observation | expense | income.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.auth.deps import CurrentFarmer, get_current_farmer, get_repository
from backend.auth.repository import Repository
from backend.diary.store import MAX_TEXT, USER_KINDS, DiaryStore, get_diary_store
from backend.shared.api_errors import api_error, not_found
from backend.shared.envelope import iso_date, iso_utc

router = APIRouter(prefix="/api/diary", tags=["Diary"])

MAX_AMOUNT_INR = 100_000_000  # 10 crore; guards against typos, not a business rule
_IST = timezone(timedelta(hours=5, minutes=30))


class DiaryIn(BaseModel):
    farm_id: Optional[str] = None
    kind: str
    text: str
    amount_inr: Optional[float] = None
    entry_date: date


def entry_out(e: dict[str, Any]) -> dict[str, Any]:
    return {
        "entry_id": e["entry_id"],
        "farm_id": e.get("farm_id"),
        "kind": e["kind"],
        "text": e["text"],
        "amount_inr": e.get("amount_inr"),
        "entry_date": iso_date(e["entry_date"]),
        "created_at": iso_utc(e.get("created_at")),
        "ref": e.get("ref"),
    }


@router.get("")
async def list_diary(
    limit: int = Query(default=50, ge=1, le=200),
    farmer: CurrentFarmer = Depends(get_current_farmer),
    store: DiaryStore = Depends(get_diary_store),
) -> dict[str, Any]:
    return {"data": [entry_out(e) for e in await store.list(farmer.farmer_id, limit)]}


@router.post("", status_code=201)
async def add_diary(
    body: DiaryIn,
    farmer: CurrentFarmer = Depends(get_current_farmer),
    store: DiaryStore = Depends(get_diary_store),
    repo: Repository = Depends(get_repository),
) -> dict[str, Any]:
    if body.kind not in USER_KINDS:
        raise api_error(400, "invalid_kind", "kind must be one of note, observation, expense, income")
    text = body.text.strip()
    if not 1 <= len(text) <= MAX_TEXT:
        raise api_error(400, "invalid_text", f"text must be 1 to {MAX_TEXT} characters")
    if body.amount_inr is not None:
        if body.kind not in ("expense", "income"):
            raise api_error(400, "amount_not_allowed", "amount_inr is only for expense or income entries")
        if not 0 <= body.amount_inr <= MAX_AMOUNT_INR:
            raise api_error(400, "invalid_amount", "amount_inr must be between 0 and 100000000")
    today_ist = datetime.now(_IST).date()
    if body.entry_date > today_ist + timedelta(days=1) or body.entry_date.year < 2000:
        raise api_error(400, "invalid_entry_date", "entry_date must not be in the future")
    if body.farm_id is not None:
        farm = await repo.get_farm(body.farm_id)
        if farm is None or str(farm["farmer_id"]) != farmer.farmer_id:
            raise not_found("Farm not found")
    entry = await store.add(farmer.farmer_id, body.kind, text, farm_id=body.farm_id,
                            amount_inr=body.amount_inr, entry_date=body.entry_date)
    return {"data": entry_out(entry)}
