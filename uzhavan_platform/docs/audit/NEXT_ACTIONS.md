# UZHAVAN AI — Next Actions

**Generated:** 2026-07-01
**Based on:** PROJECT_STATUS.md + PROJECT_HEALTH_REPORT.md audit
**Enforcement:** Every action below must pass through the FP-002 implementation gates.
**Directive:** ED-001 — No new features until farmer journey is complete, tested, documented, usable.

---

## Priority Legend

- 🔴 **CRITICAL** — Blocks FP-002 completion. Cannot ship without this.
- 🟠 **HIGH** — Required for v0.3 release. Must complete in Sprint 4.
- 🟡 **MEDIUM** — Required before v1.0. Can defer to Sprint 5–6.
- 🟢 **LOW** — Quality improvement. Can defer or skip for MVP.

---

## 🔴 CRITICAL — Sprint 4 Implementation Sequence

These must be done in order. Each step unblocks the next.

### Step 1: Database Migration (Agent: Database Agent)
**File:** `database/migrations/004_observability_memory.sql`
**Effort:** 30 min
**Delivers:**
- `request_traces` table — trace_id, session_id, farmer_id, phase latencies (ms), llm_provider, chunks_retrieved, confidence_score, error, created_at
- `ai_memory` table — farmer_id, question_embedding, intent, crop, district, weather_summary, advice, outcome, created_at
- Indexes: `idx_traces_session`, `idx_traces_farmer`, `idx_memory_farmer_intent`

**Gate:** Write SQL, review manually, mark complete. No code review gate for a migration — just correctness check.

---

### Step 2a: Shared Foundation (Agent: Backend Agent)
**Effort:** 45 min
**Files to create:**
- `backend/feature_flags.py` — 8 flags with env-var override
- `backend/shared/models.py` — ConversationState, SourceCitation, ResponseObject, ToolDefinition
- `backend/shared/exceptions.py` — UzhavanError, RAGError, WeatherError, VerificationError

**Depends on:** Nothing (can start now)

---

### Step 2b: Tool Registry (Agent: AI Agent) — parallel with 2a
**Effort:** 1 hour
**Files to create:**
- `backend/tools/registry.py` — ToolDefinition dataclass, ToolRegistry class, as_mcp_manifest()
- `backend/tools/rag_tool.py` — wraps knowledge/rag/engine.py
- `backend/tools/weather_tool.py` — wraps knowledge/weather/open_meteo.py
- `backend/tools/disease_tool.py` — wraps disease service HTTP client
- `backend/tools/market_tool.py` — stub, ENABLE_MARKET=False
- `backend/tools/satellite_tool.py` — stub, ENABLE_SATELLITE=False
- `backend/tools/memory_tool.py` — wraps knowledge/memory/farmer_memory.py

**Depends on:** Step 2a (shared/models.py for ToolDefinition)

---

### Step 3: Knowledge Layer (Agent: AI Agent + RAG Agent) — parallel with Step 2b
**Effort:** 2 hours
**Files to create:**
- `backend/knowledge/rag/engine.py` — refactored from api/advisory/rag_engine.py
  - MUST ADD: 0-chunk guard → return empty list, never call LLM
  - MUST ADD: score threshold ≥0.35 enforced
  - MUST ADD: SourceCitation output format
- `backend/knowledge/weather/open_meteo.py` — Open-Meteo HTTP client
  - district → lat/lon lookup from DB
  - Returns: forecast summary, precipitation_mm, temperature_c, humidity_pct
- `backend/knowledge/disease/client.py` — HTTP client to disease service (port 8001)
- `backend/knowledge/market/agmarknet.py` — stub (raise NotImplementedError if called without flag)
- `backend/knowledge/satellite/sickle.py` — stub
- `backend/knowledge/memory/farmer_memory.py` — ai_memory read/write against PostgreSQL

**Depends on:** Step 2a (shared/models.py, exceptions.py)

---

