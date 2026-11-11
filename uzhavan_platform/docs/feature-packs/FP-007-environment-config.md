# FP-007: Environment configuration, API base URL and secure backend settings

**Status:** `COMPLETE` (backend, 2026-09-25). Evidence: `backend/shared/settings.py`; the start-up refusal with `ENV` unset ("ENV: required but not set", exit 1) and with production + placeholder `JWT_SECRET`; `tests/api/test_settings.py` (settings matrix + subprocess start-up refusals); `tests/api/test_auth_flow.py::test_production_without_sms_provider_returns_503_and_logs_nothing`; `tests/api/test_meta_cors.py` (PUT preflight from `https://localhost`, `/health/config`); `requirements.txt` + `requirements-dev.txt` in a Python 3.14 venv → full pytest **145 passed, 0 errors**. The frontend ACs (AC-1/2/3/11) and PRODUCTION_ENVIRONMENT.md (AC-10) belong to the Frontend/Docs sub-agents and aren't covered by this status.
**Sprint:** Sprint-006 (Production Completion)
**Milestone:** M-06: Real application (plan phases 14 + the config half of 13)
**Owner:** Master Agent (spec) → Backend Sub-Agent + Frontend Sub-Agent
**Depends on:** FP-006
**Evidence:** `reports/production_build/PHASE0_BASELINE.md`; code findings listed in §1

---

## 1. Overview
Every later FP (auth, weather, market, schemes, Android) needs the app to reach the right backend with the right secrets. The code has five concrete problems today:
1. **Frontend API URL:** `VITE_API_URL` falls back to `http://localhost:8000`. On an Android phone or emulator, `localhost`/`127.0.0.1` is the phone itself, so every call fails. There's no per-environment configuration and no production HTTPS URL.
2. **CORS** on :8000 allows only `GET, POST, OPTIONS` and three localhost origins. The profile update uses `PUT` and would be blocked. Capacitor origins (`https://localhost`, `capacitor://localhost`) aren't allowed.
3. **Weak secret fallbacks:** `JWT_SECRET` silently defaults to `"change_me_to_a_long_random_string_in_production"` (`backend/conversation/auth.py:17`).
4. **Unsafe default mode:** `ENV` defaults to `"dev"` (`api/auth/main.py:202`), and in dev mode **OTPs are printed to the log**. A production server started without `ENV` would log every farmer's OTP. The auth service also crashes with a bare `KeyError` if `DATABASE_URL` is missing.
5. **No backend dependency manifest:** there's no `requirements.txt` at the repo root, and `asyncpg` is missing, so the 10 auth tests can't even import (baseline: 70 pass / 10 errors).

FP-007 fixes configuration only. **It adds no features and doesn't merge the auth service into :8000** (that path alignment is FP-008).

## 2. Business Goal
- The same build works on desktop, the Android emulator, a physical phone on the LAN, and a production HTTPS server, changing only configuration.
- It is impossible to run in production with default secrets or with OTP logging on.
- The backend is reproducible: one command installs its dependencies, and the full test suite runs.

## 3. User Story
```
As the UZHAVAN operator
I want every environment configured explicitly and validated at start-up
So that the app never silently points at the wrong server or runs with insecure defaults
```

