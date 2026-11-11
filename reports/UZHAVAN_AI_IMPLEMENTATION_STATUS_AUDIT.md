# UZHAVAN AI — Implementation Status Audit

**Date:** 2026-11-07 · **Mode:** read-only forensic audit · **Workspace:** `~/Desktop/agri`
**Requirements baseline:** `uzhavan_platform/docs/PRD.md` v1.0. **No SRS or SDD exists** in the workspace, so the PRD (nine MVP flows, NFRs, launch criteria) is the baseline. The earlier reports `TODAY_80_PERCENT_STATUS.md` and `PHYSICAL_ANDROID_ASSISTANT_FIX_REPORT.md` were treated as claims to check, not as evidence.

Application source, models, datasets and `uzhavan_ml/model_status.json` were not changed. The only files written are this report and the CSV/JSON files in `reports/artifacts/`.

## 1. Executive summary

| | Result |
|---|---|
| **Implementation progress** | **56.7 %** |
| **Verified completion** | **40.4 %** |
| Requirements scored | 79: 23 verified, 16 implemented but unverified, 16 partial, 2 mock, 16 not implemented, 6 blocked |
| Tests run today | Flutter analyze clean; Flutter 148/148 pass; backend 247 pass, 7 skipped, and the default `pytest` run aborts at collection (see 11) |
| Services up during the audit | None: no Android device, Postgres, Redis, Ollama or backend |

UZHAVAN AI is a solid, well-tested **application shell**. Auth, profile and farms, diary, weather, market, schemes, soil, bilingual UI and voice UI logic are implemented with automated tests. The **AI value proposition is not demonstrably complete**:

- No disease model is approved. MVP flows 6 and 7 are unmet.
- Live LLM answers, RAG relevance and hallucination rates have no current evidence.
- Production infrastructure, compliance and CI are absent.

The 56.7 % is the weighted result of the scoring model you specified. Blocked items score 0. Verified credit is given only where a test or command passed during this audit.

## 2. Research objectives (from PRD)

A Tamil-first, TNAU-grounded agricultural assistant for Tamil Nadu smallholders. It covers OTP registration, a farm profile, Tamil/English/Tanglish Q&A with citations, weather and irrigation advice, leaf-disease identification with treatment, scheme eligibility, and a dashboard. The research track adds SICKLE satellite models and M4 groundnut disease models.

## 3. Current architecture (verified in code)

- **Flutter app** (`uzhavan_flutter`, Riverpod): features are assistant, auth, diary, farm, home, market, meta, profile, satellite, scan, schemes, settings, shell, soil and weather.
- **FastAPI app** (`backend/conversation/main.py`): 14 routers and about 36 endpoints (`uzhavan_api_inventory.csv`).
- **Cognitive pipeline** (LangGraph, `backend/cognitive/graph/nodes/`): intent, planner, capability_resolver, executor, evidence_fusion, prompt_builder, llm_node, grounding_validator, safety_validator and formatter, with an LLM service (Ollama default) and a voice spoken-planner.
- **Data stores:**
  - PostgreSQL: 8 migrations, 25 tables.
  - Redis: rate limits and tokens.
  - ChromaDB: `uzhavan_platform/rag/chroma`, **520 vectors** (verified read-only).
  - Open-Meteo: live weather.
- **Disease:** the backend scan route is gated (503 `model_unavailable`) unless `M4_DEMO_MODE=true`. In that case it spawns a research inference server.
- **Other directories:**
  - `frontend/` (TanStack/React) is untracked and out of scope for the PRD.
  - `uzhavan_ml/` holds M4 and SICKLE research code.
  - `uzhavan_data/` is a 14 GB catalogue.
  - Legacy empty or duplicate directories remain under `backend/` and `uzhavan_platform/` (`advisory`, `gateway`, `market`, `notifications`, `schemes`, `weather`, `api`, `apps`, `agents`).

## 4. Work completed (verified today by automated tests)

- **Backend:**
  - OTP and JWT flow with rotation and logout.
  - Profile, farms, diary, meta, health.
  - Weather, market, schemes, soil.
  - Satellite status gate.
  - Disease upload validation and 503 gate.
  - Multi-turn context.
