"""
MarketAgent (FP-015) — observed AGMARKNET prices only.

Uses the same FP-011 store and queries as /api/market/latest and /api/market/trend
(Postgres `mandi_prices`). It exposes ONLY observed prices with their market and
observed_on date. No forecast, no trend interpretation, no selling advice.
"""
from __future__ import annotations

import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Awaitable, Callable

from backend.knowledge.market.catalog import COMMODITY_INDEX, PRICE_UNIT
from backend.knowledge.market.store import MarketStore, get_market_store
from backend.meta.catalog import district_id_from_name, get_district
from backend.shared.agents.base import BaseDomainAgent
from backend.shared.models.citation import Citation
from backend.shared.models.context import ConversationContext
from backend.shared.models.tool import AgentManifest, ToolCapability, ToolResult

SOURCE = "AGMARKNET (Directorate of Marketing & Inspection), TN snapshot"
SOURCE_URL = "https://agmarknet.gov.in"
STALE_DAYS = 7
NO_ADVICE = "These are past recorded prices. UZHAVAN gives no price forecast or selling advice."


def _commodity_id(crop: str | None) -> str | None:
    if not crop:
        return None
    cid = crop.strip().lower().replace(" ", "_")
    return cid if cid in COMMODITY_INDEX else None


def _iso(d: Any) -> str | None:
    if d is None:
        return None
    return d.isoformat() if isinstance(d, (date, datetime)) else str(d)


def _price(v: Any) -> str:
    return "not available" if v is None else f"Rs {v:g}"


