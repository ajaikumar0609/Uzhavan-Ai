"""Read-only queries over `government_schemes` (FP-012; migration 006, loader scripts/load_schemes.py)."""
from __future__ import annotations

import json
from typing import Any, Optional, Protocol

from backend.shared.db import get_pool

_COLS = """scheme_key, name, tamil_name, authority, level, state, active, crops, crop_applicability,
           description, description_ta, eligibility, eligibility_ta, benefit, application_method,
           documents_required, required_documents_ta, official_url, source_documents, date_checked,
           last_updated_on_source, source_catalogue, source_go_file, components"""


class SchemeStore(Protocol):
    async def list(self, q: Optional[str], level: Optional[str], crop_id: Optional[str],
                   active: Optional[bool]) -> list[dict[str, Any]]: ...
    async def get(self, scheme_id: str) -> Optional[dict[str, Any]]: ...


def _row(r) -> dict[str, Any]:
    d = dict(r)
    d["scheme_id"] = d.pop("scheme_key")
    for k in ("source_documents", "components"):
        if isinstance(d.get(k), str):
            d[k] = json.loads(d[k])
    if d.get("crops") is not None:
        d["crops"] = list(d["crops"])
    return d


class PostgresSchemeStore:
    def __init__(self, pool) -> None:
        self._pool = pool

    async def list(self, q, level, crop_id, active):
        conds, args = ["scheme_key IS NOT NULL"], []
        if q:
            args.append(f"%{q}%")
            n = len(args)
            conds.append(f"(name ILIKE ${n} OR tamil_name ILIKE ${n} OR description ILIKE ${n} "
                         f"OR authority ILIKE ${n})")
        if level:
            args.append(level)
            conds.append(f"level = ${len(args)}")
        if crop_id:
            args.append(crop_id)
            conds.append(f"${len(args)} = ANY(crops)")
        if active is not None:
            args.append(active)
            conds.append(f"active IS NOT DISTINCT FROM ${len(args)}")
        async with self._pool.acquire() as c:
            rows = await c.fetch(f"SELECT {_COLS} FROM government_schemes WHERE {' AND '.join(conds)} "
                                 "ORDER BY level, name", *args)
        return [_row(r) for r in rows]

    async def get(self, scheme_id):
        async with self._pool.acquire() as c:
            r = await c.fetchrow(f"SELECT {_COLS} FROM government_schemes WHERE scheme_key = $1", scheme_id)
        return _row(r) if r else None


async def get_scheme_store() -> SchemeStore:
    return PostgresSchemeStore(await get_pool())
