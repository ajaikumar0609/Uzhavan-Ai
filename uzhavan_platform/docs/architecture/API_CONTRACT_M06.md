# UZHAVAN M-06 API contract (Flutter ⇄ FastAPI): single source of truth

Version 1.0 · 2026-09-25 · Owner: Master Agent. The backend and Flutter sub-agents both implement **exactly** this. A change needs a version bump noted here.

## 0. Conventions
- One FastAPI app on **:8000** (`backend/conversation/main.py`). The auth, profile, farm, weather, market, scheme, soil, diary, disease and satellite routers are **all mounted there**. The separate `api/auth` service becomes a router library.
- JSON, UTF-8, snake_case. Times are ISO-8601 UTC (`2026-09-25T10:30:00Z`); dates are `YYYY-MM-DD`.
- Auth: `Authorization: Bearer <access_token>`. Endpoints marked 🔒 return 401 without it.
- **Bilingual text:** any human-readable string from the server comes as `{ "en": "...", "ta": "..." }` (`ta` may be null if no verified translation exists; the client then shows `en`).
- **Data envelope** for all information endpoints:
```json
{ "data": ..., "meta": { "source": "Open-Meteo", "source_url": "https://open-meteo.com",
  "kind": "current|forecast|historical|latest_observed|estimated|measured|reference",
  "retrieved_at": "2026-09-25T10:30:00Z", "observed_at": "…|null", "location": {"name":"Thanjavur","lat":10.787,"lon":79.138}|null,
  "notes": [ {"en":"…","ta":"…"} ] } }
```
- **Errors** (FastAPI `detail`): `{ "detail": { "code": "snake_case_code", "message": {"en":"…","ta":"…"} } }`
  - 400 validation · 401 `unauthenticated` · 403 · 404 `not_found` · 409 · 410 `otp_expired` · 422 (pydantic) · 429 `rate_limited` (+ `Retry-After`) · **503 `service_unavailable` / `model_unavailable` / `otp_delivery_not_configured`** (client maps these to UNAVAILABLE) · 500 (client maps to ERROR; never exposes a stack trace).
- **Never fabricate:** if the source has no value, the field is `null` and the client shows "not available". Never substitute a default number.

## 1. Health and meta
- `GET /health` → `{status, version}`
- `GET /api/meta/districts` → `data: [{ "id":"thanjavur", "name":{"en":"Thanjavur","ta":"தஞ்சாவூர்"}, "lat":10.787, "lon":79.138 }]`: the **38 TN districts**, HQ coordinates from `uzhavan_data/03_weather/processed/tn_district_hq_points.csv`. `meta.kind: reference`.
- `GET /api/meta/crops` → `data: [{ "id":"paddy", "name":{"en":"Paddy","ta":"நெல்"} }]` (the fixed list used by profile/farm/market).
- `GET /api/meta/enums` → `crop_stages`, `seasons`, `irrigation_types`, `diary_kinds`, each as `[{id, name:{en,ta}}]`.

## 2. Auth (FP-008)
- `POST /api/auth/send-otp` `{ "phone":"9876543210" }` → `200 { "status":"sent", "expires_in":300, "resend_after":60 }`
  - 400 `invalid_phone` (Indian 10-digit, starting 6–9) · 429 `rate_limited` (max 3 per phone per hour; 60 s resend cooldown) · 503 `otp_delivery_not_configured` (production without an SMS provider).
  - OTP: 6 digits from `secrets`, stored **hashed** (HMAC-SHA256 with a server key), 5-minute expiry, max 5 attempts. **No universal or test OTP ever.** It's printed to the server log only when `ENV=development` **and** `OTP_DEV_LOG=true`.
