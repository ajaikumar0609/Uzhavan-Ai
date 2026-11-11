# FP-010: Weather (current, 7-day forecast, cited advisories)

**Status:** `COMPLETE` (backend, 2026-09-25). Evidence: `tests/api/test_weather.py` (16 tests, mocked httpx incl. provider-failure → 503); a live Open-Meteo call via the dev server (see CHANGELOG entry and the Backend-B report).
**Sprint:** Sprint-006 · **Milestone:** M-06 · **Owner:** Backend Sub-Agent · **Depends on:** FP-007, FP-009
**Contract:** `docs/architecture/API_CONTRACT_M06.md` §0, §4

## 1. Overview
This FP exposes the existing live Open-Meteo client (`backend/knowledge/weather/open_meteo.py`) to the app. The client gains a point-based API (`PointWeatherClient`) that returns only raw provider values, with no defaults (the legacy `WeatherService` used by the cognitive agent is unchanged).

## 2. Business Goal
Farmers see real, current weather and a 7-day forecast for their farm or district, with its source and time.

## 3. User Story
As a farmer, I open Weather and see today's conditions and the week ahead for my farm, with a warning only when a cited TNAU practice applies.

## 4. Acceptance Criteria
- [x] `GET /api/weather/current`, `/forecast?days=1..7`, `/advisories`. Location resolution: `farm_id` 🔒 (farm lat/lon, else its district HQ) › `lat`+`lon` (TN bbox) › `district_id` (HQ from the meta catalogue). `meta.location.resolved_from` says which was used.
- [x] meta: `source:"Open-Meteo"`, `source_url`, `kind` current|forecast, `retrieved_at`, `observed_at` (the provider's current time; **null for the forecast**, because Open-Meteo reports no issue time), `location`, `notes` including "Official IMD warnings are not integrated".
- [x] Provider down, non-2xx or malformed → 503 `service_unavailable`, with no data and no fallback value.
- [x] Redis cache: current 30 min, forecast 3 h (cached payloads keep their original `retrieved_at`).
- [x] WMO code → `condition {en, ta:null}` (English from the Open-Meteo/WMO 4677 table; no verified Tamil strings). An unknown code becomes "Unknown weather code N".
- [x] Advisories come only from `backend/knowledge/weather/advisory_rules.yaml`. There are 2 rules, each citing the TNAU CPG Agriculture 2020 page and quote. The list is empty when no rule fires. Crop rules need `farm_id` (crop + stage).
- [x] No historical data on these endpoints.

## 5. UI Design
Flutter shows `condition.en` when `ta` is null, the location name and resolution, and the notes.

## 6. API Contract
As in §4. Additions: `meta.location.resolved_from` and `meta.location.district_id`; advisory `evidence.matched_days`.

## 7. Database Changes
None (Redis keys `weather:v2:current:<lat>:<lon>` and `weather:v2:daily:<lat>:<lon>:<days>`).

## 8. AI Changes
None. The cognitive engine's `WeatherService` is untouched.

## 9. Agent Responsibilities
Backend: the endpoints and rules. Flutter: the weather screen. Agronomy review: extend the rules only with cited sources.

## 10. Testing
`tests/api/test_weather.py`: district, point and farm resolution; the cache (1 provider call for 2 requests); null passthrough; 503 on ConnectError and HTTP 500 for all three endpoints; validation (400/422); 401 for `farm_id` without a token; 404 for another farmer's farm; advisory firing, including the 64.4/64.5 mm boundary; every rule is cited.

## 11. Security
`farm_id` is resolved only for the token's farmer (404 otherwise). No provider key is used.

## 12. Performance
One Open-Meteo call per location per TTL. Timeout 8 s.

## 13. Documentation
This FP; `advisory_rules.yaml` header (the rule policy); CHANGELOG.

## 14. Demo Checklist
- [x] `curl /api/weather/current?district_id=thanjavur` → live values, `observed_at` set
- [x] `curl /api/weather/forecast?district_id=thanjavur&days=7` → 7 days
- [x] Provider failure → 503 (tests)

## 15. Release Notes
> **FP-010: Live weather.** Current conditions and a 7-day forecast from Open-Meteo for your farm or district, always showing the source and time. Official IMD warnings are not yet included. Farm advisories appear only when a cited TNAU practice applies.

**Deviations:** `observed_at` is null for the forecast (the provider has no issue time). There are only 2 advisory rules, because others found in the CPGs had no citable numeric trigger (e.g. "when temperature is very high"). Rule `url` is null because no verified public URL exists for the 2020 CPG edition, so the rule cites the local PDF name and page.
