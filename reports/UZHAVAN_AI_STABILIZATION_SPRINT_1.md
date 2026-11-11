# UZHAVAN AI: Stabilization Sprint 1 Report

**Date:** 2026-11-08  **Result: STABILIZATION PARTIAL**

Backup, configuration guard, test-collection repair, backend and Flutter validation are done. Live-service verification is BLOCKED (PostgreSQL, Redis and Ollama are installed but not running; I was told not to start services). No off-machine backup or Git commit exists yet.

M4 stayed HOLD / NO-GO. No M4 file changed, no seed was run, no training, no model inference.

## 1. Backup (Section 2)
| Item | Value |
|---|---|
| Archive | `/Users/ajaikumarn/Desktop/uzhavan_backups_sprint1/uzhavan_source_backup_20261108_121229.tar.gz` (47.5 MB, 2,297 entries) |
| SHA256 | `19a13ac9fd39868c233a69d5d748560be2a5c2c49621cea2e2b71395bf0bd127` (sidecar `.sha256` beside it) |
| Verified | `gzip -t` OK; archive listable; restored `.git` + `uzhavan_platform/backend` to scratch, `git fsck` clean, `git log` shows `ef50615` |
| Git metadata | all 3 repos' `.git` included (root, `frontend`, `external/SICKLE`) |
| Secrets | none in archive (`.env`, `.env.local` excluded; checked by listing). Only variable *names* recorded, in the JSON |
| Taken before any edit | yes (edits happened after; timestamps confirm) |

**What the archive does NOT contain (important):**
- Datasets and checkpoints: `uzhavan_data` (6.3 GB), `runs` (3.3 GB SICKLE), `uzhavan_ml/runs_m4` + `packages` (2.2 GB), `tnau_crawler/knowledge_base` (1.1 GB). They need their own backup.
- Chroma HNSW `.bin` index files (my `*.bin` exclusion caught them). `chroma.sqlite3` with all 520 rows *is* included; the index is rebuildable from it.
- `mini project/` presentations (128 MB), regenerable build output and venvs.
- **The archive is on the same disk as the project.** It protects against a bad edit, not against disk loss. Copy it off-machine.

Original repo state preserved: no `reset`, `clean`, `checkout`, or staging was run. Root repo still has 0 tracked modifications and the same 28 untracked entries (+ my new files).

## 2. Git and source control (Section 3)
Full detail: `reports/artifacts/uzhavan_git_recovery_plan.md`. Headlines:
- **All of `uzhavan_platform/` and `uzhavan_flutter/` is untracked.** The only commit holds `uzhavan_ml/` and reports. This is the real P0.
- A blind `git add .` would stage 5,775 files including ~1.1 GB of crawled PDFs and a 98 MB pptx. A staged plan is provided instead.
- `.env` files are ignored by sub-`.gitignore`s (verified with `git check-ignore`); the root `.gitignore` has no `.env` rule. Proposed additions are in the plan (not applied).
- Three repos: `frontend/` (32 pending changes) and `external/SICKLE` (third-party) are nested; don't push SICKLE.
- Whether the existing GitHub remotes are private is **unverified**. Check before pushing anything.

## 3. Demo / release configuration (Section 4)
Audit: `reports/artifacts/uzhavan_configuration_security_audit.csv`.

**Exactly how `M4_DEMO_MODE` affects the gate (`disease_scan.py:53`, before the fix):** the route ran `if settings.M4_DEMO_MODE:` *before* the `DISEASE_MODEL_APPROVED` check at line 137. When true, it started/called the M4 service and returned 200, and the `DISEASE_MODEL_APPROVED=false` 503 gate was never reached. The response was labelled (`demo_result`, `demo_mode: true`, `production_certified: false`, "Not Production Certified" note), so it was not silently production-approved. But the flag was **not** in the production validator, unlike `AUTH_DEMO_MODE`, `ALLOW_ANONYMOUS` and `OTP_DEV_LOG`. A production deploy that inherited the dev `.env` would have served experimental disease predictions.

