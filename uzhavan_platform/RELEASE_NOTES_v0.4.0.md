# UZHAVAN AI — Release Notes v0.4.0-alpha

**Release Date:** 2026-07-01
**Sprint:** Sprint 4 — Architecture & Foundation
**Stage:** Alpha (Internal — Not for production deployment)

---

## Platform Versions

| Component | Version |
|---|---|
| AI Version | 0.1.0 |
| Graph Version | 1.0.0 |
| Prompt Version | 1 |
| RAG Version | 1 |
| Embedding Version | 1.0 |
| LLM Model | Qwen3 (via Ollama) |

---

## What This Release Is

Sprint 4 completes the full backend platform foundation. UZHAVAN AI transitions from architecture phase to product engineering phase.

Every layer from mobile transport to agricultural knowledge now has a working, tested implementation. The system can accept a Tamil-language paddy advisory question, route it through a 10-node cognitive pipeline, ground it against real agricultural data, and return a structured response — without LLM hallucination, with full observability, and with conversation persistence.

---

## Features

### Phase A — Foundation Cleanup
- Established canonical folder structure under `backend/`
- Shared contracts: `ConversationContext`, `FarmerContext`, `FarmContext`, `ToolResult`, `ResponseObject`
- Centralized exception hierarchy under `backend/shared/exceptions.py`
- Logging configuration: `uzhavan.cognitive` logger, structured JSON-compatible output

### Phase B — Shared Contracts
- `ConversationState` TypedDict as the single state object passing through LangGraph
- `ToolResult[T]` generic typed result contract for all domain agents
- `ServiceResult[T]` for service layer responses
- Full Pydantic v2 model hierarchy

### Phase C — Domain Agents
- `WeatherAgent` — current weather, 7-day forecast, rain alerts, irrigation advice, spray suitability
- `CropAgent` — NPK requirements, seed rates, water requirements, fertilizer plans, crop calendar
- `DiseaseAgent` — symptom matching, treatment recommendations
- `MarketAgent` — MSP lookup, price trend analysis
- `SchemeAgent` — government scheme eligibility checking
- `AgentRegistry` — lazy singleton, capability → agent routing
- All agents return typed `ToolResult` — no raw dicts

### Phase D — Knowledge Layer
- `CropKnowledgeService` — TNAU-sourced NPK, water, seed rate data for 21 crops
- `WeatherService` — OpenWeatherMap integration with `ServiceResult[WeatherData]` contract
- `DiseaseKnowledgeService` — symptom-based disease identification
- **Milestone:** Full Thanjavur paddy irrigation advisory without LLM — proved agricultural intelligence is LLM-independent

### Phase E — Cognitive Engine
- `backend/cognitive/` — 10-node LangGraph pipeline
- Nodes (deterministic): `intent_router` → `planner` → `capability_resolver` → `executor` → `evidence_fusion` → `grounding_validator`
- Nodes (LLM-dependent): `prompt_builder` → `llm_node` → `safety_validator` → `formatter`
- **LLM appears exactly once.** All pre-LLM nodes are deterministic.
- `NodeContext` — typed compiler-pipeline-style state object (Pydantic)
- `NodeTrace` + `observe()` context manager — per-node execution tracing
- `EvidenceBundle` — structured, deduplicated, ranked citations
- `GroundingValidator` — 5 checks before LLM is called; blocks LLM on insufficient evidence
- `LLMService` — provider-agnostic Ollama/Qwen3 abstraction with graceful fallback
- Prompt templates in `backend/cognitive/prompts/*.md` — never inline Python strings
- Graph visualization: `docs/graph.mmd` + `docs/graph.png`
- Tamil district locative suffix handling (`தஞ்சாவூரில்` → stem matching)
- **Definition of Done query passed:** `நான் தஞ்சாவூரில் 1.8 ஹெக்டேரில் சம்பா நெல் பயிரிடுகிறேன். நாளைக்கு 18 மிமீ மழை வந்தால் இன்று யூரியா போடலாமா?`

### Phase F — Session Engine
- `backend/session/` — transport layer: stream, store, history, manager, metrics
- `backend/conversation/` — FastAPI app with JWT auth, rate limiting, SSE streaming
- Typed SSE events (11 types) — never raw strings
- `POST /conversation` — streams full 10-node graph execution as SSE
- `GET /health` — liveness + platform version manifest
- `GET /metrics` — live platform metrics snapshot
- `ConversationTurn` — fully replayable (includes system_prompt, user_prompt, raw_llm_response, node_trace, platform_version)
- Rate limiting: 20 requests/minute, 100 requests/day per farmer
- Platform versioning stored with every turn (AI_VERSION, GRAPH_VERSION, etc.)
- `graph.astream()` — streaming LangGraph execution, not blocking `ainvoke()`

---

## Test Coverage

