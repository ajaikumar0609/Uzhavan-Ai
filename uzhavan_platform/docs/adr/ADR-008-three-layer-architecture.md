# ADR-008 — Three-Layer Conversation Architecture

**Status:** Approved
**Date:** 2026-07-01
**Deciders:** Architecture Agent, Master Agent
**Feature Pack:** FP-002 — AI Orchestrator & Conversation Platform

---

## Context

The initial FP-002 design placed all conversation logic in a single `backend/advisory/` service. While modular graphs (ADR-005) and a tool registry (ADR-006) addressed internal modularity, the service itself had no clear boundary between:

- HTTP concerns (receiving requests, streaming SSE, managing sessions)
- Orchestration concerns (intent, planning, tool selection, verification)
- Data concerns (RAG retrieval, weather, disease, market, memory)

This matters for one specific future requirement: voice, WhatsApp, and web integrations must use the same AI orchestration and the same knowledge sources — but with completely different transport layers. If HTTP, orchestration, and data are tangled in one service, every new interface requires forking or wrapping the entire service.

---

## Decision

**Split the Conversation Service into three independent layers.**

```
Conversation Layer          backend/conversation/
        ↓
Decision Layer              backend/decision/
        ↓
Knowledge Layer             backend/knowledge/
```

### Conversation Layer (`backend/conversation/`)

Responsibility: Everything the farmer sees and touches at the transport level.

- FastAPI application: `/chat`, `/chat/history`, `/chat/session/{id}`, `/health`
- SSE streaming: opening the stream, writing events, closing cleanly
- Session management: creating sessions, linking to farmer_id
- Rate limiting: Redis `chat_rate:{farmer_id}` counter
- JWT validation: extracting farmer_id, farm_id from token
- Request/response serialization

This layer knows nothing about LangGraph, tools, RAG, or weather. It knows how to receive a message and stream back events.

### Decision Layer (`backend/decision/`)

Responsibility: Everything that happens between receiving a message and knowing what to say.

- `graph/` — all LangGraph subgraphs (Intent, Planner, ToolExecution, Verification, Response)
- `state.py` — ConversationState
- `context_builder.py` — ContextBuilder
- `prompt_builder.py` — PromptBuilder
- `observability.py` — trace collection

This layer knows nothing about HTTP, SSE, or sessions. It receives a ConversationState object and returns an updated ConversationState object with `final_response` populated.

### Knowledge Layer (`backend/knowledge/`)

Responsibility: All data retrieval and external service integration.

```
backend/knowledge/
  rag/         ← ChromaDB retrieval (rag_engine.py → renamed/moved here)
  weather/     ← Open-Meteo integration
  disease/     ← Disease detection service client
  market/      ← AGMARKNET client (Phase 4+)
  satellite/   ← SICKLE models (Phase 3+)
  memory/      ← ai_memory read/write
```

This layer knows nothing about LangGraph, sessions, or HTTP. It provides a clean callable interface: `rag.retrieve(query, filters) → list[RetrievedChunk]`.

### Tool Registry (`backend/tools/`)

The ToolRegistry sits between Decision and Knowledge layers. It registers Knowledge layer callables as tools with metadata, and the Decision layer's PlanningGraph selects from it.

---

## Updated Folder Structure