## 4. Acceptance Criteria
- [ ] AC-1 The frontend reads **`VITE_API_BASE_URL`**. `VITE_API_URL` is accepted as a deprecated alias for one release, with a console warning.
- [ ] AC-2 **Production builds fail** (`vite build --mode production`) if `VITE_API_BASE_URL` is unset or isn't `https://`. Dev builds default to `http://localhost:8000` with a console notice.
- [ ] AC-3 `frontend/.env.example` documents four profiles: desktop (`http://localhost:8000`), Android emulator (`http://10.0.2.2:8000`, or `adb reverse` + `http://localhost:8000`), physical device on the LAN (`http://<mac-lan-ip>:8000`), and production (`https://api.<domain>`).
- [ ] AC-4 The backend has one **settings module** (`backend/shared/settings.py`, pydantic-settings) that all entry points read. At start-up it validates: `ENV ∈ {development, test, production}` **required, no default**; in `production`, `JWT_SECRET` must be ≥ 32 chars and not the known placeholder, `DATABASE_URL`, `REDIS_URL` and `CORS_ORIGINS` are required, and `ALLOW_ANONYMOUS` must be false. Missing or invalid settings cause a clear start-up error naming the variable, not a `KeyError` or a silent default.
- [ ] AC-5 **OTP logging** happens only when `ENV=development`. In `production`, if no SMS provider is configured, `/auth/send-otp` returns 503 "OTP delivery not configured" and never logs the code.
- [ ] AC-6 **CORS** origins come from `CORS_ORIGINS` (comma-separated). Development defaults cover `http://localhost:5173`, `http://localhost:5180`, `http://127.0.0.1:5180`, `https://localhost` and `capacitor://localhost`. Methods: `GET, POST, PUT, PATCH, DELETE, OPTIONS`.
- [ ] AC-7 `uzhavan_platform/requirements.txt` (runtime) and `requirements-dev.txt` (pytest etc.) are pinned to the versions that pass the tests. `asyncpg` is included. `pip install -r requirements-dev.txt` in a clean venv then `pytest` gives **80/80 collected, none erroring on import**. The auth tests themselves may still need Postgres; if they fail on DB access rather than import, that's reported, not hidden.
- [ ] AC-8 The `uzhavan_platform/.env.example` is rewritten from the settings module, so **every variable the code reads is documented** (description, required/optional, default, example; no real values). The code reads 27 variables today (list in §6).
- [ ] AC-9 `GET /health/config` (development and test only; 404 in production) returns which features are *configured*, as booleans only and never values: `llm_provider_set`, `database_reachable`, `redis_reachable`, `chroma_present`, `disease_service_url_set`.
- [ ] AC-10 `reports/.../PRODUCTION_ENVIRONMENT.md` (deliverable 4 of the plan) documents every variable, the four frontend profiles, how to generate `JWT_SECRET`, and the emulator/phone run steps.
- [ ] AC-11 No secret appears in any frontend file or built bundle. The grep over `frontend/.output` for `ANTHROPIC_API_KEY`, `JWT_SECRET` and the key prefix `sk-ant-` returns 0 hits.
- [ ] AC-12 Regression: tsc 0 errors; vite build passes; `check:no-fabrication` passes; backend tests ≥ the baseline (70 pass) plus the auth tests now importable.

**Out of scope:** the auth path unification and profile work (FP-008); an SMS provider (later, with your keys); Capacitor packaging (FP-016); HTTPS hosting and a domain (operator decision).

## 5. UI Design
No visible UI change, except that in development builds a small **"API: <host>"** line appears on the Profile → About section, so testers can see which backend the app is using. It's hidden in production builds.

## 6. API Contract
- **New:** `GET /health/config` (development and test only), 200 `{ "env": "development", "llm_provider_set": true, "database_reachable": true, "redis_reachable": true, "chroma_present": true, "disease_service_url_set": true }`.
- **Changed:** CORS preflight now allows PUT/PATCH/DELETE for the configured origins.
- **Changed:** `POST /auth/send-otp`, when `ENV=production` and no SMS provider is configured: `503 {"detail":"otp_delivery_not_configured"}`.
- **Environment variables** read by the code today, all to be documented: `ENV, JWT_SECRET, DATABASE_URL, REDIS_URL, CORS_ORIGINS, ALLOW_ANONYMOUS, LLM_PROVIDER, ANTHROPIC_API_KEY, CLAUDE_MODEL, OPENAI_API_KEY, OPENAI_MODEL, OLLAMA_HOST, OLLAMA_URL, OLLAMA_MODEL, LLM_TIMEOUT_S, EMBED_MODEL, EMBEDDING_VERSION, CHROMA_PATH, TOP_K_RETRIEVAL, RAG_SCORE_THRESHOLD, RAG_VERSION, PROMPT_VERSION, GRAPH_VERSION, AI_VERSION, DISEASE_SERVICE_URL, DISEASE_TIMEOUT_S, WHISPER_PROVIDER, TTS_PROVIDER, GOOGLE_APPLICATION_CREDENTIALS`, plus the `ENABLE_*` flags and `KNOWLEDGE_BASE` from the current `.env.example`.

