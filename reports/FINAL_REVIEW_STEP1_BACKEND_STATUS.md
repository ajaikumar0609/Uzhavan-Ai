# Final Review, Step 1: Local Services and Backend Status

**Date:** 2026-11-08  **FINAL STATUS: BACKEND PARTIAL**

Infrastructure is up and every discovered API route answers. The AI assistant is not review-ready: retrieval-augmented answering (RAG) is broken in the running app, two agriculture questions are refused as off-topic, and the model's answers are poor and mislabelled "grounded". Details and evidence below. No mobile voice code was touched; Step 1 stops here.

## 1. Services (task 1-2)
| Service | Before | Action | Now |
|---|---|---|---|
| PostgreSQL 14.19 (`uzhavan_dev`, 127.0.0.1:5432) | stopped | `brew services start postgresql@14` | **running**, 20 public tables, data dir unchanged |
| Redis 8.6.1 (127.0.0.1:6379) | stopped | `brew services start redis` | **running**, PONG |
| Ollama 0.12.3 (127.0.0.1:11434) | stopped | `brew services start ollama` | **running**; `qwen2.5:7b-instruct` (4.68 GB) already present, **nothing downloaded** |
| ChromaDB (embedded, `uzhavan_platform/rag/chroma`) | n/a | none | collection `tnau_knowledge`, **520 records** (read-only check); not rebuilt |
| FastAPI | stopped | uvicorn command below | **running** on 0.0.0.0:8000, pid 29990 |
| M4 disease service :8001 | stopped | not started | not running (M4 HOLD) |

All ports 5432/6379/8000/8001/11434 were free before I started. All three services are the Homebrew-managed local instances, bound to 127.0.0.1, development only. No credentials, data directories or schemas were changed. Services *blocked*: none, apart from M4 (intentional) and the phone (no device).

**Exact commands**
```
brew services start postgresql@14
brew services start redis
brew services start ollama
cd uzhavan_platform && .venv/bin/uvicorn backend.conversation.main:app --host 0.0.0.0 --port 8000     # log: scratchpad/uvicorn.log
```
Stop: `kill 29990; brew services stop ollama; brew services stop redis; brew services stop postgresql@14`.
Env (names/values; secrets omitted): `ENV=development`, `LLM_PROVIDER=ollama`, `OLLAMA_MODEL=qwen2.5:7b-instruct`, `ALLOW_ANONYMOUS=true`, `OTP_DEV_LOG=true`, `AUTH_DEMO_MODE=true`, `M4_DEMO_MODE=true`. Python 3.14.3 in `uzhavan_platform/.venv`.

## 2. FastAPI results (task 3)
No health endpoint was invented; routes were discovered from the app and `openapi.json`.
| Route | Result |
|---|---|
| `GET /health` | 200 `status: ok`, model `qwen2.5:7b-instruct` |
| `GET /health/config` | 200: `database_reachable: true`, `redis_reachable: true`, `chroma_present: true`, `llm_provider_set: true` (this route reports presence/reachability only) |
| `GET /metrics` | 200 |
| `/api/meta/{districts,crops,enums}` | 200 |
| `/api/weather/current`, `/forecast` (thanjavur) | 200, ~0.8 s (live external weather call) |
| `/api/market/{commodities,markets,latest}` | 200 |
| `/api/schemes` | 200 |
| `/api/soil` (no location) | 400 `location_required` (correct validation) |
| `/api/satellite/status` | 200 `available: false, reason: under_validation` |
| `/api/farmer/profile`, `/api/diary` (no token) | 401 (correct) |
Ollama reachability is shown by the three `/api/chat` calls in its log during the assistant test. I did not call `/api/auth/*` or `/api/disease/scan` (auth is protected; scanning with `M4_DEMO_MODE=true` would try to launch the M4 service).

## 3. Assistant test (task 4)
Endpoint: `POST /conversation` (SSE), anonymous, `language: "English"`. Raw events: `reports/artifacts/final_review_step1_assistant_results.json`.
| # | Question | HTTP | Time | Ollama called | Tools that ran OK | Sources retrieved | Result |
|---|---|---|---|---|---|---|---|
| 1 | What is photosynthesis? | 200 | 42.9 s (first call; model load) | yes | `weather.irrigation_advice` only | **0** | Tamil text, **incoherent**; flagged `grounded: true` |
| 2 | What is NPK fertilizer? | 200 | 15.1 s | yes | `weather.irrigation_advice` only | **0** | Tamil/English mix, **mostly nonsensical** (N, P, K definitions garbled); `grounded: true` |
| 3 | Why are rice leaves turning yellow? | 200 | 0.01 s | **no** | none | 0 | Intent `off_topic` (confidence 0.3) → canned fallback "Sorry, the information… TNAU help centre: 0431-2371622" |
| 4 | How can I improve soil health? | 200 | 0.01 s | **no** | none | 0 | `off_topic` → same fallback |
| 5 | Explain the importance of crop rotation. | 200 | 20.9 s | yes | `crop.recommend` only | **0** | Tamil, **incoherent** ("Kharif: படி, Rabi: மருந்து"); `grounded: true` |

