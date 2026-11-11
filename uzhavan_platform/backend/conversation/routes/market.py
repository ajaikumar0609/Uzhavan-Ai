"""Market prices (FP-011, API contract §5). AGMARKNET snapshot in Postgres; no advice, no forecast."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from backend.knowledge.market.catalog import PRICE_UNIT, commodity as commodity_info
from backend.knowledge.market.store import MarketStore, get_market_store
from backend.meta.catalog import get_district
from backend.shared.api_errors import api_error, service_unavailable
from backend.shared.envelope import envelope, iso_date, note

router = APIRouter(prefix="/api/market", tags=["Market"])

SOURCE = "AGMARKNET (Directorate of Marketing & Inspection), TN snapshot"
SOURCE_URL = "https://agmarknet.gov.in"
STALE_DAYS = 7
NOTE_NO_ADVICE = note("Prices are past observations. UZHAVAN gives no price forecast or selling advice.")


async def _snapshot_notes(store: MarketStore) -> list[dict]:
    snap = await store.snapshot()
    if not snap:
        raise service_unavailable("Market data not loaded")
    return [note(f"Snapshot of AGMARKNET data up to {iso_date(snap['snapshot_date'])}; not live."), NOTE_NO_ADVICE]


def _check_district(district_id: Optional[str]) -> None:
    if district_id and get_district(district_id) is None:
        raise api_error(400, "invalid_district", "Unknown district_id; see /api/meta/districts")


@router.get("/commodities")
async def commodities(store: MarketStore = Depends(get_market_store)) -> dict[str, Any]:
    notes = await _snapshot_notes(store)
    return envelope([commodity_info(c) for c in await store.commodities()],
                    source=SOURCE, source_url=SOURCE_URL, kind="reference", notes=notes)


@router.get("/markets")
async def markets(district_id: Optional[str] = None, store: MarketStore = Depends(get_market_store)) -> dict[str, Any]:
    _check_district(district_id)
    notes = await _snapshot_notes(store)
    return envelope(await store.markets(district_id), source=SOURCE, source_url=SOURCE_URL,
                    kind="reference", notes=notes)


@router.get("/latest")
async def latest(
    commodity: Optional[str] = None,
    district_id: Optional[str] = None,
    market: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    store: MarketStore = Depends(get_market_store),
) -> dict[str, Any]:
    _check_district(district_id)
    notes = await _snapshot_notes(store)
    today = datetime.now(timezone.utc).date()
    rows = await store.latest(commodity, district_id, market, limit)
    data = []
    for r in rows:
        observed: date = r["price_date"]
        data.append({
            "commodity": r["commodity"],
            "commodity_name": commodity_info(r["commodity"])["name"],
            "variety": r["variety"],
            "market": r["market"],
            "district_id": r["district_id"],
            "modal_price": r["modal_price_inr"],
            "min_price": r["min_price_inr"],
            "max_price": r["max_price_inr"],
            "unit": r.get("price_unit") or PRICE_UNIT,
            "arrivals_tonnes": r["arrivals_tonnes"],
            "observed_on": iso_date(observed),
            "stale": (today - observed).days > STALE_DAYS,
        })
    if any(d["commodity"] == "coconut" for d in data):
        notes.append(note("Coconut price unit unverified (per quintal vs per 1000 nuts)."))
    newest = max((d["observed_on"] for d in data), default=None)
    return envelope(data, source=SOURCE, source_url=SOURCE_URL, kind="latest_observed",
                    observed_at=newest, notes=notes)


@router.get("/trend")
async def trend(
    commodity: str,
    market: str,
    days: int = Query(default=90, ge=1, le=730),
    variety: Optional[str] = None,
    store: MarketStore = Depends(get_market_store),
) -> dict[str, Any]:
    notes = await _snapshot_notes(store)
    since = datetime.now(timezone.utc).date() - timedelta(days=days)
    rows = await store.trend(commodity, market, since, variety)
    points = [{"date": iso_date(r["price_date"]), "modal_price": r["modal_price_inr"], "variety": r["variety"]}
              for r in rows]
    if len({p["variety"] for p in points}) > 1:
        notes.append(note("Several varieties are reported for this market; points are per variety, not averaged."))
    return envelope({"commodity": commodity, "market": market, "unit": PRICE_UNIT, "days": days, "points": points},
                    source=SOURCE, source_url=SOURCE_URL, kind="historical",
                    observed_at=points[-1]["date"] if points else None, notes=notes)