## 7. Database Changes
None.

## 8. AI Changes
None. LLM provider selection is unchanged and is now validated at start-up (for example, `LLM_PROVIDER=claude` requires `ANTHROPIC_API_KEY`).

## 9. Agent Responsibilities
| Agent | Task |
|---|---|
| Master Agent | FP; review; gates |
| Backend Sub-Agent | B1 `settings.py` + wire it into `backend/conversation/main.py`, `backend/conversation/auth.py`, `api/auth/main.py` · B2 CORS · B3 OTP fail-closed · B4 `/health/config` · B5 requirements files + clean-venv test run · B6 `.env.example` |
| Frontend Sub-Agent | F1 `VITE_API_BASE_URL` + alias + production build guard · F2 `frontend/.env.example` profiles · F3 dev-only API host line |
| QA Sub-Agent | §10 on desktop + Android emulator via `10.0.2.2` **without** `adb reverse` (proves AC-3) |
| Docs Sub-Agent | PRODUCTION_ENVIRONMENT.md |

## 10. Testing
- **Backend unit:** settings validation matrix: ENV missing → start-up error; production + placeholder JWT → error; production + `ALLOW_ANONYMOUS=true` → error; development defaults OK. OTP: production without an SMS provider → 503 and no log line (checked with caplog).
- **CORS:** preflight `OPTIONS` with `Origin: https://localhost`, `Access-Control-Request-Method: PUT` → allowed.
- **Clean-venv reproducibility:** `python -m venv /tmp/x && pip install -r requirements-dev.txt && pytest`.
- **Frontend:** `vite build --mode production` without `VITE_API_BASE_URL` fails; with `https://…` it passes. The bundle secret grep is empty.
- **Emulator:** app at `http://10.0.2.2:5180` with `VITE_API_BASE_URL=http://10.0.2.2:8000` → the conversation request reaches the backend (the network log shows 200 / SSE).

## 11. Security
- Fail-closed configuration: no default secrets, no OTP logging outside development, anonymous access off in production.
- `/health/config` exposes booleans only, and only outside production.
- `.env` stays git-ignored (to be confirmed); `.env.example` holds no real values.
- `JWT_SECRET` generation is documented (`python -c "import secrets;print(secrets.token_urlsafe(48))"`).

## 12. Performance
Settings are parsed once at start-up. No runtime cost.

## 13. Documentation
`PRODUCTION_ENVIRONMENT.md` (new); both `.env.example` files; the README "Run locally" section updated with the four profiles.

## 14. Demo Checklist
- [ ] The backend refuses to start with `ENV` unset (screenshot of the error)
- [ ] Emulator using `10.0.2.2` reaches the backend (no `adb reverse`)
- [ ] `pytest` runs from a clean venv with all tests collected
- [ ] The production build refuses an `http://` API URL

## 15. Release Notes
> **FP-007: Environment configuration (v0.6.0-rc2).** The app now reads its server address from `VITE_API_BASE_URL`, with documented set-ups for desktop, the Android emulator, phones on the same Wi-Fi and production HTTPS. The backend validates its configuration at start-up and refuses insecure settings in production: default secrets, OTP logging, anonymous access. Backend dependencies are now pinned, so the full test suite can be installed and run anywhere.

---

## Sign-offs Required Before Status → COMPLETE
| Gate | Owner | Status |
|---|---|---|
| Planning | Project owner | ☐ **awaiting approval** |
| Architecture | Master Agent | ☐ |
| Backend | Backend Sub-Agent | ☐ |
| Frontend | Frontend Sub-Agent | ☐ |
| AI | – (validation only) | N/A |
| Tests | QA Sub-Agent | ☐ |
| Security | Security Sub-Agent | ☐ |
| Performance | – | ☐ |
| Documentation | Docs Sub-Agent | ☐ |
| Standards | Master Agent | ☐ |