Your local `.env` has `ENV=development`, `M4_DEMO_MODE=true`, `AUTH_DEMO_MODE=true`, `ALLOW_ANONYMOUS=true`, `OTP_DEV_LOG=true`. **I did not change it**; local demos behave exactly as before.

### Files modified
| File | Change | Why |
|---|---|---|
| `uzhavan_platform/backend/shared/settings.py` | +3 lines in `validate_for_env`: production rejects `M4_DEMO_MODE=true` | Closes the gap; same mechanism as the other demo flags |
| `uzhavan_platform/backend/conversation/routes/disease_scan.py` | `if settings.M4_DEMO_MODE and not settings.is_production:` + comment | Defence in depth: even a `Settings` built without validation can't bypass the gate in production; falls through to the fail-closed 503 |
| `uzhavan_platform/tests/api/test_demo_flag_guard.py` | **new**, 9 tests | Proof (below) |
| `uzhavan_platform/tests/unit/conftest.py` | **new** | Satellite collection fix (section 4) |

Before/after: development behaviour unchanged. Production with `M4_DEMO_MODE=true` previously started and bypassed the gate; now it fails at startup with `M4_DEMO_MODE: must not be true in production`. Model weights, checkpoints, thresholds and inference code untouched. Auth/JWT/OTP code untouched.

**Tests added and passing:** production + unsafe flags rejected; production + disease bypass rejected; error text doesn't leak the JWT secret; safe production config still loads with the gate closed; development may enable demo flags; defaults fail-closed; dev demo output explicitly labelled research / not certified; production ignores the bypass at the route (503, model never called); default route state closed. Existing `test_auth_demo.py` / `test_settings.py` still pass, so auth behaviour is unchanged.

**Safe migration plan:** (1) keep dev `.env` as is. (2) For any production/staging deploy, start from `.env.example` and never copy the dev `.env`. (3) Startup now fails loudly if a demo flag is present. (4) When the disease model is eventually approved, flip only `DISEASE_MODEL_APPROVED` through the release gates.

## 4. Backend test collection repair (Section 5)
**Root cause:** `scripts` is a namespace package (no `__init__.py`) that exists twice: `agri/scripts/ingest_sentinel2.py` and `uzhavan_platform/scripts/` (loaders). From `uzhavan_platform/`, only the second is on `sys.path`, so `from scripts.ingest_sentinel2 import ...` raised `ModuleNotFoundError`, and that collection error aborted the whole run. From the repo root both resolve, matching the "six tests pass at root" observation.

**Fix:** new `tests/unit/conftest.py` appends (never prepends) the repo root to `sys.path`, so the namespace package spans both directories without shadowing platform modules. No test removed, skipped, weakened or mocked.

**Full backend run** (`cd uzhavan_platform && ENV_FILE=none .venv/bin/python -m pytest -q -rs`), including the satellite file:

| Collected | Passed | Failed | Skipped | Collection errors |
|---|---|---|---|---|
| 269 | 262 | 0 | 7 | 0 |

Before the fix: 263 collected + 1 collection error (run aborted; that count already included the 9 new guard tests). The 6 satellite tests now collect: 263 + 6 = 269. Per-test list in `uzhavan_backend_test_results.csv`.

**All 7 skips have one reason, "local Postgres not reachable"** (`test_market.py:145,169`, `test_postgres_integration.py:35,75`, `test_schemes.py:177,210`, `test_soil.py:183`). Status: **BLOCKED**. Database integration has **not** been verified. The earlier audit's "247 passed, 7 skipped (satellite file excluded)" is not directly comparable: this run adds the 6 satellite tests and the new guard tests, and I did not re-derive the exact delta.

Side effect found: the suite opens the live `rag/chroma` store, so file mtimes changed. Row data is identical before/after (520 rows, same fingerprint). Tests should use a temp `CHROMA_PATH`: queued for Sprint 2, not changed here.

## 5. Services (Section 6)
Detail: `reports/artifacts/uzhavan_service_health.csv`. Nothing was started, installed or modified.