Per-answer classification: none is source-grounded. Q1, Q2, Q5 are ungrounded generated text from a 7B model; Q3, Q4 are refusals. No answer contained dosage-like numbers (checked with a pattern scan), so no unsupported pesticide dosage appeared. **No citations were returned** (`source_count: 0` on every answer), so no citation could be valid or invalid. Q1, Q2, Q5 report `evidence citations: 1`, but that single citation belongs to the weather/crop tool, not to knowledge-base text, and it is not relevant to the question.

### Findings (evidence-backed)
1. **RAG is broken in the running app.** `RAGAgent._search_tnau` treats `RAGService.retrieve()`'s return value as a list of citations, but `retrieve()` returns a `ServiceResult` wrapper. Reproduced on a scratch copy of the Chroma store: `rag.advisory` fails with `'tuple' object has no attribute 'confidence'`. The agent's `except` hides it (nothing in the server log), so every run shows `failed ≥ 2` tools and zero knowledge-base sources. Files: `backend/tools/agents/rag_agent.py` (call sites around `retrieve(...)`), `backend/knowledge/rag/engine.py:65`. This may be why tests with fakes passed. **I did not change it** (outside this step's scope; fix is small and I can do it on your say-so).
2. **Retrieval relevance is also weak even when called directly** (copy of the store, bge-m3 offline): all 5 queries returned 6 hits with similarity 0.48-0.62, but top hits are largely off-topic (photosynthesis → food-lab enzyme table; soil health → potato/carrot pages). The 520 chunks are TNAU portal pages; coverage of general topics is thin. Fixing finding 1 alone will not give good answers.
3. **Off-topic classifier rejects genuine agriculture questions** (Q3, Q4), including one that names rice and yellowing (entities were extracted: crop = paddy, symptom = yellowing, but intent still `off_topic`).
4. **The grounding check passes ungrounded text** (`grounded: true`, confidence 0.85-0.87) with zero knowledge sources. The metric would mislead a reviewer.
5. **Language:** the backend maps `English` correctly, but the model answered in Tamil. Tamil generation quality from `qwen2.5:7b-instruct` is poor (garbled words). For the review demo I would not show free-text Tamil answers from this model without a fix or a stronger model (e.g. the Claude provider is configured via `LLM_PROVIDER=claude`; not switched, and needs your approval since it sends questions to an external service).
6. Latency: 13-43 s per answer on this machine, which is long for voice use.

## 4. App connection (task 5)
- Flutter default base URL (`lib/core/config/app_config.dart`): Android → `http://10.0.2.2:8000` (emulator only); other → `http://127.0.0.1:8000`; override with `--dart-define=API_BASE_URL=…`. Release builds refuse non-https unless `ALLOW_INSECURE_API=true`.
- **A physical phone using `adb reverse tcp:8000 tcp:8000` needs a build with `API_BASE_URL=http://127.0.0.1:8000`**; the default 10.0.2.2 will not reach the Mac from a real phone. Which value the existing APKs were built with was not checked.
- **`adb devices -l`: no device attached → phone connectivity is NOT tested and I make no claim about it.** The backend is bound to 0.0.0.0, so it is also reachable over Wi-Fi from other machines on the LAN (dev auth bypass flags are on: `ALLOW_ANONYMOUS`, `AUTH_DEMO_MODE`, `OTP_DEV_LOG`). Use a trusted network, or restart with `--host 127.0.0.1` when using adb reverse.

## 5. Remaining errors / risks
1. RAG failure (finding 1): assistant has no knowledge-base grounding.
2. Weak retrieval relevance and thin corpus (finding 2).
3. Off-topic misclassification (finding 3).
4. Misleading `grounded` flag (finding 4).
5. Poor Tamil quality and slow responses (findings 5-6).
6. No phone attached; app↔backend unverified.
7. Database-dependent pytest skips are now unblocked (Postgres up) but I did **not** re-run the suite, because the suite opens the live Chroma store.
8. My assistant test wrote nothing to the DB (anonymous requests aren't diaried); Redis holds 2 rate-limit keys.

## 6. Protected items
No change to auth/OTP/JWT, disease inference or checkpoints, M4, DB schema or records, Chroma data (read-only; the retrieval experiment used a scratch copy). No training, no resets, no downloads, no Git, no deployment. Source files modified this step: **none**.

**Recommended next step (your decision):** fix `RAGAgent` to unwrap `ServiceResult` (small change plus a test), then re-run these five questions; separately decide on the off-topic classifier and the LLM provider for the review.
