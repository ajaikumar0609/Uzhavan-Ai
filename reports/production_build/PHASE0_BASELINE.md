# Phase 0: baseline and implementation map (2026-09-25, read-only)

Snapshot before any change: `~/Desktop/agri/backups/pre_production_build_20260925_1556.tgz` (frontend + uzhavan_platform source, 593 files, no node_modules).

## Baseline checks
| Check | Result | Log |
|---|---|---|
| Frontend TypeScript (`tsc --noEmit`) | ✅ 0 errors | `baseline_tsc.log` |
| Frontend production build (`vite build`) | ✅ passes | `baseline_build.log` |
| Backend tests (`pytest`, system python3) | **70 passed, 10 errors**. All 10 are `tests/api/auth` failing to import `asyncpg` (missing dependency) | `baseline_pytest.log` |

## Infrastructure on this Mac
Postgres ✅ running (:5432, database `uzhavan_dev`, 17 tables) · Redis ✅ running (:6379) · Docker ✅ installed · backend `.env` ❌ missing · Android SDK + `Pixel_6` AVD ✅ (Chrome 109).

## Implementation map: what exists vs what is connected
| Domain | Backend service | REST route on :8000 | Data | Frontend |
|---|---|---|---|---|
| Conversation / cognitive engine | ✅ 10-node graph (intent → planner → capability resolver → executor → evidence fusion → grounding → prompt → LLM → safety → formatter) | ✅ `/conversation` (SSE) | ChromaDB 520 TNAU chunks | ✅ connected |
| Weather | ✅ `knowledge/weather/open_meteo.py`: **live** Open-Meteo, Redis cache, district coords | ❌ none | live API | mock fallback |
| Market | ❌ `knowledge/market/agmarknet.py` is a **stub** (NotImplementedError) | ❌ | `mandi_prices` table **0 rows**; `uzhavan_data/08_market/processed/tn_mandi_prices.parquet` (1.08 M rows) unused | mock fallback |
| Schemes | ✅ `knowledge/scheme/service.py` (asyncpg, needs a pool) | ❌ | `government_schemes` table **0 rows**; `09_government_schemes/processed/schemes.jsonl` (136) unused | mock fallback |
| Auth / farmer | separate service `api/auth/main.py` (asyncpg; `/auth/send-otp`, `/auth/verify-otp`, `/farmers/profile`, `/farms`, `/farmers/me`) | ❌ not on :8000; paths ≠ frontend | `farmers`, `otp_requests`, `refresh_tokens` tables exist, **0 rows** | onboarding never verifies |
| Disease | client → :8001 `/predict` | ✅ `/api/disease/scan` | :8001 has **no `model_loader.py`** | fabricated fallback |
| Voice | ✅ `/voice/stt` (Whisper), `/voice/tts` (gTTS) | ✅ | – | unused (browser Web Speech instead) |
| Soil | – | ❌ | `soil_types` 10 rows; `uzhavan_data/04_soil/processed` | none |
| Satellite | `api/satellite` (folder) | ❌ | SICKLE (research-only) | none |
| Diary / history | – | ❌ | `chat_sessions`/`chat_messages` tables | mock fallback |