| Service | Endpoint | Installed | Status |
|---|---|---|---|
| PostgreSQL | 127.0.0.1:5432 | 14.19 | **Not running** |
| Redis | 127.0.0.1:6379 | 8.6.1 | **Not running** |
| Ollama | localhost:11434 | client 0.12.3 | **Not running** |
| ChromaDB | embedded `rag/chroma` | 1.5.9 | Readable, 520 embeddings in `tnau_knowledge` |
| M4 disease service :8001, backend :8000 | | | Not running (expected) |

Until these run, the assistant, OTP/Redis flow, and DB-backed modules are verified only against fakes.

## 6. Flutter (Section 7)
- `flutter analyze`: **No issues found.**
- `flutter test`: **148 passed, 0 failed.**
- Build config: release buildType is signed with the **debug keystore** (`android/app/build.gradle.kts:34`, comment says release signing is a later sprint). Fine for testing, **not acceptable for distribution**. Default API URL is `http://10.0.2.2:8000` while the manifest sets `usesCleartextTraffic="false"`: confirm the release build passes an https `API_BASE_URL`. An APK from 26 Sep (release) and 30 Sep (debug) exist; no new build was made.
- **No physical-device validation was performed in this sprint.** The Samsung screenshots in `reports/` are from earlier work.
- No UI/app code changed.

## 7. Documentation baseline (Section 8)
Checked the repo, `uzhavan_platform/docs/`, and `~/Downloads`/`~/Documents` filenames.
- **Found in repo:** `uzhavan_platform/docs/PRD.md`, `PROJECT_BIBLE.md`, `FRAMEWORK.md`, `data_dictionary.md`, `er_diagram.md`, `architecture/` (`CONVERSATION-SERVICE.md`, `API_CONTRACT_M06.md`), `adr/ADR-008-three-layer-architecture.md`, `roadmap/`, `milestones/`, `sprints/`, `feature-packs/`.
- **No SRS or SDD file found** in those locations. They may exist only in your ChatGPT workspace, as you said; I can't see them.
- **Recommended destination:** `uzhavan_platform/docs/srs/SRS.md` and `uzhavan_platform/docs/architecture/SDD.md`, committed after the code backup. I did not create or invent any requirement IDs.

## 8. Acceptance checklist
- [x] Verified source backup exists (same-disk only; see caveat)
- [x] Git history and working changes preserved
- [x] No secrets exposed or committed (values never printed; `.env` excluded)
- [x] Production demo configuration protected
- [x] M4 HOLD / NO-GO untouched (no file under `uzhavan_ml/` newer than the backup)
- [x] Satellite collection issue repaired
- [x] Full backend results recorded (269 / 262 / 0 / 7 / 0)
- [x] Flutter analyze + tests recorded
- [x] PostgreSQL, Redis, Ollama accurately reported: **all down**
- [x] No production behaviour unintentionally modified (one intended production-only change: `M4_DEMO_MODE` now refused)
- [ ] Off-machine backup / Git commit of application code: **not done, needs your authorization**
- [ ] Live-service integration: **BLOCKED**

## 9. Remaining concerns
1. **P0**: application code still untracked; backup is single-disk.
2. Release APK signed with debug key; https API URL for release unconfirmed.
3. `DEMO_OTP` / `DEMO_PHONE_NUMBER` have hard-coded defaults in `settings.py`. Inert in production, but left alone because authentication code is protected.
4. Test suite touches the real Chroma store.
5. Confirm that the existing GitHub remotes are private.
6. Reported percentages remain provisional (79 PRD requirements vs. an unreconciled SRS).

## 10. Test commands
```
cd uzhavan_platform
ENV_FILE=none .venv/bin/python -m pytest tests/api/test_demo_flag_guard.py tests/api/test_settings.py tests/api/test_auth_demo.py tests/api/test_diary_disease_satellite.py -q   # 46 passed
ENV_FILE=none .venv/bin/python -m pytest tests/unit/test_satellite_pipeline.py -q                                                              # 6 passed
ENV_FILE=none .venv/bin/python -m pytest -q -rs                                                                                                 # 262 passed, 7 skipped
cd ../uzhavan_flutter && flutter analyze && flutter test                                                                                         # clean; 148 passed
```

Stopping here as instructed. No further phase started.