```
backend/
├── conversation/            ← Conversation Layer
│   ├── main.py              ← FastAPI app: /chat, /chat/history, /health
│   ├── session.py           ← session CRUD, history queries
│   ├── streaming.py         ← SSE event writer
│   ├── rate_limit.py        ← Redis rate limiter (moved from auth)
│   └── requirements.txt
│
├── decision/                ← Decision Layer
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── conversation.py  ← root graph
│   │   ├── intent.py
│   │   ├── planner.py
│   │   ├── tools.py
│   │   ├── verification.py
│   │   └── response.py
│   ├── state.py
│   ├── context_builder.py
│   ├── prompt_builder.py
│   └── observability.py
│
├── knowledge/               ← Knowledge Layer
│   ├── rag/
│   │   ├── engine.py        ← was rag_engine.py
│   │   └── embed.py
│   ├── weather/
│   │   └── open_meteo.py
│   ├── disease/
│   │   └── client.py        ← calls disease service on port 8001
│   ├── market/
│   │   └── agmarknet.py     ← stub (ENABLE_MARKET flag)
│   ├── satellite/
│   │   └── sickle.py        ← stub (ENABLE_SATELLITE flag)
│   └── memory/
│       └── farmer_memory.py ← ai_memory read/write
│
├── tools/                   ← Tool Registry (bridges Decision → Knowledge)
│   ├── registry.py
│   ├── rag_tool.py
│   ├── weather_tool.py
│   ├── disease_tool.py
│   ├── market_tool.py
│   ├── satellite_tool.py
│   └── memory_tool.py
│
├── prompts/                 ← Prompt templates (no strings in Python)
│   ├── system.md
│   ├── advisory.md
│   ├── weather.md
│   ├── disease.md
│   ├── market.md
│   ├── crop.md
│   └── scheme.md
│
├── auth/                    ← Existing auth service (FP-001)
├── feature_flags.py         ← All layers read this
└── shared/                  ← Shared models (ConversationState, ResponseObject, etc.)
    ├── models.py
    └── exceptions.py
```

---

## How Future Interfaces Connect

This is the key benefit. When WhatsApp or voice is added:

```
WhatsApp Webhook (future)          Voice WebSocket (future)
        │                                  │
        ▼                                  ▼
  conversation/                     conversation/
  whatsapp.py                       voice.py
        │                                  │
        └──────────────┬────────────────────┘
                       │
                       ▼
               decision/ (unchanged)
                       │
                       ▼
               knowledge/ (unchanged)
```

The Decision Layer and Knowledge Layer do not change when a new interface is added. The new interface code handles transport concerns (WhatsApp message format, audio transcription) and then calls `ConversationGraph.invoke(state)` exactly as the HTTP layer does.

---

## Alternatives Considered

### Alternative A: Single service with internal modules
Keep everything in `backend/advisory/` with internal Python modules for separation.

**Rejected:** Import boundaries are not enforced. A developer can accidentally import `rag_engine.py` directly from a streaming handler. In 2 years, with 10 developers and 20+ files, the layers will be tangled. Hard boundaries (separate directories, separate Python packages) enforce the architecture.

### Alternative B: Three separate microservices with HTTP between layers
Each layer as its own Docker service with REST calls between them.

**Rejected for V0.3:** Adds latency (network hop per layer), complexity (service discovery, auth between internal services), and overhead that is not justified at current scale. The three-layer separation within a single process gives the same architectural benefits without the operational complexity. Migration to microservices is straightforward later if needed.

### Alternative C: Keep existing structure (single advisory service)
Do not split; keep `backend/advisory/` with modular graphs.

**Rejected:** The original structure makes every future interface (WhatsApp, voice, web) require duplicating or wrapping the FastAPI routing logic. Three layers is a small organizational cost now that pays off significantly at Sprint 5+.

---

## Consequences

### Positive
- New interface (WhatsApp, voice, web) connects at Conversation Layer only — Decision and Knowledge unchanged
- Each layer is independently testable: decision layer tests do not require a running FastAPI server
- Clear ownership: Flutter Agent works with Conversation Layer only; AI Agent works with Decision Layer only; RAG/Weather Agents work in Knowledge Layer
- Future microservice decomposition is straightforward along existing layer boundaries

### Negative
- Three directories instead of one — more navigation for simple changes
- `backend/shared/` models.py must be imported by all three layers — careful to avoid circular imports
- Requires updating import paths from old `advisory/` structure

### Mitigations
- `backend/shared/models.py` contains only data classes — no logic — so circular imports are impossible
- CONVERSATION-SERVICE.md and this ADR give developers a clear map of what belongs where
- Standards Agent to enforce layer boundary during code review

---

## Review

| Reviewer | Status |
|----------|--------|
| Architecture Agent | ✅ Approved |
| Master Agent | ✅ Approved |
