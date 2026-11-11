#!/usr/bin/env python
"""Load the AGMARKNET TN mandi snapshot into Postgres `mandi_prices` (FP-011, contract §5).

- Reads uzhavan_data/08_market/processed/tn_mandi_prices.parquet (read-only), QC-pass rows only.
- Idempotent: TRUNCATE + COPY inside ONE transaction (a failure leaves the old data intact).
- District names are mapped to meta district ids (backend.meta.catalog); unknown → NULL.
- Records the load in `data_sources` (name, snapshot date, row count, file sha256), upsert by name.

Usage:
  .venv/bin/python scripts/load_mandi_prices.py [--file PATH] [--dsn DSN] [--snapshot-date 2026-09-24]
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.meta.catalog import district_id_from_name  # noqa: E402

DEFAULT_FILE = ROOT.parent / "uzhavan_data" / "08_market" / "processed" / "tn_mandi_prices.parquet"
SOURCE_NAME = "AGMARKNET TN mandi prices (tn_mandi_prices.parquet)"
SOURCE_URL = "https://agmarknet.gov.in"
COLUMNS = ("commodity", "district", "district_id", "market", "market_type", "variety", "commodity_source_name",
           "price_date", "min_price_inr", "max_price_inr", "modal_price_inr", "arrivals_tonnes",
           "price_unit", "source", "snapshot_date", "source_file")
BATCH = 50_000


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _date(v) -> date:
    return v.date() if isinstance(v, datetime) else v


def read_records(path: Path, snapshot: date):
    """Yield (qc_total_rows, records) where records are tuples in COLUMNS order (QC-pass only)."""
    import pyarrow.parquet as pq

    table = pq.read_table(path)
    total = table.num_rows
    d = table.to_pydict()
    cache: dict[str, str | None] = {}
    records = []
    for i in range(total):
        if not d["qc_pass"][i]:
            continue
        dname = d["district"][i]
        if dname not in cache:
            cache[dname] = district_id_from_name(dname)
        records.append((
            d["commodity"][i], dname, cache[dname], d["market_raw"][i], d["market_type"][i],
            d["variety"][i], d["commodity_source_name"][i], _date(d["date"][i]),
            d["min_price"][i], d["max_price"][i], d["modal_price"][i], d["arrivals_tonnes"][i],
            d["price_unit"][i], "AGMARKNET", snapshot, d["source_file"][i],
        ))
    return total, records


async def load(dsn: str, path: Path, snapshot: date) -> dict:
    import asyncpg

    total, records = read_records(path, snapshot)
    digest = sha256_file(path)
    conn = await asyncpg.connect(dsn)
    try:
        async with conn.transaction():
            await conn.execute("TRUNCATE mandi_prices")
            for start in range(0, len(records), BATCH):
                await conn.copy_records_to_table("mandi_prices", records=records[start:start + BATCH],
                                                 columns=list(COLUMNS))
            n = await conn.fetchval("SELECT COUNT(*) FROM mandi_prices")
            await conn.execute(
                """INSERT INTO data_sources (name, url, type, snapshot_date, row_count, file_path, file_sha256,
                                             loaded_at, notes)
                   VALUES ($1, $2, 'Dataset', $3, $4, $5, $6, NOW(), $7)
                   ON CONFLICT (name) DO UPDATE SET url = EXCLUDED.url, snapshot_date = EXCLUDED.snapshot_date,
                       row_count = EXCLUDED.row_count, file_path = EXCLUDED.file_path,
                       file_sha256 = EXCLUDED.file_sha256, loaded_at = EXCLUDED.loaded_at, notes = EXCLUDED.notes""",
                SOURCE_NAME, SOURCE_URL, snapshot, n, str(path), digest,
                f"QC-pass rows only ({n} of {total}); loaded by scripts/load_mandi_prices.py",
            )
        await conn.execute("ANALYZE mandi_prices")
    finally:
        await conn.close()
    unmapped = sum(1 for r in records if r[2] is None)
    return {"file_rows": total, "qc_pass_rows": len(records), "loaded": n, "district_id_null": unmapped,
            "sha256": digest}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", type=Path, default=DEFAULT_FILE)
    ap.add_argument("--dsn", default=os.environ.get("DATABASE_URL", "postgresql://127.0.0.1:5432/uzhavan_dev"))
    ap.add_argument("--snapshot-date", type=date.fromisoformat, default=date(2026, 9, 24))
    a = ap.parse_args()
    print(asyncio.run(load(a.dsn, a.file, a.snapshot_date)))


if __name__ == "__main__":
    main()
