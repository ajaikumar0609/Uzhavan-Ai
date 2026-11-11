"""Read-only queries over `mandi_prices` / `data_sources` (FP-011)."""
from __future__ import annotations

from datetime import date
from typing import Any, Optional, Protocol

from backend.shared.db import get_pool

SOURCE_NAME = "AGMARKNET TN mandi prices (tn_mandi_prices.parquet)"


class MarketStore(Protocol):
    async def commodities(self) -> list[str]: ...
    async def markets(self, district_id: Optional[str]) -> list[dict[str, Any]]: ...
    async def latest(self, commodity: Optional[str], district_id: Optional[str], market: Optional[str],
                     limit: int) -> list[dict[str, Any]]: ...
    async def trend(self, commodity: str, market: str, since: date, variety: Optional[str]) -> list[dict[str, Any]]: ...
    async def snapshot(self) -> Optional[dict[str, Any]]: ...


def _f(v):
    return None if v is None else float(v)


class PostgresMarketStore:
    def __init__(self, pool) -> None:
        self._pool = pool

    async def commodities(self):
        async with self._pool.acquire() as c:
            return [r["commodity"] for r in await c.fetch(
                "SELECT DISTINCT commodity FROM mandi_prices ORDER BY commodity")]

    async def markets(self, district_id):
        q = "SELECT DISTINCT market, district_id, market_type FROM mandi_prices"
        args: list[Any] = []
        if district_id:
            q += " WHERE district_id = $1"
            args.append(district_id)
        async with self._pool.acquire() as c:
            return [dict(r) for r in await c.fetch(q + " ORDER BY market", *args)]

    async def latest(self, commodity, district_id, market, limit):
        conds, args = [], []
        for col, val in (("commodity", commodity), ("district_id", district_id), ("market", market)):
            if val:
                args.append(val)
                conds.append(f"{col} = ${len(args)}")
        where = ("WHERE " + " AND ".join(conds)) if conds else ""
        args.append(limit)
        q = f"""SELECT * FROM (
                  SELECT DISTINCT ON (commodity, market, variety)
                         commodity, variety, market, district_id, modal_price_inr, min_price_inr, max_price_inr,
                         arrivals_tonnes, price_unit, price_date
                  FROM mandi_prices {where}
                  ORDER BY commodity, market, variety, price_date DESC) t
                ORDER BY price_date DESC, market, variety LIMIT ${len(args)}"""
        async with self._pool.acquire() as c:
            rows = await c.fetch(q, *args)
        return [{**dict(r), "modal_price_inr": _f(r["modal_price_inr"]), "min_price_inr": _f(r["min_price_inr"]),
                 "max_price_inr": _f(r["max_price_inr"]), "arrivals_tonnes": _f(r["arrivals_tonnes"])} for r in rows]

    async def trend(self, commodity, market, since, variety):
        q = ("SELECT price_date, variety, modal_price_inr FROM mandi_prices "
             "WHERE commodity = $1 AND market = $2 AND price_date >= $3")
        args: list[Any] = [commodity, market, since]
        if variety:
            q += " AND variety = $4"
            args.append(variety)
        async with self._pool.acquire() as c:
            rows = await c.fetch(q + " ORDER BY price_date, variety", *args)
        return [{"price_date": r["price_date"], "variety": r["variety"], "modal_price_inr": _f(r["modal_price_inr"])}
                for r in rows]

    async def snapshot(self):
        async with self._pool.acquire() as c:
            r = await c.fetchrow("SELECT snapshot_date, row_count, loaded_at, url FROM data_sources WHERE name = $1",
                                 SOURCE_NAME)
        return dict(r) if r else None


async def get_market_store() -> MarketStore:
    return PostgresMarketStore(await get_pool())
