# FP-011: Market prices (AGMARKNET snapshot)

**Status:** `COMPLETE` (backend, 2026-09-25). Evidence: the loader on uzhavan_dev loaded **1,068,236** rows (= QC-pass rows in the parquet, of 1,081,848), with the load recorded in `data_sources` (snapshot 2026-09-24, sha256 `254efd3f…`); `tests/api/test_market.py` (7 tests); live curl of latest/trend via the dev server.
**Sprint:** Sprint-006 · **Milestone:** M-06 · **Owner:** Backend Sub-Agent · **Depends on:** FP-007
**Contract:** §0, §5

## 1. Overview
The processed AGMARKNET TN snapshot (`uzhavan_data/08_market/processed/tn_mandi_prices.parquet`) is loaded into Postgres and served read-only.

## 2. Business Goal
Farmers see recent recorded mandi prices near them, clearly dated. There's no advice and no forecast (the M6 model is not trained).

## 3. User Story
As a farmer, I pick paddy and see the latest modal price at nearby markets and the 90-day trend, marked stale if old.

## 4. Acceptance Criteria
- [x] Migration 005 extends `mandi_prices` (`district_id`, `market_type`, `variety`, `commodity_source_name`, `price_unit`, `snapshot_date`, `source_file`) and adds indexes (commodity, market, price_date DESC), (commodity, price_date DESC), (district_id) and (market). `data_sources` gains `snapshot_date`, `row_count`, `file_path`, `file_sha256` and `loaded_at`, plus a unique name.
- [x] `scripts/load_mandi_prices.py`: QC-pass rows only; TRUNCATE + COPY in one transaction (idempotent, verified twice in the tests); district → meta id via `catalog.district_id_from_name` (all 36 source district spellings map; the 8,114 rows with no source district stay NULL); records the load in `data_sources`.
- [x] `GET /api/market/commodities`: 14 commodities; coconut `unit_note` = "unit unverified (per quintal vs per 1000 nuts)"; Tamil names are standard common words only.
- [x] `GET /api/market/markets?district_id=`, `GET /api/market/latest?commodity=&district_id=&market=&limit=20` (latest row per commodity × market × variety; `stale:true` when `observed_on` is more than 7 days before today (UTC); `meta.kind:"latest_observed"`; notes carry the snapshot date).
- [x] `GET /api/market/trend?commodity=&market=&days=90[&variety=]` → `points[{date, modal_price, variety}]`, `meta.kind:"historical"`. Varieties are not averaged.
- [x] No advice or forecast fields (asserted in the tests). 503 if the snapshot isn't loaded.

## 5. UI Design
Flutter shows the snapshot note, stale badges and the coconut unit note.

## 6. API Contract
As in §5. Additions: `stale` on every latest row (true/false); `variety` on trend points; the `market` value is the AGMARKNET market name including its type (e.g. "Thanjavur APMC"), because the same town can have an APMC and an Uzhavar Sandhai.

## 7. Database Changes
`005_market_mandi_prices.sql` (idempotent; applied twice). Backup: `backups/uzhavan_dev_before_005_20260925_234259.sql`.

## 8. AI Changes
None.

## 9. Agent Responsibilities
Backend: the loader and API. Data: refresh the parquet and re-run the loader. Flutter: the market screen.

## 10. Testing
`test_market.py`: endpoints on a fake store (shape, stale, coconut note, no-advice fields, validation, 503 when unloaded); the loader on a 3-row parquet in a throwaway schema (QC filter, district mapping, idempotency, sha256); the real `PostgresMarketStore` read-only.

## 11. Security
Read-only, parameterised SQL. No auth is needed (public prices).

## 12. Performance
The DISTINCT ON latest query takes about 0.2 s for paddy (117k rows) after ANALYZE; the load takes about 18 s.

## 13. Documentation
This FP; the loader docstring; CHANGELOG.

## 14. Demo Checklist
- [x] `curl /api/market/latest?commodity=paddy` · `curl /api/market/trend?commodity=paddy&market=…`

## 15. Release Notes
> **FP-011: Mandi prices.** Recorded AGMARKNET prices for 14 commodities across 431 Tamil Nadu markets, with the date of every price and a 90-day trend. Old prices are marked. There's no price prediction or selling advice.

**Deviations:** The market identifier is `market_raw` ("X APMC" / "X Uzhavar Sandhai") to keep the two market types distinct. Rice, copra and brinjal Tamil names (அரிசி, கொப்பரை, கத்தரிக்காய்) are standard words not present in the React data.
