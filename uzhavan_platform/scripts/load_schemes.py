#!/usr/bin/env python
"""Load the scheme catalogue into Postgres `government_schemes` (FP-012, contract §6).

- Reads uzhavan_data/09_government_schemes/processed/schemes.jsonl (read-only, 136 records).
- Fields are copied as-is; a missing value stays NULL. Tamil fields are kept where present.
- `crops`: meta crop ids that are EXPLICITLY named in the source `crop_applicability` text;
  NULL when the source gives no crop applicability or names none of our crops.
- `active`: source_active_flag yes → true, no → false, absent → NULL.
- Idempotent: upsert on scheme_key; rows whose scheme_key is no longer in the file are deleted;
  all inside one transaction. The load is recorded in data_sources.

Usage: .venv/bin/python scripts/load_schemes.py [--file PATH] [--dsn DSN]
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FILE = ROOT.parent / "uzhavan_data" / "09_government_schemes" / "processed" / "schemes.jsonl"
SOURCE_NAME = "Government schemes catalogue (schemes.jsonl)"

# Explicit crop words in `crop_applicability` → meta crop id. Whole-word, case-insensitive.
CROP_WORDS = {
    r"paddy": "paddy", r"rice": "paddy", r"cotton": "cotton", r"sugarcane": "sugarcane",
    r"maize": "maize", r"coconut": "coconut", r"vegetables?": "vegetables", r"banana": "banana",
    r"groundnut": "groundnut", r"turmeric": "turmeric", r"chill?i(es)?": "chilli",
    r"black ?gram": "black_gram", r"green ?gram": "green_gram",
}

COLUMNS = ("scheme_key", "name", "tamil_name", "authority", "level", "state", "active", "crops",
           "crop_applicability", "description", "description_ta", "eligibility", "eligibility_ta", "benefit",
           "application_method", "documents_required", "required_documents_ta", "official_url",
           "source_documents", "date_checked", "last_updated_on_source", "source_catalogue",
           "source_go_file", "components", "source")


def crops_from_text(text: str | None) -> list[str] | None:
    if not text:
        return None
    found = []
    for pat, cid in CROP_WORDS.items():
        if re.search(rf"\b{pat}\b", text, re.IGNORECASE) and cid not in found:
            found.append(cid)
    return found or None


def _active(flag):
    return {"yes": True, "no": False}.get((flag or "").strip().lower())


def to_row(r: dict) -> tuple:
    return (
        r["scheme_id"], r["scheme_name"], r.get("scheme_name_ta"), r.get("authority"), r.get("level"),
        r.get("state"), _active(r.get("source_active_flag")), crops_from_text(r.get("crop_applicability")),
        r.get("crop_applicability"), r.get("description"), r.get("description_ta"), r.get("eligibility"),
        r.get("eligibility_ta"), r.get("benefits"), r.get("application_method"), r.get("required_documents"),
        r.get("required_documents_ta"), r.get("official_url"),
        json.dumps(r.get("source_documents")) if r.get("source_documents") is not None else None,
        date.fromisoformat(r["date_checked"]) if r.get("date_checked") else None,
        r.get("last_updated_on_source"), r.get("source_catalogue"), r.get("source_go_file"),
        json.dumps(r.get("components"), ensure_ascii=False) if r.get("components") is not None else None,
        "schemes.jsonl",
    )


def read_rows(path: Path) -> list[tuple]:
    rows = [to_row(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    keys = [r[0] for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate scheme_id in source")
    return rows


async def load(dsn: str, path: Path) -> dict:
    import asyncpg

    rows = read_rows(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    cols = ", ".join(COLUMNS)
    ph = ", ".join(f"${i + 1}" + ("::jsonb" if c in ("source_documents", "components") else "")
                   for i, c in enumerate(COLUMNS))
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in COLUMNS if c != "scheme_key")
    conn = await asyncpg.connect(dsn)
    try:
        async with conn.transaction():
            await conn.executemany(
                f"INSERT INTO government_schemes ({cols}) VALUES ({ph}) "
                f"ON CONFLICT (scheme_key) DO UPDATE SET {updates}, updated_at = NOW()", rows)
            await conn.execute("DELETE FROM government_schemes WHERE scheme_key IS NOT NULL "
                               "AND NOT (scheme_key = ANY($1::text[]))", [r[0] for r in rows])
            n = await conn.fetchval("SELECT COUNT(*) FROM government_schemes WHERE scheme_key IS NOT NULL")
            await conn.execute(
                """INSERT INTO data_sources (name, url, type, snapshot_date, row_count, file_path, file_sha256,
                                             loaded_at, notes)
                   VALUES ($1, NULL, 'Dataset', $2, $3, $4, $5, NOW(), 'loaded by scripts/load_schemes.py')
                   ON CONFLICT (name) DO UPDATE SET snapshot_date = EXCLUDED.snapshot_date,
                       row_count = EXCLUDED.row_count, file_path = EXCLUDED.file_path,
                       file_sha256 = EXCLUDED.file_sha256, loaded_at = EXCLUDED.loaded_at""",
                SOURCE_NAME, max((r[19] for r in rows if r[19]), default=None), n, str(path), digest,
            )
    finally:
        await conn.close()
    return {"file_records": len(rows), "loaded": n, "sha256": digest}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", type=Path, default=DEFAULT_FILE)
    ap.add_argument("--dsn", default=os.environ.get("DATABASE_URL", "postgresql://127.0.0.1:5432/uzhavan_dev"))
    a = ap.parse_args()
    print(asyncio.run(load(a.dsn, a.file)))


if __name__ == "__main__":
    main()
