# FP-009: Farmer profile, farms and reference meta

**Status:** `COMPLETE` (backend, 2026-09-25). Evidence: the live dev-server PUT/GET profile and POST/GET farms (bbox 400 shown); `tests/api/test_profile_farms.py`, `tests/api/test_meta_cors.py`, `tests/api/test_conversation_farm.py`; full pytest 145 passed.
**Sprint:** Sprint-006 · **Milestone:** M-06 · **Owner:** Backend Sub-Agent · **Depends on:** FP-008
**Contract:** `docs/architecture/API_CONTRACT_M06.md` §1, §3, and §9 (`farm_id`)

## 1. Overview
There was no working profile or farm store: the `farms` table needed PostGIS, which isn't installed, and `farmers.name` was NOT NULL even though a new farmer has no name after OTP. This FP adds a PostGIS-free farm table, profile completion, and the reference lists the client needs.

## 2. Business Goal
Advice can use the farmer's real district, crop, stage and area instead of values typed into each question.

## 3. User Story
As a farmer, I set my name and district once and register up to 5 farms, so that the assistant, weather and market screens know where and what I grow.

## 4. Acceptance Criteria
- [x] `GET/PUT /api/farmer/profile` 🔒 (partial PUT): `name` 2–100, `district_id` from the meta list, `preferred_language` `ta|en`. `profile_complete` = name and district set.
- [x] `GET/POST /api/farms`, `PUT/DELETE /api/farms/{id}` 🔒: own farms only (another farmer's farm → 404 `not_found`); max 5 (409 `farm_limit_reached`); lat/lon inside the TN bbox (lat 8.0–13.6, lon 76.2–80.4), enforced in the API **and** by DB CHECKs; lat and lon only together; `area_ha` in (0, 10000]; crop, stage, season and irrigation IDs validated.
- [x] `GET /api/meta/districts`: 38 districts; HQ coordinates from `uzhavan_data/03_weather/processed/tn_district_hq_points.csv` (GeoNames); Tamil names from the Tamil Mannvalam district list (`uzhavan_data/04_soil/soil_health_card/raw/tn_mannvalam/districts.json`), 38/38 found, none invented. `meta.kind:"reference"`.
- [x] `GET /api/meta/crops` (13) and `GET /api/meta/enums` (`crop_stages`, `seasons`, `irrigation_types`, `diary_kinds`). Tamil is `null` where there's no standard common word (Kharif, Rabi, Year-round, Scan).
- [x] `/conversation` accepts `farm_id`: with a valid token, district, crop, stage and area come from the farm and client values are ignored. Anonymous callers' `farm_id` is ignored; another farmer's farm → 404.

## 5. UI Design
None (Flutter). The UI takes acres; the API stores hectares.

## 6. API Contract
As in contract §1 and §3. `POST`/`PUT /api/farms` return the bare `Farm` object (per contract text); `GET /api/farms` and the profile endpoints use `{data: …}`. `Farm` additionally carries `boundary_geojson` (null unless sent).

## 7. Database Changes
`004_auth_profile_farms.sql`: the `farms` table (UUID PK, FK farmer ON DELETE CASCADE, `name`, `district_id`, `village`, `latitude`/`longitude` DOUBLE PRECISION with bbox + pair CHECKs, `boundary_geojson` JSONB, `area_ha` with a CHECK, crop/stage/season/irrigation IDs, timestamps); `farmers.name` DROP NOT NULL; `farmers.district_id`. Existing columns kept. If an old PostGIS `farms` table exists, the new columns are added to it. Backup: `backups/uzhavan_dev_before_FP-008-009_20260925_165947.sql`.

## 8. AI Changes
None to the cognitive engine. The `/conversation` route only fills request context from the farm.

## 9. Agent Responsibilities
Backend: API + migration + meta. Flutter: onboarding, profile and farm screens (acre ↔ ha). QA: device run.

## 10. Testing
`test_profile_farms.py`: profile PUT/GET and validation, farm CRUD, 10 invalid-body cases, bbox edges, ownership 404, 5-farm cap, 401s. `test_meta_cors.py`: 38 districts with the Thanjavur Tamil name, crops, enums, CORS PUT preflight. `test_postgres_integration.py`: the real DB round-trip and the CHECK constraint.

## 11. Security
Every farm query is scoped by the token's `sub`. Ownership failures return 404 (no enumeration). Input is validated before SQL, and all SQL is parameterised.

## 12. Performance
Index `idx_farms_farmer_id`. The meta lists are static and loaded once.

## 13. Documentation
This FP; `scripts/build_district_meta.py` regenerates `backend/meta/data/tn_districts.json` from project data; CHANGELOG.

## 14. Demo Checklist
- [x] PUT profile → `profile_complete:true`
- [x] POST farm → 201; POST outside TN → 400 `location_outside_tamil_nadu`
- [x] `/api/meta/districts` → 38

## 15. Release Notes
> **FP-009: Your profile and farms.** Farmers can save their name, district and village, and register up to five farms with location, area, crop, stage, season and irrigation. The assistant uses the selected farm's details automatically. District names and locations come from official sources, in English and Tamil.
