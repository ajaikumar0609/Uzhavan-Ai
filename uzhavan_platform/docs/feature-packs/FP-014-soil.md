# FP-014: Soil (district reference, SoilGrids estimate with caveats, farmer soil tests)

**Status:** `COMPLETE` (backend, 2026-09-25). Evidence: `tests/api/test_soil.py` (13 tests incl. the real project files and a Postgres round-trip); live curl `/api/soil?district_id=thanjavur`.
**Sprint:** Sprint-006 · **Milestone:** M-06 · **Owner:** Backend Sub-Agent · **Depends on:** FP-008, FP-009
**Contract:** §0, §7

## 1. Overview
`backend/knowledge/soil/service.py` reads the project's processed soil outputs (read-only, `uzhavan_data/04_soil/processed/`). Farmers can store their own lab results in `soil_tests`.

## 2. Business Goal
Farmers see what is known about their district's soils, clearly separated from their own measured results, and are nudged towards a real soil test.

## 3. User Story
As a farmer in Thanjavur, I see my zone's major soil types, how district SHC samples are rated, a clearly caveated model estimate, and the soil card results I entered.

## 4. Acceptance Criteria
- [x] `regional` ← `tn_mannvalam_district_major_soil_types.csv` (37 districts; Chennai has no row data → null). Tamil names are paired only when the source's English and Tamil lists have equal length; otherwise `ta:null`. `kind:"reference"`.
- [x] `nutrient_status` ← `tn_shc_district_nutrient_status_long.csv` (37 districts; Chennai absent → null). Record choice: the most recent cycle with ≥100 N samples; within it, the record (scheme) with the most samples. `low/medium/high_pct` only for Low/Medium/High categories; Deficient/Sufficient, Acidic/Neutral/Alkaline and Saline/NonSaline are returned in `categories` (never relabelled). `kind:"reference"`.
- [x] `estimated` ← `tn_district_soil_summary.csv` (38/38): 0–30 cm weighted means for pH, SOC, clay, sand, silt, CEC, BDOD and N, with `units`. `kind:"estimated"`. `caveats` say it's a "modelled estimate; may differ strongly from field measurements; use a soil test" and repeat the audit finding that SoilGrids SOC and texture look implausible for TN; low-coverage districts (Chennai) get an extra caveat.
- [x] `measured` = the farm's soil tests only (needs `farm_id` + token).
- [x] `POST /api/soil/tests` 🔒 → 201 SoilTest (`kind:"measured"`, `source:"farmer-entered lab result"`); range-validated (pH 0–14, EC 0–20 dS/m, OC 0–10 %, N 0–2000, P 0–500, K 0–3000 kg/ha, S/Zn/Fe/Cu/Mn/B 0–1000 ppm; sample_date 1990..today; at least one value); own farms only (404). `GET /api/soil/tests?farm_id=` 🔒.

## 5. UI Design
Flutter shows the four sections with their kind badges; estimates are always shown with their caveats.

## 6. API Contract
As in §7. Additions: `regional.zone`, `nutrient_status.scheme|updated_at|categories|notes`, `estimated.units|qc_flag`, section `source_url`s, and `meta.location.district_id`.

## 7. Database Changes
`007_soil_tests.sql` (`soil_tests`, FKs to farmers/farms ON DELETE CASCADE, range CHECKs mirroring the API). Idempotent; applied twice. Backup: `backups/uzhavan_dev_before_007_20260925_234302.sql`.

## 8. AI Changes
None.

## 9. Agent Responsibilities
Backend: the API. Data: refresh the processed CSVs. Flutter: the soil screen and soil card entry form.

## 10. Testing
A fixture CSV dir (pairing rules, SHC record selection, no relabelling, caveats, low-coverage); the real files (38/37/37 coverage); endpoints (district, farm, 401/404, 7 validation cases); a Postgres round-trip including a CHECK violation.

## 11. Security
Soil tests are scoped to the token farmer's farms. The reference data is public.

## 12. Performance
CSVs are parsed once per process (`lru_cache`), about 6k rows.

## 13. Documentation
This FP and the service docstring. The data dir can be overridden with the `UZHAVAN_DATA_DIR` setting.

## 14. Demo Checklist
- [x] `curl /api/soil?district_id=thanjavur` → regional, nutrient_status, estimated, measured []

## 15. Release Notes
> **FP-014: Soil.** See your district's major soil types, how Soil Health Card samples in your district are rated, and a modelled estimate that's clearly marked as such. Save your own soil test results. A real soil test is always the recommended source.

**Deviations:** SHC shares are district-wide, and the latest qualifying record can be a scheme-specific survey (e.g. Thanjavur 2026-27 "NMEO Oilseed", 230 samples); the `scheme` field says which. Farm lat/lon is not used for SoilGrids (only district summaries were processed).
