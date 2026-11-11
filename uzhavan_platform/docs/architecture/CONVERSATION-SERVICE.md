# UZHAVAN AI — Conversation Service Architecture

**Version:** 2.0
**Status:** ✅ Architecture Gate Approved
**Author:** Architecture Agent
**Date:** 2026-07-01
**Changes from v1.0:** Three-layer architecture (ADR-008); updated folder structure; Product Quality Agent added to release gates.

> This document is the source of truth for the AI Orchestrator & Conversation Platform (FP-002).
> All implementation must conform to this spec. Any deviation requires an ADR.

---

## 1. System Context

```
┌──────────────────────────────────────────────────────────────┐
│  Farmer Interfaces                                           │
│                                                              │
│   [Flutter App]  [WhatsApp]  [Voice]  [Web]  [Gov Portal]   │
│        │              │         │       │          │         │
└────────┼──────────────┼─────────┼───────┼──────────┼────────┘
         │              │         │       │          │
         └──────────────┴─────────┴───────┴──────────┘
                                  │
                          ┌───────▼────────┐
                          │  API Gateway   │
                          │  (future)      │
                          └───────┬────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   Conversation Service      │
                    │   backend/advisory/         │
                    │   FastAPI + LangGraph       │
                    └─────────────┬──────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
   ┌──────▼──────┐        ┌───────▼──────┐        ┌──────▼──────┐
   │  Tool       │        │  ChromaDB    │        │  PostgreSQL  │
   │  Registry   │        │  (RAG store) │        │  + Redis     │
   └──────┬──────┘        └──────────────┘        └─────────────┘
          │
   ┌──────┼──────────────────────────────────────┐
   │      │                                      │
   ▼      ▼        ▼          ▼         ▼        ▼
Weather Disease  Schemes   Market   Satellite  Memory
 Tool    Tool    Tool       Tool     Tool      Tool
   │
Open-Meteo
```

V0.3 active: Conversation Service, ChromaDB, PostgreSQL, Redis, WeatherTool, DiseaseTool, SchemesTool.
V0.3 registered but disabled: MarketTool (ENABLE_MARKET=True but no data source yet), SatelliteTool (ENABLE_SATELLITE=False), MemoryTool reasoning (ENABLE_MEMORY=True for writes; reasoning is Phase 2).

---

## 2. Request Lifecycle

```
Farmer sends message
        │
        ▼
POST /chat (FastAPI)
  - Validate JWT → extract farmer_id
  - Validate body (message, language)
  - Generate trace_id
  - Emit SSE response stream (open connection)
        │
        ▼
ConversationGraph.invoke(initial_state)
        │
        ├─[Node 1]── IntentGraph
        │              ├── classify_intent     (LLM mini-call or rule-based)
        │              └── extract_entities    (NER: crop, district, season, pest)
        │                    └── Updates: state.intent, state.entities
        │
        ├─[Node 2]── PlanningGraph
        │              └── select_tools        (reads ToolRegistry.list_enabled())
        │                    └── Updates: state.tools_planned
        │
        ├─[Node 3]── ToolExecutionGraph
        │              └── event_dispatch      (EventBus.publish per tool)
        │                    ├── RAGTool ──────────► rag_chunks
        │                    ├── WeatherTool ────────► weather
        │                    ├── DiseaseTool ─────────► disease
        │                    └── SchemesTool ─────────► schemes
        │                    All run in parallel (asyncio.gather)
        │                    └── Updates: state.tool_results, state.rag_chunks
        │
        ├─[Pure Fn]── ContextBuilder.build(state)
        │              └── Returns: ContextDict (merged, structured)
        │
        ├─[Node 4]── VerificationGraph
        │              ├── check_citations     → fallback if no sources
        │              ├── check_rag           → fallback if no chunks + advisory intent
        │              └── check_confidence    → warning if all scores < 0.35
        │                    ├── [PASS] → continue to PromptBuilder
        │                    └── [FAIL] → fallback_node → Tamil message → END
        │
        ├─[Pure Fn]── PromptBuilder.build(intent, context, language)
        │              └── Loads prompts/{intent}.md; fills template
        │
        ├─[Node 5]── LLM Node
        │              └── qwen3_stream / claude_stream
        │                    Streams tokens → SSE: {"type": "delta", "content": "..."}
        │
        ├─[Node 6]── ResponseGraph
        │              ├── structure_response  → builds ResponseObject
        │              │     Emits SSE: {"type": "sources", "sources": [...]}
        │              │     Emits SSE: {"type": "meta", "intent": ..., "tools_used": ...}
        │              └── suggest_questions   → 3 follow-ups
        │                    Emits SSE: {"type": "suggestions", "next_questions": [...]}
        │                    Emits SSE: {"type": "done", "session_id": ..., "trace_id": ...}
        │
        └─[Post-graph]── ObservabilityLogger
                           ├── write request_traces (async, non-blocking)
                           └── write ai_memory (async, non-blocking, if meaningful intent)
```

