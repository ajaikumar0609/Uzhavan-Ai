"""Diary persistence (API contract §8). Postgres table diary_entries (migration 008)."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import date
from typing import Any, Optional, Protocol

from backend.shared.db import get_pool

logger = logging.getLogger("uzhavan.diary")

USER_KINDS = ("note", "observation", "expense", "income")
AUTO_KINDS = ("question", "scan")
ALL_KINDS = USER_KINDS + AUTO_KINDS
MAX_TEXT = 1000


class DiaryStore(Protocol):
    async def add(self, farmer_id: str, kind: str, text: str, *, farm_id: Optional[str] = None,
                  amount_inr: Optional[float] = None, entry_date: Optional[date] = None,
                  ref: Optional[dict[str, Any]] = None) -> dict[str, Any]: ...
    async def list(self, farmer_id: str, limit: int) -> list[dict[str, Any]]: ...


def _uuid(v: Optional[str]):
    if v is None:
        return None
    try:
        return uuid.UUID(str(v))
    except (ValueError, TypeError):
        return None


_COLS = "entry_id, farmer_id, farm_id, kind, text, amount_inr, entry_date, ref, created_at"


def _row(r) -> dict[str, Any]:
    d = dict(r)
    for k in ("entry_id", "farmer_id", "farm_id"):
        if d.get(k) is not None:
            d[k] = str(d[k])
    if isinstance(d.get("ref"), str):
        d["ref"] = json.loads(d["ref"])
    if d.get("amount_inr") is not None:
        d["amount_inr"] = float(d["amount_inr"])
    return d


class PostgresDiaryStore:
    def __init__(self, pool) -> None:
        self._pool = pool

    async def add(self, farmer_id, kind, text, *, farm_id=None, amount_inr=None, entry_date=None, ref=None):
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""INSERT INTO diary_entries (farmer_id, farm_id, kind, text, amount_inr, entry_date, ref)
                    VALUES ($1, $2, $3, $4, $5, COALESCE($6, (NOW() AT TIME ZONE 'Asia/Kolkata')::date), $7::jsonb)
                    RETURNING {_COLS}""",
                _uuid(farmer_id), _uuid(farm_id), kind, text[:MAX_TEXT], amount_inr, entry_date,
                json.dumps(ref) if ref is not None else None,
            )
        return _row(row)

    async def list(self, farmer_id, limit):
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"SELECT {_COLS} FROM diary_entries WHERE farmer_id = $1 "
                "ORDER BY entry_date DESC, created_at DESC LIMIT $2",
                _uuid(farmer_id), limit,
            )
        return [_row(r) for r in rows]


async def get_diary_store() -> DiaryStore:
    return PostgresDiaryStore(await get_pool())


def get_diary_store_factory():
    """Returns the factory without opening a pool (used by routes that log only sometimes)."""
    return get_diary_store


async def auto_log(store_factory, farmer_id: str, kind: str, text: str, *,
                   farm_id: Optional[str] = None, ref: Optional[dict[str, Any]] = None) -> None:
    """Best-effort auto-log (question / scan). Never raises: logging must not break the request."""
    if kind not in AUTO_KINDS or not farmer_id or farmer_id == "anonymous":
        return
    try:
        store = await store_factory()
        await store.add(farmer_id, kind, text, farm_id=farm_id, ref=ref)
    except Exception as exc:  # noqa: BLE001
        logger.warning("diary auto-log (%s) failed: %s", kind, type(exc).__name__)