### Step 4: Decision Layer — LangGraph Graphs (Agent: AI Agent)
**Effort:** 4–5 hours (largest step)
**Files to create (in order):**
1. `backend/decision/state.py` — ConversationState TypedDict
2. `backend/decision/context_builder.py` — assembles ContextDict from all tool results
3. `backend/decision/prompt_builder.py` — loads prompts/{intent}.md (no strings in Python)
4. `backend/decision/observability.py` — writes to request_traces table
5. `backend/decision/graph/__init__.py`
6. `backend/decision/graph/intent.py` — IntentGraph: classify intent → crop/district entities
7. `backend/decision/graph/planner.py` — PlanningGraph: select tools from ToolRegistry
8. `backend/decision/graph/tools.py` — ToolExecutionGraph: asyncio.gather tool calls
9. `backend/decision/graph/verification.py` — VerificationGraph: 5 checks, Tamil fallback on fail
10. `backend/decision/graph/response.py` — ResponseGraph: build ResponseObject from state
11. `backend/decision/graph/conversation.py` — root graph, composes all 5 subgraphs

**Also create — prompt templates:**
- `backend/prompts/system.md`
- `backend/prompts/advisory.md`
- `backend/prompts/weather.md`
- `backend/prompts/disease.md`
- `backend/prompts/crop.md`
- `backend/prompts/scheme.md`

**Non-negotiable VerificationGraph checks:**
1. `citation_check` — at least 1 SourceCitation with confidence ≥0.35
2. `rag_check` — at least 1 RAG chunk retrieved
3. `weather_check` — if weather tool called, verify response is not empty
4. `confidence_check` — overall confidence ≥0.3
5. `context_check` — ContextBuilder output is not empty dict

Any check failing → set `state.final_response = TAMIL_FALLBACK_MESSAGE`, skip LLM call.

**Depends on:** Steps 2a, 2b, 3

---

### Step 5: Conversation Layer — FastAPI + SSE (Agent: Backend Agent)
**Effort:** 2 hours
**Files to create:**
- `backend/conversation/session.py` — session CRUD, history queries from conversation_messages table
- `backend/conversation/streaming.py` — SSE event writer: delta / sources / meta / suggestions / done
- `backend/conversation/rate_limit.py` — Redis `chat_rate:{farmer_id}` counter
- `backend/conversation/main.py` — FastAPI app:
  - `POST /chat` → SSE stream
  - `GET /chat/history` → last 20 sessions
  - `GET /chat/session/{id}` → messages in session
  - `GET /health`

**SSE event sequence:**
```
event: delta      (text chunks as LLM generates)
event: sources    (SourceCitation list when LLM done)
event: meta       (intent, confidence, tools_used)
event: suggestions (3 follow-up questions)
event: done       (close stream)
```

**Depends on:** Step 4 (Decision Layer complete)

---

## 🟠 HIGH — Sprint 4 Parallel Tasks

### Fix .env.example (Agent: Backend Agent)
**File:** `.env.example`
**Effort:** 5 min
**Add:**
```
JWT_SECRET=change_me_in_production
ENV=development
ENABLE_WEATHER=true
ENABLE_DISEASE=true
ENABLE_SCHEMES=true
ENABLE_MARKET=false
ENABLE_SATELLITE=false
ENABLE_MEMORY=true
ENABLE_MCP=false
ENABLE_STREAMING=true
```

---

### Populate ChromaDB (Agent: RAG Agent)
**Effort:** 1–2 hours (depends on TNAU data availability)
**Steps:**
1. Place TNAU PDF/text files in `knowledge/tnau/`
2. Run: `python data_pipeline/normalize_tnau.py --input knowledge/tnau/ --output rag/chunks.jsonl`
3. Run: `python data_pipeline/embed_chunks.py --input rag/chunks.jsonl --chroma rag/chroma/`
4. Verify: minimum 500 chunks embedded, Tamil content present
5. Test: query "நெல் நோய்" and verify ≥3 results with score ≥0.35