- **Flutter:**
  - Analyze clean, 148 tests pass.
  - Localization, home, shell and routing, error states.
  - Scan UI, soil/diary/satellite screens.
  - Token refresh.
  - Voice state banner, stop and interrupt, spoken-text planning.

## 5. Work partially completed

- **AI assistant:** the pipeline is tested with a faked LLM.
  - Intent detection is keyword-based.
  - The citation rule was relaxed on 28 Sep for general guidance.
  - There is no benchmark.
- **Disease:** gated scan route and research models only.
- **Treatment knowledge:** about 18 disease rows, not tied to a scan result.
- **Schemes:** application guidance is missing for 124 of 136 schemes (data report).
- **Sentinel-2 pipeline:** its tests pass only when run from the repo root.
- **Hardening:** secrets, version control and observability are only partly in place.

## 6. Not implemented

- Account erasure and a consent flow (DPDPA).
- Answer feedback and the GUS-1 to GUS-3 end-to-end tests.
- Crop recommendation (GUS-3).
- Offline cache (only `shared_preferences` is present).
- Farmer memory (module exists but is not referenced by the graph).
- A market refresh scheduler.
- CI/CD, hosted staging or production, and monitoring.
- Performance measurement, a security review and SBOM, and the pilot.
- Hallucination benchmark results (`evaluation/results` is empty).
- A Tamil STT accuracy evaluation.

## 7. Blocked

- Live SMS (DLT registration).
- Production disease inference and external model validation: M4 HOLD, and no model passes the gates.
- Rice disease: Paddy Doctor requires a login.
- Farmer-facing satellite predictions: licence unverified, georeferencing stripped, Cauvery Delta only, research-only models.
- Copernicus CDS access: no account.
- data.gov.in feeds: no API key.

## 8. Dataset inventory summary (`uzhavan_dataset_inventory.csv`)

The catalogue (`master_catalog.json`, 2026-09-25) lists 46 entries: 29 source, 6 derived, 1 reference, 1 planned and 9 blocked.

- **Held:** 36 entries, 14.15 GB under `uzhavan_data`, plus SICKLE (15 GB) in place.
- **Licences:** 20 of 46 are still marked UNVERIFIED. These include SICKLE, TNAU, Agmarknet, IMD, NASA POWER, schemes and Mannvalam.
- **Counts:** I did not recompute the large dataset counts. The CSV repeats catalogue counts and labels them as such.
- **SICKLE:** 2,370 CSV rows, 2,164 with masks, 351 plots. The project's own notes record georeferencing as stripped.
- **Actually used by the app** (from code and docs, with the database down so counts are not re-verified):
  - Mandi prices loaded to Postgres.
  - 136 schemes.
  - Soil summaries.
  - TNAU chunks in Chroma (520).
  - Live Open-Meteo.
- **Used for training (research only):** SICKLE for M1–M3 and the VIT multi-crop and Sasmal groundnut data for M4.
- Presence in a directory does not mean the data was used for training.

## 9. AI/ML status

**Disease (M4).** Production status: **not approved; the safety gate is closed by default.**

| Run | Evidence |
|---|---|
| V1 | 3 seeds, checkpoints present in `uzhavan_ml/runs_m4`. Validation 98.7 %, but on the external West Bengal groundnut set healthy recall is 0.0017. |
| V2.2 | Reports a three-seed mean full-set macro-F1 of **0.834 ± 0.116** (seeds 0.855 / 0.709 / 0.939). The gate is ≥ 0.85, so it **fails**, and the seed spread is large. Coverage 78 % and accepted accuracy 87.8 % at τ = 0.70 also miss their gates. |
| V2.3 / V2.3.1 | Regress: V2.3.1 healthy recall falls from 70 % to 33.7 % as rust recovers. |

- **V2.2 Seed 42 clean reproduction: outcome UNKNOWN.** Only `m4_v2_2_repro_config_audit.csv` (every parameter EXACT) and `m4_v2_2_repro_environment.csv` exist, with no metrics, log, run directory or checkpoint. `uzhavan_ml/runs_m4_v2` and `runs_m4_v2_3_1` are empty on this machine. The repro files record a different host (Windows, RTX 4050, `Acer ALPHA`). Do not assume it finished.
- **Provenance conflict.** The three-seed report says seeds 1337 and 2024 were evaluated on 2026-09-28, while the project rule and the Android fix report say they were never run. This needs to be reconciled.
- `model_status.json` and the registry are dated 25 Sep and still show M4 as "PLANNED". They are stale.
- **Language intelligence:**
  - Ollama has `qwen2.5:7b/3b` and `mistral` installed, but the server is not running.
  - `LLM_PROVIDER=ollama` and `ANTHROPIC_API_KEY` is empty, so there is no Claude fallback configured.
  - No live generation was verified today.