---

## 3. Data Models

### ConversationState (LangGraph state object)
```
Field               Type                    Set By
─────────────────────────────────────────────────────────────
# Request identity
session_id          str                     main.py (new or from request)
trace_id            str (uuid4)             main.py at request start
user_id             str                     JWT sub
farmer_id           str                     JWT sub (same as user_id in V0.3)
farm_id             str | None              request body

# Input
message             str                     request body
language            str                     request body ("Tamil"/"English")

# Intent
intent              str | None              IntentGraph
entities            dict                    IntentGraph
  crop:             str | None
  district:         str | None
  season:           str | None
  pest:             str | None

# Tool execution
tools_planned       list[str]               PlanningGraph
tool_results        dict[str, Any]          ToolExecutionGraph
  rag_chunks:       list[RetrievedChunk]
  weather:          dict | None
  disease:          dict | None
  schemes:          list | None
  market:           dict | None             (when ENABLE_MARKET active)

# Context aggregation
context             ContextDict | None      ContextBuilder

# Verification
verification_passed bool                    VerificationGraph
fallback_reason     str | None              VerificationGraph
warnings            list[str]               VerificationGraph

# Response
sources             list[SourceCitation]    ResponseGraph
confidence          float                   ResponseGraph
final_response      ResponseObject | None   ResponseGraph

# Timing (for observability)
timing              dict[str, int]          various nodes (ms)
  started_at:       float                   main.py
  intent_ms:        int                     IntentGraph
  planning_ms:      int                     PlanningGraph
  embedding_ms:     int                     ToolExecutionGraph (RAGTool)
  retrieval_ms:     int                     ToolExecutionGraph (RAGTool)
  tool_ms:          int                     ToolExecutionGraph (total)
  llm_ms:           int                     LLM Node
```

### SourceCitation
```
title:        str      ← "TNAU Plant Protection Manual"
page:         int | None
url:          str      ← canonical TNAU URL
confidence:   float    ← cosine similarity 0.0–1.0
excerpt:      str      ← 1–2 sentence quote
category:     str      ← "Plant Protection" | "Crop Management" | etc.
```

### ResponseObject
```
answer:          str
language:        str    ← "ta" | "en"
intent:          str
confidence:      float  ← mean(source.confidence)
sources:         list[SourceCitation]
tools_used:      list[str]
recommendations: list[str]
warnings:        list[str]
next_questions:  list[str]    ← 3 follow-up suggestions
```

### ToolDefinition
```
name:            str
display_name:    str
description:     str   ← used by PlanningGraph for selection
version:         str   ← semver
permissions:     list[str]
timeout_s:       int
retry:           int
input_schema:    dict  ← JSON Schema
output_schema:   dict  ← JSON Schema
mcp_compatible:  bool
enabled:         bool  ← reads feature_flags at registration time
```

---

## 4. Folder Structure (Three-Layer Architecture — ADR-008)