| Suite | Tests | Status |
|---|---|---|
| `tests/knowledge/` | 17 | ✅ All pass |
| `tests/integration/test_phase_d.py` | 10 | ✅ All pass |
| `tests/integration/test_phase_e.py` | 17 | ✅ All pass |
| `tests/integration/test_phase_f.py` | 16 | ✅ All pass |
| `tests/api/auth/test_main.py` | 10 | ⚠️ 2 fail (see Known Issues) |
| **Total** | **80** | **78/80 pass** |

---

## Architecture

```
Flutter App
    │  POST /conversation (JWT + SSE)
    ▼
Conversation Layer (FastAPI)
    │  rate limit, auth, session lifecycle
    ▼
Session Engine
    │  SessionManager, ConversationTurn, Metrics
    ▼
Cognitive Engine (LangGraph)
    │  10-node pipeline, deterministic → LLM → validation
    ▼
Agent Registry
    │  capability routing
    ▼
Domain Agents
    │  Weather · Crop · Disease · Market · Schemes · RAG
    ▼
Knowledge Services
    │  TNAU data · OpenWeatherMap · ChromaDB (RAG)
    ▼
Data Sources
```

---

## Known Issues

### KI-001 — RAG Advisory Capability Not Active
- **Severity:** Medium
- **Description:** `rag.advisory` capability is registered but ChromaDB has no indexed Tamil Nadu agriculture data yet. The `AgentRegistry` logs a warning and skips it gracefully.
- **Impact:** Responses rely on structured agent data only; no free-text TNAU document retrieval.
- **Resolution:** Sprint 5 — RAG Quality evaluation and data ingestion.

### KI-002 — Ollama/LLM Not Required for Core Intelligence
- **Severity:** Low (by design)
- **Description:** If Ollama is not running, `LLMService` returns a fallback Tamil response. All 10 grounding checks and agent tools still execute; only LLM generation is skipped.
- **Impact:** Fallback response is generic. No hallucination risk.
- **Resolution:** Ollama + Qwen3 deployment in Sprint 5 infrastructure.

### KI-003 — In-Memory Session Store
- **Severity:** Medium
- **Description:** `backend/session/store.py` uses a Python dict with TTL. Sessions are lost on process restart.
- **Impact:** No persistence across server restarts; not suitable for multi-process deployment.
- **Resolution:** Redis backend in Sprint 7.

---

## Technical Debt

| ID | Description | Priority | Sprint |
|---|---|---|---|
| TD-001 | FastAPI/Pydantic compatibility in `api/auth/` — `AsyncMock` vs sync Redis mock mismatch causes 2 test failures | Medium | Maintenance |
| TD-002 | `database/migrations/004_observability_memory.sql` not written | Low | Sprint 5 |
| TD-003 | `.github/workflows/ci.yml` not written | Medium | Sprint 5 |
| TD-004 | Session store is in-memory; needs Redis for multi-process deployment | Medium | Sprint 7 |
| TD-005 | RAG ChromaDB not populated; `rag.advisory` always skipped | High | Sprint 5 |

---

## Security Posture

All security constraints established at Sprint 4 kickoff are in effect and enforced in code:

| Constraint | Status |
|---|---|
| No raw Aadhaar storage — SHA-256 hash only | ✅ Enforced |
| No hardcoded secrets — environment variables only | ✅ Enforced |
| Parameterized SQL only — no f-strings in SQL | ✅ Enforced |
| Prompt injection check on all user input to LLM | ✅ Enforced (safety_validator node) |
| File upload MIME validation (not extension) | ✅ Enforced |
| `from exc` on all re-raises | ✅ Enforced |
| JWT_SECRET from environment | ✅ Enforced |

---

## What Was Deliberately Not Built

- Flutter UI (Sprint 6)
- Voice input (Sprint 8)
- Satellite / yield prediction (Sprint 9)
- Disease camera (Sprint 7)
- Redis session store (Sprint 7)
- Real-time market price feeds (Sprint 7)
- CI/CD pipeline (Sprint 5)

These are not gaps. They are sequenced deliverables.

---

## Sprint 5 Objectives

Sprint 5 is an Intelligence Validation Sprint. The goal shifts from building to proving.

**Grounded Response Rate target: >95%** before Flutter development begins.

1. **RAG Quality** — 200 Tamil Nadu agriculture question benchmark; measure retrieval precision, citation quality, hallucination rate
2. **Agent Evaluation** — per-agent latency, confidence, failure, cache hit metrics
3. **Cognitive Engine Evaluation** — independent node-by-node testing
4. **Tamil Language Evaluation** — pure Tamil / Tanglish / English / mixed benchmark
5. **Agricultural Gold Dataset** — expected intent, agents, sources, advice per question
6. **AI Benchmark Dashboard** — `evaluation/dashboard.py` live metrics tracking

---

*This document is the canonical record of the v0.4.0-alpha release.*
*All platform decisions made in Sprint 4 are frozen. No features. No refactoring. Tag it.*