class MarketAgent(BaseDomainAgent):
    VERSION = "2.0"
    _CAPABILITIES = ["current_price", "trend"]

    def __init__(self, store_factory: Callable[[], Awaitable[MarketStore]] | None = None) -> None:
        self._store_factory = store_factory or get_market_store

    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_name="market",
            version=self.VERSION,
            description="Observed AGMARKNET mandi prices for Tamil Nadu (dated, no forecast or advice)",
            avg_latency_ms=300,
            typical_confidence=0.85,
            feature_flag="ENABLE_MARKET",
            dependencies=["postgresql"],
            capabilities=[
                ToolCapability(name="current_price", description="Latest observed modal price per market, with date", avg_latency_ms=300),
                ToolCapability(name="trend", description="Observed modal prices over the last 90 days at one market (no interpretation)", avg_latency_ms=300),
            ],
        )

    def can_handle(self, capability_name: str) -> bool:
        parts = capability_name.split(".", 1)
        return len(parts) == 2 and parts[0] == "market" and parts[1] in self._CAPABILITIES

    async def execute(self, capability_name: str, context: ConversationContext, params: dict[str, Any]) -> ToolResult:
        start_ns = time.monotonic_ns()
        _, method = capability_name.split(".", 1)
        crop = params.get("crop") or (context.farm.crop if context.farm else None)
        district = params.get("district") or (context.farm.district if context.farm else None) or context.farmer.district
        commodity = _commodity_id(crop)
        if method not in self._CAPABILITIES:
            return self._timed_result(capability_name, start_ns, False, error=f"Unknown method: {method}")
        if commodity is None:
            return self._timed_result(capability_name, start_ns, False,
                                      error=f"commodity unknown or not in the AGMARKNET snapshot: {crop!r}")
        try:
            store = await self._store_factory()
            snap = await store.snapshot()
            if not snap:
                return self._timed_result(capability_name, start_ns, False, error="Market data not loaded")
            if method == "current_price":
                return await self._current_price(start_ns, store, snap, commodity, district)
            return await self._trend(start_ns, store, snap, commodity, district)
        except Exception as exc:  # DB down etc. → honest failure, never a made-up price
            return self._timed_result(capability_name, start_ns, False, error=f"market data unavailable: {type(exc).__name__}")

    async def _latest_rows(self, store: MarketStore, commodity: str, district: str | None) -> tuple[list[dict], str | None, bool]:
        did = district_id_from_name(district) if district else None
        rows = await store.latest(commodity, did, None, 5) if did else []
        if rows:
            return rows, did, True
        return await store.latest(commodity, None, None, 5), did, False

    def _snapshot_fact(self, snap: dict) -> str:
        return f"Source: {SOURCE}; snapshot of data up to {_iso(snap.get('snapshot_date'))}; not live. {NO_ADVICE}"

    async def _current_price(self, start_ns: int, store: MarketStore, snap: dict, commodity: str, district: str | None) -> ToolResult:
        rows, did, in_district = await self._latest_rows(store, commodity, district)
        name = COMMODITY_INDEX[commodity]["name"]["en"]
        if not rows:
            return self._timed_result("market.current_price", start_ns, False, error=f"No observed {name} prices in the snapshot")
        today = datetime.now(timezone.utc).date()
        facts = [self._snapshot_fact(snap)]
        if did and not in_district:
            dname = (get_district(did) or {}).get("name", {}).get("en", district)
            facts.append(f"No {name} prices are recorded for {dname} district; the rows below are from other Tamil Nadu markets.")
        elif not did:
            facts.append("District not known; the rows below are the latest recorded Tamil Nadu markets.")
        prices, citations = [], []
        for r in rows:
            observed = r.get("price_date")
            stale = isinstance(observed, date) and (today - observed).days > STALE_DAYS
            unit = r.get("price_unit") or PRICE_UNIT
            line = (f"{name}{' (' + r['variety'] + ')' if r.get('variety') else ''} at {r['market']}: modal price "
                    f"{_price(r.get('modal_price_inr'))} per quintal (min {_price(r.get('min_price_inr'))}, "
                    f"max {_price(r.get('max_price_inr'))}), observed on {_iso(observed)}"
                    + (" — older than 7 days" if stale else "") + ".")
            facts.append(line)
            prices.append({"market": r["market"], "variety": r.get("variety"), "district_id": r.get("district_id"),
                           "modal_price": r.get("modal_price_inr"), "min_price": r.get("min_price_inr"),
                           "max_price": r.get("max_price_inr"), "unit": unit, "observed_on": _iso(observed), "stale": stale})
            citations.append(Citation(source="AGMARKNET", title=f"{name} — {r['market']} ({_iso(observed)})",
                                      excerpt=line, confidence=0.85, url=SOURCE_URL, category="market"))
        if commodity == "coconut":
            facts.append("Coconut price unit is unverified (per quintal vs per 1000 nuts).")
        data = {"commodity": commodity, "prices": prices, "facts": facts, "kind": "latest_observed"}
        return self._timed_result("market.current_price", start_ns, True, data=data, citations=citations, confidence=0.85)

    async def _trend(self, start_ns: int, store: MarketStore, snap: dict, commodity: str, district: str | None) -> ToolResult:
        rows, _, _ = await self._latest_rows(store, commodity, district)
        name = COMMODITY_INDEX[commodity]["name"]["en"]
        if not rows:
            return self._timed_result("market.trend", start_ns, False, error=f"No observed {name} prices in the snapshot")
        market = rows[0]["market"]
        last = rows[0].get("price_date")
        since = (last if isinstance(last, date) else datetime.now(timezone.utc).date()) - timedelta(days=90)
        points = [p for p in await store.trend(commodity, market, since, None) if p.get("modal_price_inr") is not None]
        if not points:
            return self._timed_result("market.trend", start_ns, False, error=f"No observed {name} price history at {market}")
        lo = min(points, key=lambda p: p["modal_price_inr"])
        hi = max(points, key=lambda p: p["modal_price_inr"])
        first, latest = points[0], points[-1]
        line = (f"Observed {name} modal prices at {market} from {_iso(first['price_date'])} to {_iso(latest['price_date'])} "
                f"({len(points)} records): first {_price(first['modal_price_inr'])}, latest {_price(latest['modal_price_inr'])}, "
                f"lowest {_price(lo['modal_price_inr'])} on {_iso(lo['price_date'])}, highest {_price(hi['modal_price_inr'])} "
                f"on {_iso(hi['price_date'])} per quintal.")
        data = {"commodity": commodity, "market": market, "points": [{"date": _iso(p["price_date"]), "modal_price": p["modal_price_inr"], "variety": p.get("variety")} for p in points],
                "facts": [line, NO_ADVICE], "kind": "historical"}
        citation = Citation(source="AGMARKNET", title=f"{name} price history — {market}", excerpt=line, confidence=0.85, url=SOURCE_URL, category="market")
        return self._timed_result("market.trend", start_ns, True, data=data, citations=[citation], confidence=0.85)

    async def health(self) -> bool:
        try:
            return bool(await (await self._store_factory()).snapshot())
        except Exception:
            return False