**Depends on:** TNAU source data access

---

### Tests — VerificationGraph (Agent: Testing Agent)
**Effort:** 1.5 hours
**Files to create:**
- `tests/decision/test_verification_graph.py`

**Must test:**
- Zero chunks retrieved → VerificationGraph blocks LLM, returns Tamil fallback
- Zero citations → blocks
- Low confidence (<0.3) → blocks
- All checks pass → LLM called, ResponseObject returned
- Tamil fallback is valid Tamil (not empty string)

**Depends on:** Step 4 complete

---

### Tests — ConversationGraph Integration (Agent: Testing Agent)
**Effort:** 2 hours
**File:** `tests/decision/test_conversation_graph.py`

**Must test:**
- Murugan flow: "நாளை மழை வருமா?" → weather tool called → response has weather data
- Disease flow: image path → disease tool called → TNAU guidance returned
- Off-topic flow: "என் பெயர் என்ன?" → off_topic intent → graceful Tamil response
- Hallucination guard: mock RAG to return 0 chunks → no LLM call, Tamil fallback returned

---

### CI/CD Pipeline (Agent: DevOps Agent)
**File:** `.github/workflows/ci.yml`
**Effort:** 1 hour
**Jobs to add:**
1. `lint` — Black + Ruff on `backend/`, `api/`
2. `test` — pytest on all tests, coverage ≥80% for auth service
3. `security` — pip-audit on requirements.txt files
4. `build` — `docker compose build` smoke test
5. `api-smoke` — start auth service, call /health, assert 200

**Trigger:** push to any branch, PR to main

---

### Flutter Scaffold + Auth Screens (Agent: Flutter Agent)
**Effort:** 3–4 hours
**Steps:**
1. `flutter create apps/farmer` — Flutter project scaffold
2. Add dependencies: `http`, `flutter_secure_storage`, `provider` or `riverpod`
3. Create screens:
   - `PhoneInputScreen` — phone number entry, calls POST /auth/send-otp
   - `OTPVerifyScreen` — OTP entry, calls POST /auth/verify-otp, stores JWT
   - `ProfileSetupScreen` — name + language preference, calls POST /farmers/profile
   - `FarmSetupScreen` — district + area + crop, calls POST /farms
4. Basic navigation: Phone → OTP → Profile → Farm → (placeholder Home)

**Depends on:** Auth backend (complete). Does NOT require FP-002 backend.

---

## 🟡 MEDIUM — Sprint 4 Documentation Completions

### Update STANDARDS.md
**File:** `agents/standards/STANDARDS.md`
**Effort:** 30 min
**Change:** Replace all `api/` folder references with `backend/conversation/`, `backend/decision/`, `backend/knowledge/`. Update test coverage target from `--cov=api` to `--cov=backend`.

---

### Remove Duplicate Documents
**Effort:** 5 min total
**Actions:**
1. Delete `docs/ROADMAP.md` (keep `docs/roadmap/ROADMAP.md`)
2. Delete `docs/SPRINT.md` (keep `docs/sprints/SPRINT-004.md`)
3. Delete `docs/UX/Farmer Journey.md` (keep `docs/UX/Farmer_Journey.md`)

---

### Golden User Stories
**File:** `docs/GOLDEN_USER_STORIES.md`
**Effort:** 45 min
**Content:** 5 full user stories from Murugan + Lakshmi + Tamil-only farmer perspectives, each with exact UI steps, expected AI response, acceptance criteria.

---

### Playbooks — Missing 2
**Files:**
- `playbooks/Performance Tuning.md` — latency targets per phase, ChromaDB tuning, LLM timeout config
- `playbooks/Release Checklist.md` — pre-release gates, smoke test steps, rollback procedure

**Effort:** 45 min each

---