- `POST /api/auth/verify-otp` `{ "phone", "otp" }` → `200 { "access_token", "refresh_token", "token_type":"bearer", "expires_in":900, "is_new_farmer":bool, "profile_complete":bool }` · 400 `otp_incorrect` · 400 `otp_attempts_exceeded` · 410 `otp_expired` · 404 `otp_not_found`.
- `POST /api/auth/refresh` `{ "refresh_token" }` → new access **and** refresh tokens (rotation; the old one is revoked; reuse of a revoked token → 401 and all of that farmer's tokens revoked).
- `POST /api/auth/logout` 🔒 `{ "refresh_token" }` → `204` (revokes).
- Access JWT: HS256, 15 min, claims `sub`=farmer_id, `phone`, `iat`, `exp`, `typ:"access"`. Refresh: an opaque random token, stored hashed, 30 days.

## 3. Farmer profile and farms (FP-009) 🔒
- `GET /api/farmer/profile` → `data: { farmer_id, phone, name|null, district_id|null, village|null, preferred_language:"ta"|"en", profile_complete, created_at, updated_at }`
- `PUT /api/farmer/profile` (partial) `{ name?, district_id?, village?, preferred_language? }` → updated profile. `name` 2–100 chars; `district_id` ∈ `/api/meta/districts`.
- `GET /api/farms` → `data: [Farm]` · `POST /api/farms` `FarmIn` → `201 Farm` · `PUT /api/farms/{farm_id}` → Farm · `DELETE /api/farms/{farm_id}` → 204 (own farms only; max 5 farms).
- `Farm = { farm_id, name, district_id, village|null, latitude|null, longitude|null, area_ha|null, crop_id|null, crop_stage_id|null, season_id|null, irrigation_type_id|null, created_at, updated_at }`. Lat/lon must fall inside the TN bbox (lat 8.0–13.6, lon 76.2–80.4). The UI accepts acres; **the API stores hectares**.

## 4. Weather (FP-010)
Location resolution: `farm_id` 🔒 (its lat/lon, else its district HQ) › `lat`+`lon` › `district_id` (HQ point). `meta.location` always says which point was used.
- `GET /api/weather/current?…` → `data: { temperature_c, apparent_temperature_c|null, humidity_pct, precipitation_mm, wind_speed_kmph, wind_direction_deg|null, weather_code, condition:{en,ta}, is_day }`, `meta.kind:"current"`, `meta.observed_at` = the provider's model time.
- `GET /api/weather/forecast?…&days=1..7` → `data: { daily:[{ date, temp_max_c, temp_min_c, precipitation_mm, precipitation_probability_pct|null, wind_max_kmph, weather_code, condition:{en,ta} }] }`, `meta.kind:"forecast"`, `meta.observed_at` = the forecast issue time.
- `GET /api/weather/advisories?…` → `data: [{ rule_id, severity:"info|caution", text:{en,ta}, evidence:{…values used…}, rule_source }]`. Only rules defined in `backend/knowledge/weather/advisory_rules.yaml`, each citing its source. The list is **empty when no rule fires**.
- `warnings`: Open-Meteo provides none. `meta.notes` says "Official IMD warnings not integrated". No invented warnings.
- Provider down → 503 `service_unavailable`. Cache: current 30 min, forecast 3 h (Redis). Historical data is never returned on these endpoints.

## 5. Market (FP-011)
Data: `uzhavan_data/08_market/processed/tn_mandi_prices.parquet` loaded into Postgres `mandi_prices` (QC-pass rows only). The snapshot runs to 2026-09-24.
- `GET /api/market/commodities` → `data:[{id, name:{en,ta}, unit, unit_note|null}]`. Coconut carries `unit_note` = "unit unverified (per quintal vs per 1000 nuts)".
- `GET /api/market/markets?district_id=` → `data:[{market, district_id|null, market_type}]`
- `GET /api/market/latest?commodity=&district_id=&market=&limit=20` → `data:[{ commodity, commodity_name:{en,ta}, variety, market, district_id|null, modal_price, min_price|null, max_price|null, unit:"Rs/quintal", arrivals_tonnes|null, observed_on }]`, `meta.kind:"latest_observed"`, `meta.notes` includes the snapshot date. Anything older than 7 days also carries `stale:true`.
- `GET /api/market/trend?commodity=&market=&days=90` → `data:{ points:[{date, modal_price}] }`, `meta.kind:"historical"`.
- **No advice fields.** No forecast endpoint (M6 is not trained).

## 6. Government schemes (FP-012)
Data: `uzhavan_data/09_government_schemes/processed/schemes.jsonl` (136) → Postgres `government_schemes`.
- `GET /api/schemes?q=&level=central|state&crop_id=&active=true` → `data:[{ scheme_id, name:{en,ta}, authority, level, active|null, crops:[…]|null, official_url }]`
- `GET /api/schemes/{scheme_id}` → full record: `description, eligibility_text, benefits, application_method|null, required_documents|null, official_url, source_documents, date_checked, last_updated_on_source`. Missing fields are `null`, never inferred.
- `GET /api/schemes/{scheme_id}/eligibility` 🔒 → `data:{ status:"eligible_known_criteria|not_eligible_known_criteria|more_information_required|cannot_determine", reasons:[{en,ta}], missing_fields:[…], criteria_source_url }`. Rules live only in `backend/knowledge/scheme/eligibility_rules.yaml`, each with a source URL. A scheme without rules returns `cannot_determine`.

## 7. Soil (FP-014)
- `GET /api/soil?farm_id=|district_id=` → `data:{`
  - `regional: { soil_types:[{name:{en,ta}}], source:"TN Agriculture Dept (Tamil Mannvalam)", kind:"reference" }|null,`
  - `nutrient_status: { cycle, parameters:[{param, low_pct, medium_pct, high_pct, samples}], source:"Soil Health Card dashboard", kind:"reference" }|null,`
  - `estimated: { depth:"0-30cm", values:{ph, soc_g_kg, clay_pct, sand_pct, silt_pct, cec, bdod, nitrogen}, source:"ISRIC SoilGrids 2.0", kind:"estimated", caveats:[{en,ta}] }|null,`
  - `measured: [SoilTest] }`
- `POST /api/soil/tests` 🔒 `{ farm_id, sample_date, lab_name|null, ph|null, ec_ds_m|null, oc_pct|null, n_kg_ha|null, p_kg_ha|null, k_kg_ha|null, s_ppm|null, zn_ppm|null, fe_ppm|null, cu_ppm|null, mn_ppm|null, b_ppm|null }` → `201 SoilTest` (`kind:"measured"`, farmer-entered). Range-validated.
- `GET /api/soil/tests?farm_id=` 🔒 → list.

## 8. Diary / history (FP-013 home + diary) 🔒
- `GET /api/diary?limit=50` → `data:[{ entry_id, farm_id|null, kind:"note|observation|expense|income|question|scan", text, amount_inr|null, entry_date, created_at, ref|null }]`
- `POST /api/diary` `{ farm_id?, kind in note|observation|expense|income, text (1–1000), amount_inr?, entry_date }` → 201.
- Assistant questions and disease scans are logged automatically as `question` / `scan` entries (text = the question / "scan submitted"; **never** a fabricated result).

## 9. Assistant (FP-015)
- `POST /conversation` (SSE, existing). Request: `{ question, session_id?, language:"Tamil"|"English", farm_id? }` (🔒 optional; with a token, the server fills district/crop/stage/area from the farm, and client-sent values are ignored).
- Events (`data:` JSON `{event, session_id, conversation_id, timestamp, data}`): `session_started`, `intent_detected`, `planning`, `tool_complete`, `evidence_ready`, `grounding`, `reasoning`, `token` (optional), `sources` `{sources:[{source,title,confidence,url?}]}` (**only when TNAU/RAG evidence was actually retrieved**), `completed` `{answer, is_fallback, grounded:bool}`, `error` `{code, message:{en,ta}}`.
- Voice: the Flutter client uses on-device `speech_to_text` (ta-IN / en-IN following the UI language) and `flutter_tts`. The backend `/voice/stt`/`/voice/tts` stay available but are optional.

## 10. Disease (FP-018)
- `POST /api/disease/scan` multipart `image` (+ `crop_id`) → **until the M4 model is independently approved: 503 `model_unavailable`**.
- Future 200: `data:{ status:"ok|unsure", crop_id, top:{class_id, label:{en,ta}, probability}|null, predictions:[…], model_version, inferred_at, production_eligible:bool, guidance:[{text:{en,ta}, source, source_url}] }`. Doses appear only when present in the cited source.

## 11. Satellite (FP-019)
- `GET /api/satellite/status` → `data:{ available:false, reason:"under_validation", gates:{licence:false, units:false, geography_scope:"Cauvery Delta only", independent_evaluation:"baseline only (val, 14 plots)"} }`. No predictions are served while `available:false`.