```
backend/
│
├── conversation/                ← Conversation Layer (HTTP, SSE, sessions)
│   ├── main.py                  ← FastAPI: /chat, /chat/history, /chat/session/{id}
│   ├── session.py               ← session CRUD, history queries
│   ├── streaming.py             ← SSE event writer
│   ├── rate_limit.py            ← Redis rate limiter
│   └── requirements.txt
│
├── decision/                    ← Decision Layer (LangGraph, intent, planning)
│   ├── graph/
│   │   ├── __init__.py          ← exports ConversationGraph
│   │   ├── conversation.py      ← root graph: wires all subgraphs
│   │   ├── intent.py            ← IntentGraph
│   │   ├── planner.py           ← PlanningGraph
│   │   ├── tools.py             ← ToolExecutionGraph (EventBus dispatch)
│   │   ├── verification.py      ← VerificationGraph
│   │   └── response.py          ← ResponseGraph
│   ├── state.py                 ← ConversationState dataclass
│   ├── context_builder.py       ← ContextBuilder
│   ├── prompt_builder.py        ← PromptBuilder
│   └── observability.py         ← ObservabilityLogger
│
├── knowledge/                   ← Knowledge Layer (all data sources)
│   ├── rag/
│   │   └── engine.py            ← ChromaDB retrieval (was rag_engine.py)
│   ├── weather/
│   │   └── open_meteo.py        ← Open-Meteo client
│   ├── disease/
│   │   └── client.py            ← calls disease service on port 8001
│   ├── market/
│   │   └── agmarknet.py         ← stub (ENABLE_MARKET=True)
│   ├── satellite/
│   │   └── sickle.py            ← stub (ENABLE_SATELLITE=False)
│   └── memory/
│       └── farmer_memory.py     ← ai_memory read/write
│
├── tools/                       ← Tool Registry (bridges Decision → Knowledge)
│   ├── registry.py              ← ToolRegistry class
│   ├── rag_tool.py
│   ├── weather_tool.py
│   ├── disease_tool.py
│   ├── market_tool.py           ← ENABLE_MARKET
│   ├── satellite_tool.py        ← ENABLE_SATELLITE
│   └── memory_tool.py           ← ENABLE_MEMORY
│
├── prompts/                     ← Prompt templates (no strings in Python)
│   ├── system.md
│   ├── advisory.md
│   ├── weather.md
│   ├── disease.md
│   ├── market.md
│   ├── crop.md
│   └── scheme.md
│
├── shared/                      ← Shared models (no logic — data classes only)
│   ├── models.py                ← ConversationState, ResponseObject, SourceCitation, ToolDefinition
│   └── exceptions.py
│
├── auth/                        ← FP-001 (unchanged)
└── feature_flags.py             ← Read by all layers; env-var override
```

### Layer Boundary Rules (enforced by Standards Agent)

| From ↓ / To → | Conversation | Decision | Knowledge | Tools | Shared |
|----------------|-------------|----------|-----------|-------|--------|
| Conversation | — | ✅ calls | ❌ never | ❌ never | ✅ imports |
| Decision | ❌ never | — | ❌ never | ✅ calls | ✅ imports |
| Knowledge | ❌ never | ❌ never | — | ❌ never | ✅ imports |
| Tools | ❌ never | ❌ never | ✅ calls | — | ✅ imports |

Any PR that crosses a ❌ boundary must be rejected by Standards Agent.

---

## 5. Feature Flags

```
Flag                Default  Description
────────────────────────────────────────────────────────
ENABLE_WEATHER      True     Open-Meteo WeatherTool
ENABLE_DISEASE      True     Disease detection via disease service
ENABLE_SCHEMES      True     Government schemes RAG
ENABLE_MARKET       True     MarketTool registered; AGMARKNET not yet integrated
ENABLE_SATELLITE    False    Phase 3
ENABLE_MEMORY       True     ai_memory writes; Agent reasoning = Phase 2
ENABLE_MCP          False    Expose Tool Registry as MCP server (Phase 4)
ENABLE_STREAMING    True     SSE streaming; False returns full JSON (for testing)
```

---

## 6. Event Bus

V0.3 implementation: in-process asyncio. Interface identical to a message-broker version.

```
EventBus
  .publish(ToolRequestEvent)     → puts event in asyncio.Queue per tool
  .subscribe(tool_name, handler) → registers handler callable
  .wait_all(timeout_s)           → asyncio.gather all subscribed tools; returns list[ToolResultEvent]

ToolRequestEvent:  event_id, tool_name, payload, trace_id
ToolResultEvent:   event_id, tool_name, result|None, error|None, duration_ms
```

Future migration: swap asyncio.Queue for Redis Pub/Sub or RabbitMQ — zero graph changes.

---

## 7. Observability Schema