### UX Docs — Missing 2
**Files:**
- `docs/UX/Design System.md` — colors (Tamil green #2E7D32, saffron #FF6F00), fonts (Noto Sans Tamil), button sizing (48dp), spacing grid
- `docs/UX/Navigation.md` — tab bar structure, back navigation rules, deep link paths

**Effort:** 30 min each

---

### Evaluation Script — weather_eval.py
**File:** `evaluation/weather_eval.py`
**Effort:** 30 min
**Content:** Calls /chat with weather questions, verifies weather data present in response, checks district-specific accuracy.

---

## 🟡 MEDIUM — Sprint 5 Items (after Murugan demo)

These are blocked on FP-002 completion or deliberately deferred.

| Action | Reason Deferred |
|--------|----------------|
| Add Docker services for backend/conversation + auth | Backend not built yet |
| Add WhatsApp transport layer | Conversation Layer must be stable first |
| AGMARKNET market price integration | Phase 4 per roadmap |
| SICKLE satellite model integration | Phase 3 per roadmap |
| Grafana observability dashboard | Need real trace data first |
| Multilingual intent model fine-tuning | Phase 2 |
| District-specific RAG metadata filtering | FP-004 |

---

## 🟢 LOW — Cleanup / Nice to Have

| Action | File | Effort |
|--------|------|--------|
| Add CHANGELOG.md | `CHANGELOG.md` | 20 min |
| Engineering Dashboard | `docs/ENGINEERING_DASHBOARD.md` | 1 hour |
| Move seed CSVs to `database/seed/` | `database/data/` → `database/seed/` | 10 min |
| pytest coverage target update | `pytest.ini` | 5 min |
| Add `from __future__ import annotations` to all Python files | All `*.py` | 15 min |
| Add mypy.ini for type checking | `mypy.ini` | 15 min |
| Add `backend/*/README.md` layer docs | All backend dirs | 30 min each |

---

## Recommended Sprint 4 Execution Order

```
Day 1 (Foundation)
  AM: Step 1 — Migration 004              (30 min)
      Step 2a — Shared models             (45 min)
      Fix .env.example                    (5 min)
  PM: Step 2b — Tool Registry             (1 hr)
      Step 3 — Knowledge Layer            (2 hrs)

Day 2 (Decision Layer)
  ALL DAY: Step 4 — LangGraph graphs      (4-5 hrs)
           This is the hardest step.

Day 3 (Conversation Layer + Tests)
  AM: Step 5 — FastAPI + SSE             (2 hrs)
  PM: Tests — VerificationGraph          (1.5 hrs)
      Tests — ConversationGraph           (2 hrs)

Day 4 (Flutter + CI/CD)
  AM: Flutter scaffold + auth screens     (3-4 hrs)
  PM: CI/CD pipeline                     (1 hr)
      ChromaDB population                (1-2 hrs, parallel)

Day 5 (Product Quality Gate)
  Murugan Walkthrough (Product Quality Agent)
  Standards Gate (Standards Agent)
  Security Gate (Security Agent)
  FP-002 merge
```

---

## Definition of Done for FP-002

The feature pack is complete when ALL of the following are true:

- [ ] Migration 004 applied to local DB
- [ ] `backend/` three-layer structure fully implemented
- [ ] All 7 LangGraph nodes working
- [ ] VerificationGraph tested with zero-chunk scenario → Tamil fallback (not LLM call)
- [ ] POST /chat SSE endpoint returns all 5 event types
- [ ] ChromaDB populated with ≥500 TNAU chunks
- [ ] Murugan asks "நாளை மழை வருமா?" → gets Tamil weather response with source
- [ ] Flutter app shows chat screen (even if basic)
- [ ] All 18 FP-002 acceptance criteria verified
- [ ] Product Quality Agent walkthrough passed (no veto)
- [ ] Standards Gate passed
- [ ] Security Gate passed (prompt injection check present)
- [ ] 80%+ test coverage on `backend/decision/`
- [ ] CI pipeline runs without failure
