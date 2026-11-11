"""Farmer-entered soil test results (table soil_tests, migration 007). kind = measured."""
from __future__ import annotations

import uuid
from typing import Any, Optional, Protocol

from backend.shared.db import get_pool

VALUE_FIELDS = ("ph", "ec_ds_m", "oc_pct", "n_kg_ha", "p_kg_ha", "k_kg_ha", "s_ppm",
                "zn_ppm", "fe_ppm", "cu_ppm", "mn_ppm", "b_ppm")
# Plausibility limits, mirrored by CHECK constraints in 007_soil_tests.sql.
RANGES: dict[str, tuple[float, float]] = {
    "ph": (0, 14), "ec_ds_m": (0, 20), "oc_pct": (0, 10), "n_kg_ha": (0, 2000), "p_kg_ha": (0, 500),
    "k_kg_ha": (0, 3000), "s_ppm": (0, 1000), "zn_ppm": (0, 1000), "fe_ppm": (0, 1000),
    "cu_ppm": (0, 1000), "mn_ppm": (0, 1000), "b_ppm": (0, 1000),
}
_COLS = "test_id, farmer_id, farm_id, sample_date, lab_name, " + ", ".join(VALUE_FIELDS) + ", created_at"


class SoilTestStore(Protocol):
    async def add(self, farmer_id: str, farm_id: str, fields: dict[str, Any]) -> dict[str, Any]: ...
    async def list_for_farm(self, farm_id: str) -> list[dict[str, Any]]: ...


def _row(r) -> dict[str, Any]:
    d = dict(r)
    for k in ("test_id", "farmer_id", "farm_id"):
        d[k] = str(d[k])
    for k in VALUE_FIELDS:
        if d.get(k) is not None:
            d[k] = float(d[k])
    return d


class PostgresSoilTestStore:
    def __init__(self, pool) -> None:
        self._pool = pool

    async def add(self, farmer_id, farm_id, fields):
        cols = ["sample_date", "lab_name", *VALUE_FIELDS]
        ph = ", ".join(f"${i + 3}" for i in range(len(cols)))
        async with self._pool.acquire() as c:
            r = await c.fetchrow(
                f"INSERT INTO soil_tests (farmer_id, farm_id, {', '.join(cols)}) VALUES ($1, $2, {ph}) RETURNING {_COLS}",
                uuid.UUID(farmer_id), uuid.UUID(farm_id), *[fields.get(k) for k in cols])
        return _row(r)

    async def list_for_farm(self, farm_id):
        async with self._pool.acquire() as c:
            rows = await c.fetch(f"SELECT {_COLS} FROM soil_tests WHERE farm_id = $1 "
                                 "ORDER BY sample_date DESC, created_at DESC", uuid.UUID(farm_id))
        return [_row(r) for r in rows]


async def get_soil_test_store() -> SoilTestStore:
    return PostgresSoilTestStore(await get_pool())


def get_soil_test_store_factory():
    return get_soil_test_store