```sql
-- in 004_observability_memory.sql

CREATE TABLE request_traces (
    trace_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id       UUID REFERENCES chat_sessions(session_id),
    farmer_id        UUID REFERENCES farmers(farmer_id),
    intent           VARCHAR(50),
    tools_used       TEXT[],
    embedding_ms     INTEGER,
    retrieval_ms     INTEGER,
    tool_ms          INTEGER,
    llm_ms           INTEGER,
    total_ms         INTEGER,
    llm_provider     VARCHAR(20),
    chunks_retrieved INTEGER,
    confidence       NUMERIC(4,3),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE ai_memory (
    memory_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farmer_id        UUID NOT NULL REFERENCES farmers(farmer_id),
    session_id       UUID REFERENCES chat_sessions(session_id),
    question         TEXT NOT NULL,
    intent           VARCHAR(50),
    crop             VARCHAR(100),
    district         VARCHAR(100),
    weather_summary  TEXT,
    advice           TEXT NOT NULL,
    outcome          VARCHAR(50),      -- "applied" | "ignored" | "unknown"
    confidence       NUMERIC(4,3),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 8. MCP Compatibility Surface

The ToolRegistry exposes `as_mcp_manifest() → dict` which returns a valid MCP tool list:

```json
{
  "tools": [
    {
      "name": "rag",
      "description": "Retrieve TNAU agricultural knowledge for a crop question",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query":    { "type": "string" },
          "language": { "type": "string", "enum": ["Tamil", "English"] },
          "district": { "type": "string" }
        },
        "required": ["query"]
      }
    },
    {
      "name": "weather",
      "description": "Get weather forecast and irrigation advice for a Tamil Nadu district",
      "inputSchema": {
        "type": "object",
        "properties": {
          "district": { "type": "string" }
        },
        "required": ["district"]
      }
    }
  ]
}
```

When `ENABLE_MCP=True` (Phase 4), the service also exposes `GET /mcp/manifest` returning this JSON, making it consumable by any MCP-compatible AI system.

---

## 9. Performance Budget

| Phase | Budget | Notes |
|-------|--------|-------|
| JWT validation | ≤ 5 ms | Synchronous |
| Intent classification | ≤ 200 ms | Rule-based in V0.3; LLM mini-call if needed |
| bge-m3 embedding | ≤ 150 ms | Query embedding only |
| ChromaDB retrieval | ≤ 350 ms | Top-6 chunks, cosine, score filter |
| Parallel tool execution | ≤ 500 ms | All tools in parallel |
| ContextBuilder | ≤ 50 ms | Pure Python |
| VerificationGraph | ≤ 20 ms | Pure Python checks |
| PromptBuilder | ≤ 10 ms | File read + string substitution |
| Time to first token (Qwen3) | ≤ 2000 ms | Ollama local |
| Total streaming (typical) | ≤ 7000 ms | Target ≤ 8000 ms |
| Observability writes | ≤ 20 ms | Non-blocking; after response sent |

---

## 10. Security Checklist (Architecture Layer)

- [ ] JWT secret never logged, never in tool results
- [ ] Prompt templates in .md files — no secret injection possible via file read
- [ ] Tool results treated as untrusted — never embedded raw in system prompt
- [ ] ConversationState never serialized to logs (contains farmer_id, message)
- [ ] trace_id is opaque UUID — no server internals exposed
- [ ] Session queries always scoped to farmer_id from JWT
- [ ] SSE Content-Type: text/event-stream; X-Accel-Buffering: no
- [ ] Rate limit key: `chat_rate:{farmer_id}` — farmer_id from JWT, not from request body

---

## 11. Interfaces This Service Will Support (V0.3 → V1.0)

| Interface | V0.3 | V0.4 | V0.5+ |
|-----------|------|------|-------|
| Flutter chat | ✅ | ✅ | ✅ |
| Web dashboard | - | ✅ | ✅ |
| WhatsApp | - | - | ✅ |
| Voice | - | - | ✅ |
| Government portal | - | - | ✅ |
| Call centre | - | - | V1.0 |

The service contract (ConversationState, ResponseObject, SSE event schema) is stable from V0.3 and must not break across future interface additions.

---

## Document History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-07-01 | Initial — Architecture Gate revision from Planning Gate approval |