- **Satellite:** every SICKLE model is RESEARCH-ONLY. M2 uses n = 14 plots and has wide confidence intervals. The app exposes only the status gate.

## 10. Component status

**Flutter.**
- Complete and tested: core screens and navigation.
- Missing: offline mode.
- Partial: accessibility, with TalkBack untested.
- The release APK/AAB are dated 26 Sep, **before** the 28 Sep voice and assistant fixes. A debug APK from 30 Sep exists.

**Backend.**
- Functional and tested against in-memory repositories and fakeredis.
- Real Postgres and Redis paths are untested today.
- `backend/disease/m4_client.py` hardcodes `/Users/ajaikumarn/...` paths and launches a subprocess from a request handler.
- The Chroma path is `./rag/chroma`, relative to the working directory. Starting from the repo root would hit `rag/chroma`, which has **0** embeddings.

**Voice assistant — your specific question.** The fixes are present in code: a 1.8 s silence timer at `voice_services.dart:104`, the `_wasVoiceInput` flag in `assistant_screen.dart`, a `ta-IN`/`ta_IN`/`tam` language fallback, and a listening/thinking/speaking banner with a stop button. The 148 Flutter tests, with a fake STT/TTS, pass. **Physical proof is only the earlier report** (logcat excerpt and PNGs in `reports/`). No device was connected today, so I mark it **IMPLEMENTED, NOT RE-VERIFIED ON DEVICE** and not PASS. The release build predates the fix. Tamil STT accuracy has never been measured.

**External services.**
- Open-Meteo: wired.
- Agmarknet: loaded as static data.
- SMS: blocked.
- Claude: not configured.
- Ollama: installed but down.

## 11. Testing results (`uzhavan_test_inventory.csv`)

| Suite | Result |
|---|---|
| `flutter analyze` | No issues |
| `flutter test` | **148 / 148 pass** |
| Backend `pytest` (default) | **Aborts: 1 collection error** (`tests/unit/test_satellite_pipeline.py` imports `scripts.ingest_sentinel2`, which lives at repo-root `scripts/`) |
| Backend, excluding that file | **247 pass, 7 skipped** (Postgres unreachable) |
| `test_satellite_pipeline.py` from repo root | 6 pass |
| Earlier docs claimed | 241 backend / 144 Flutter. Counts have since grown. |
| Integration or device E2E, GUS tests | None exist |
| RAG / hallucination benchmark | Never run (`results/` empty) |

## 12. Deployment and security status

- **Local development only.**
- `.github/workflows` is empty.
- No hosted environment, HTTPS or India-region hosting, backups or monitoring.
- Sessions and traces are in memory.
- Dockerfiles exist for advisory, disease and pipeline only.
- **Version control is a major risk.** The repo has one commit, `ef50615`.
  - `uzhavan_platform/`, `uzhavan_flutter/`, `frontend/` and `rag/` are **untracked**.
  - `*.pt` and `uzhavan_data/` are gitignored.
  - The repo contains only reports, M4 scripts and docs, with no remote push confirmed.
- The development `.env` has `AUTH_DEMO_MODE=true`, `ALLOW_ANONYMOUS=true`, `OTP_DEV_LOG=true` and **`M4_DEMO_MODE=true`**. This contradicts the "disease gate closed" statement in earlier reports. Secret values were not read or printed.

## 13. Requirement traceability

The full matrix is in `uzhavan_implementation_matrix.csv` (79 rows with source files, endpoint, screen, test, status and remaining work). Of the nine MVP flows:

| MVP flow | Status |
|---|---|
| 1 OTP register | Verified in tests (SMS not live) |
| 2 Farm profile | Implemented, backend verified |
| 3 Multilingual question | Partial |
| 4 Cited TNAU answer | Partial: pipeline tested, live and citation policy unverified |
| 5 Weather and irrigation advice | Implemented; advisories are rule-based |
| 6 Leaf scan | **Blocked** |
| 7 Treatment | Partial |
| 8 Scheme eligibility | Implemented, DB claim unverified |
| 9 Dashboard | Verified |

## 14. Completion percentages

Derivation: score = mean of requirement scores (V 1.0, I 0.75, P 0.5, M 0.1, N 0, B 0) × weight. Verified score counts only items with automated evidence from this audit.

| Workstream | Weight | Implementation | Verified |
|---|---:|---:|---:|
| Flutter UI and navigation | 15 | 80.0 % | 60.0 % |
| Backend and APIs | 15 | 66.7 % | 55.6 % |
| Authentication | 5 | 50.0 % | 50.0 % |
| AI assistant, LLM and RAG | 15 | 53.5 % | 30.0 % |
| Voice | 10 | 75.0 % | 37.5 % |
| Disease vision | 10 | 38.9 % | 27.8 % |
| Weather, market, soil, schemes | 10 | 56.2 % | 50.0 % |
| Satellite | 5 | 40.0 % | 30.0 % |
| Database and infrastructure | 5 | 40.7 % | 10.7 % |
| Testing, security, deployment | 10 | 31.2 % | 25.0 % |
| **Total** | 100 | **56.7 %** | **40.4 %** |

**Other views.**

| View | Implementation | Verified |
|---|---:|---:|
| Core mobile app (Flutter + voice) | 78 % | 51 % |
| Backend (+ auth) | 62.5 % | 54 % |
| AI (assistant, disease, satellite) | 46 % | 29 % |
| Integration (weather, market, soil, schemes) | 56 % | 50 % |
| Testing | 31 % | 25 % |
| Production readiness | 34 % | 20 % |

Dataset preparation is 36 of 46 catalogued sources held, with 20 licences unverified.

**Limitations.**
- The requirement list is my decomposition of the PRD and is not a formal SRS. Different splits would shift the percentages by a few points.
- Authentication scores 50 % because SMS is blocked, demo flags are on and DPDPA is absent.
- Scores for items with Postgres or Redis evidence are capped by services being down today.
- Historical manual evidence is deliberately excluded from "verified".

## 15. Critical findings

1. Application code is not under version control, so one disk failure loses it.
2. The dev environment enables demo, anonymous and M4-demo flags. `M4_DEMO_MODE` bypasses the disease safety gate.
3. No disease model meets its gates. V2.2 seed variance is large, V2.3/V2.3.1 regress, and the V2.2 Seed 42 reproduction result is unknown.
4. Assistant quality is unmeasured. The citation rule was relaxed, RAG depends on the working directory, and there is no benchmark output.
5. The default `pytest` run fails, there is no CI or E2E, and the DPDPA features are missing.

## 16. Remaining backlog

20 items with severity, dependency and acceptance criteria are in `uzhavan_remaining_work.csv`: 4 at P0, 8 at P1, 6 at P2 and 2 at P3.

## 17. Recommended roadmap

1. **Protect and harden (days).** Commit and back up the code, add the demo-flag startup guard, remove hardcoded paths, fix the pytest collection error and add CI.
2. **Prove what exists (1–2 weeks).**
   - Bring up Postgres, Redis and Ollama.
   - Rebuild the release APK from current source.
   - Run one recorded Samsung smoke test: Tamil voice, auto-send, cited answer, auto-speak, stop.
   - Run `evaluation/benchmark.py`.
   - Re-verify the database counts.
3. **Close compliance and MVP gaps.** Account erasure, consent, GUS-1 to GUS-3 tests, a citation policy and an offline cache.
4. **Disease.** Keep the gate closed. Reconcile run provenance, then follow the M4 hold: reproduce V2.2 Seed 42 and review calibration before any new training.
5. **Later:** staging deployment, pilot, licence verification and satellite validation.

**AUDIT STATUS: PARTIAL.** The code, tests and artifacts were inspected and run. Live behaviour (device, LLM, Postgres, Redis) could not be re-verified because the services and device were unavailable.

**RECOMMENDED NEXT PHASE:** Stabilisation and verification of the existing product (items 1 and 2 above), with no M4 work until the hold is lifted.
