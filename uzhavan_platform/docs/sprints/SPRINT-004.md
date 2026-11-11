# Sprint 4 (Revised)

**Goal:** Build the AI intelligence layer. Deliver a working end-to-end query: farmer asks a question, system returns a grounded Tamil answer with citations.
**Duration:** 2 weeks
**Engineering Directive:** ED-001 Active
**Documentation Freeze:** Active until Sprint 6. No new docs unless required by a release gate.

---

## Feature Packs

| FP | Name | Status | Version |
|----|------|--------|---------|
| FP-001 | Farmer Authentication | ✅ DONE | V0.2 |
| FP-002 | AI Orchestrator & Conversation Platform | 🔓 IN PROGRESS | V0.3 |
| FP-003 | Weather Intelligence | ⏳ QUEUED | V0.4 |

> FP-003 planning begins only when FP-002 reaches Integration Testing.

---

## FP-002 Gate Status

| Gate | Agent | Status |
|------|-------|--------|
| Planning | Planning Agent | ✅ Approved 2026-07-01 |
| Architecture | Architecture Agent | ✅ Approved 2026-07-01 |
| Product Quality | Product Quality Agent | 🔄 Active |
| Backend | Backend Agent | 🔓 UNLOCKED |
| AI | AI Agent | 🔓 UNLOCKED |
| Tests | Testing Agent | 🔒 After Phase E |
| Security | Security Agent | 🔒 After Phase E |
| Performance | DevOps Agent | 🔒 After Phase E |
| Documentation | Documentation Agent | 🔒 Frozen until Sprint 6 |
| Standards | Standards Agent | 🔒 After Phase E |
| Flutter | Flutter Agent | 🔒 After Integration Sprint |
| **MERGE** | **Master Agent** | 🔒 Locked |

---

## Implementation Phases

### Phase B — Shared Models ✅ COMPLETE
Executed 2026-07-01.

- ✅ `backend/shared/models/` — 13 files (citation, farmer, weather, market, disease, crop, tool, response, memory, message, decision, context, conversation)
- ✅ `backend/shared/agents/base.py` — BaseDomainAgent interface (manifest, can_handle, execute, validate, health, describe_tools, _timed_result)
- ✅ `backend/shared/exceptions.py` — 9 typed exceptions (UzhavanError → RAGError, WeatherError, VerificationError, SafetyError, ToolNotFoundError, AgentError, SessionError, AuthError, RateLimitError)
- ✅ `backend/feature_flags.py` — FeatureFlags class, flags singleton, enabled_agents()
- ✅ All 41 imports verified: `python3.12 -c "from backend.shared.models import ..."` → OK

**Universal AI Contract is live. Every future agent, graph node, and layer speaks this language.**

---

### Phase A — Foundation Cleanup ✅ COMPLETE
Executed 2026-07-01.

- ✅ `JWT_SECRET` + `ENV` + all feature flags added to `.env.example`
- ✅ Duplicate docs removed: `docs/ROADMAP.md`, `docs/SPRINT.md`, `docs/UX/Farmer Journey.md`
- ✅ `STANDARDS.md` updated: all `api/` references → `backend/` three-layer layout; commit scopes updated; test mirror paths updated
- ✅ Layer boundary rules documented in STANDARDS.md

**Documentation frozen. No new docs until Sprint 6.**

---

### Phase B — Shared Models
**Owner:** Backend Agent
**Deliverable:** `backend/shared/` — every other module depends on this; build it first.

```
backend/shared/
├── models.py
└── exceptions.py
```

**models.py must define:**

```python
# Core state
class ConversationState(TypedDict)       # full pipeline state
class Message(TypedDict)                 # user/assistant message
class FarmerContext(TypedDict)           # farmer_id, farm_id, district, crop, area_ha, language
class WeatherContext(TypedDict)          # district, temp_c, humidity_pct, rain_mm_today, rain_mm_forecast, description

# Tool execution
class ToolCall(TypedDict)                # tool_name, input, timestamp
class ToolResult(TypedDict)              # tool_name, output, duration_ms, error

# Knowledge output
class Citation(TypedDict)               # source, title, excerpt, page, confidence
class SourceCitation(BaseModel)          # Pydantic — serializable to SSE JSON

# Decision
class Decision(TypedDict)               # intent, tools_selected, planning_rationale

# Memory
class ConversationMemory(TypedDict)      # last_n_messages, relevant_past_advice

# Final output
class ResponseObject(BaseModel)         # answer, language, intent, confidence, sources, tools_used,
                                        # recommendations, warnings, next_questions

# Tool contract
class ToolDefinition(dataclass)         # name, description, version, permissions, timeout_s,
                                        # retry, input_schema, output_schema, mcp_compatible, enabled
```

**exceptions.py must define:**
- `UzhavanError(Exception)` — base
- `RAGError(UzhavanError)` — retrieval failures
- `WeatherError(UzhavanError)` — Open-Meteo failures
- `VerificationError(UzhavanError)` — hallucination guard trigger
- `ToolNotFoundError(UzhavanError)` — registry miss
- `AgentError(UzhavanError)` — domain agent failures

**Also create:**
- `backend/feature_flags.py` — 8 flags read from env, with boolean defaults

**Depends on:** Nothing. Start here.

---

### Phase C — Tool Registry + Domain Agents
**Owner:** AI Agent
**Deliverable:** `backend/tools/` — the bridge between Decision Layer and Knowledge Layer.

#### Tool Registry

```python
# backend/tools/registry.py
class ToolRegistry:
    def register(tool: ToolDefinition, handler: Callable) -> None
    def get(name: str) -> tuple[ToolDefinition, Callable]
    def list_enabled() -> list[ToolDefinition]
    def as_mcp_manifest() -> dict                    # ENABLE_MCP gate
```

#### Domain Agent Pattern

Each domain is a mini-agent: a class with multiple callable tools, all returning structured data. LangGraph calls domain agents — it never calls HTTP services directly.

```python
# backend/tools/weather_agent.py
class WeatherAgent:
    async def get_current_weather(district: str) -> WeatherContext
    async def get_forecast(district: str, days: int) -> list[WeatherContext]
    async def irrigation_advice(weather: WeatherContext, crop: str) -> str

# backend/tools/disease_agent.py
class DiseaseAgent:
    async def predict(image_path: str) -> DiseaseResult
    async def treatment(disease_label: str, crop: str) -> TNAUGuidance
    async def severity(confidence: float) -> Literal["low", "medium", "high"]

# backend/tools/market_agent.py  (ENABLE_MARKET=false → stub)
class MarketAgent:
    async def today_prices(crop: str, district: str) -> MarketPrice
    async def trend(crop: str, days: int) -> PriceTrend
    async def recommendation(prices: MarketPrice, trend: PriceTrend) -> str

# backend/tools/rag_agent.py
class RAGAgent:
    async def retrieve(query: str, filters: dict) -> list[Citation]
    async def retrieve_for_farmer(query: str, farmer: FarmerContext) -> list[Citation]

# backend/tools/scheme_agent.py
class SchemeAgent:
    async def list_applicable(crop: str, district: str, area_ha: float) -> list[Scheme]
    async def get_details(scheme_id: str) -> SchemeDetails

# backend/tools/memory_agent.py
class MemoryAgent:
    async def recall(farmer_id: str, intent: str) -> ConversationMemory
    async def save(farmer_id: str, question: str, intent: str, advice: str) -> None
```

Register all agents in the ToolRegistry at startup.

**Depends on:** Phase B (shared models)

---

### Phase D — Knowledge Layer
**Owner:** AI Agent + RAG Agent
**Deliverable:** `backend/knowledge/` — all data retrieval. No LLM calls in this layer.

```
backend/knowledge/
├── rag/
│   └── engine.py           # ChromaDB query, score threshold ≥0.35, returns list[Citation]
├── weather/
│   └── open_meteo.py       # Open-Meteo HTTP, district → lat/lon lookup, returns WeatherContext
├── disease/
│   └── client.py           # HTTP client to disease service (port 8001), returns DiseaseResult
├── market/
│   └── agmarknet.py        # Stub — raises ToolNotFoundError if ENABLE_MARKET=false
├── satellite/
│   └── sickle.py           # Stub — raises ToolNotFoundError if ENABLE_SATELLITE=false
└── memory/
    └── farmer_memory.py    # PostgreSQL ai_memory read/write
```

**RAG Engine non-negotiables:**
- If 0 chunks returned → return empty list, NEVER call LLM
- Score threshold: 0.35 minimum (configurable via env RAG_SCORE_THRESHOLD)
- Return `list[Citation]` with title, excerpt, page, confidence per chunk
- Tamil queries work via bge-m3 semantic matching — no translation needed

**Weather Engine:**
- District → PostGIS coordinates lookup from DB `districts` table
- Open-Meteo free tier: current + 7-day forecast
- Returns `WeatherContext` with irrigation_needed boolean

**Depends on:** Phase B (shared models), Migration 004 (ai_memory table)

---

### Phase E — Decision Layer (LangGraph) ⭐ The Core
**Owner:** AI Agent
**Deliverable:** `backend/decision/` — the intelligence layer. This IS UZHAVAN AI.

#### Pipeline (11 nodes)

```
User Message
      │
      ▼
 Intent Router          Classify: advisory | weather | disease | market | scheme | crop | off_topic
      │                 Extract entities: crop, district, quantity, date → extracted_entities
      ▼
   Planner              Emits list[CapabilityRequest] — e.g. "weather.forecast", "rag.advisory"
      │                 Never names agents directly. Requests capabilities.
      ▼
Capability Resolver     Reads AgentManifest from every registered agent
      │                 Matches CapabilityRequests → ResolvedCapability (agent + method + version)
      │                 Respects feature flags: skips disabled agents gracefully
      │                 Output: list[ResolvedCapability]
      ▼
 Parallel Domain        asyncio.gather() — calls each resolved agent.execute()
    Agents              Every agent returns ToolResult (tool, success, data, citations, confidence)
      │                 Never fails pipeline — ToolResult.success=False is handled gracefully
      ▼
Evidence Fusion         Merges all ToolResults:
   Engine               - Deduplicates citations by excerpt similarity
      │                 - Ranks by confidence score (desc)
      │                 - Resolves conflicts (e.g., two weather sources disagree)
      │                 - Computes overall_confidence from weighted mean
      │                 - Populates context.knowledge (KnowledgeContext)
      ▼
Grounding Validator     5 checks — any failure → Tamil fallback, LLM NOT called
      │                 1. citation_check: ≥1 citation with confidence ≥0.35
      │                 2. rag_check: ≥1 chunk if intent requires TNAU knowledge
      │                 3. weather_check: WeatherContext not empty if weather was requested
      │                 4. confidence_check: overall_confidence ≥0.30
      │                 5. context_check: KnowledgeContext has at least one data source
      ▼
Answer Generator        Load backend/prompts/{intent}.md via PromptBuilder
      │                 Build full prompt: system + farmer_profile + knowledge + question
      │                 Call LLM (Qwen3/Ollama primary, claude-sonnet-4-6 fallback)
      │                 Stream tokens as DeltaEvents
      ▼
Safety Validator        Post-generation checks (distinct from grounding — different responsibility):
      │                 1. Language check: Tamil response contains <5% English words
      │                 2. Tamil terminology: crop names use TNAU standard names
      │                 3. No banned outputs: no Aadhaar numbers, no phone numbers
      │                 4. Formatting: answer ends with actionable recommendation
      │                 Any failure → append warning to ResponseObject.warnings
      ▼
  Formatter             Assemble final ResponseObject:
      │                 answer, language, intent, confidence, sources (list[SourceCitation]),
      │                 tools_used, recommendations, warnings, next_questions (3 Tamil suggestions)
      ▼
   Response             Return ResponseObject to Conversation Layer → SSE stream
```

#### Files to create (in dependency order):

1. `backend/decision/prompt_builder.py` — loads `backend/prompts/{intent}.md`, no strings in Python
2. `backend/decision/observability.py` — writes per-request trace to `request_traces`
3. `backend/prompts/system.md` — base system prompt (Tamil-first, TNAU-grounded, no hallucination)
4. `backend/prompts/advisory.md`, `weather.md`, `disease.md`, `crop.md`, `scheme.md`, `off_topic.md`
5. `backend/decision/graph/__init__.py`
6. `backend/decision/graph/intent.py` — IntentGraph: classify + entity extraction
7. `backend/decision/graph/planner.py` — PlannerGraph: emit list[CapabilityRequest]
8. `backend/decision/graph/capability_resolver.py` — reads manifests → list[ResolvedCapability]
9. `backend/decision/graph/tools.py` — ToolExecutionGraph: asyncio.gather agent calls
10. `backend/decision/graph/evidence_fusion.py` — EvidenceFusionEngine: merge/rank/deduplicate
11. `backend/decision/graph/grounding_validator.py` — 5 checks + Tamil fallback constant
12. `backend/decision/graph/answer_generator.py` — LLM call with PromptBuilder
13. `backend/decision/graph/safety_validator.py` — language, terminology, format checks
14. `backend/decision/graph/formatter.py` — build ResponseObject
15. `backend/decision/graph/conversation.py` — root graph, composes all 11 nodes

**Tamil fallback message (hardcoded, shown when grounding fails):**
```
"மன்னிக்கவும். இந்த கேள்விக்கு தேவையான தகவல்கள் என்னிடம் இல்லை.
 TNAU உதவி மையத்தை தொடர்பு கொள்ளவும்: 0431-2371622"
```

**Depends on:** Phase B, Phase C, Phase D

---

### Phase F — Conversation Layer
**Owner:** Backend Agent
**Deliverable:** `backend/conversation/` — HTTP and SSE interface to the Decision Layer.

```
backend/conversation/
├── main.py         POST /chat (SSE), GET /chat/history, GET /chat/session/{id}, GET /health
├── session.py      Session CRUD, message persistence to chat_sessions + chat_messages
├── streaming.py    SSE event writer
└── rate_limit.py   Redis chat_rate:{farmer_id} — 20 requests/hour
```

**SSE event sequence (per request):**
```
event: delta      {"text": "..."} (streaming LLM tokens)
event: sources    [{"title": "...", "confidence": 0.87, "excerpt": "..."}]
event: meta       {"intent": "advisory", "confidence": 0.85, "tools_used": ["rag", "weather"]}
event: suggestions ["அடுத்து என்ன செய்ய வேண்டும்?", "மழை வருமா?", "யூரியா போட வேண்டுமா?"]
event: done       {}
```

**JWT validation:** Extract `farmer_id`, `farm_id` from token on every request. Reject 401 if invalid.

**Depends on:** Phases B, C, D, E all complete.

---

## Integration Test (Sprint 4 DoD)

After Phase F, before any other gate, run this scenario manually:

**Query:**
> "நான் தஞ்சாவூரில் சம்பா நெல் பயிர் செய்கிறேன். நாளை மழை வரலாம். இன்று யூரியா போட வேண்டுமா?"
> "I'm a farmer from Thanjavur growing Samba paddy. It may rain tomorrow. Should I apply urea today?"

**Expected system behavior:**
1. Intent Router → `advisory` + entities: crop=paddy, district=Thanjavur, topic=fertilizer
2. Planner → selects: WeatherAgent.get_forecast + RAGAgent.retrieve_for_farmer
3. Tool Executor → parallel: weather forecast (Thanjavur, 2 days) + TNAU retrieval ("நெல் யூரியா பயன்பாடு மழை")
4. Evidence Collector → weather context + ≥2 TNAU citations (score ≥0.35)
5. Grounding Validator → all 5 checks pass
6. Answer Generator → Tamil response with specific advice
7. Response includes: confidence score, ≥2 source citations, ≥1 recommendation, ≥3 next questions

**Pass criteria:**
- Response is in Tamil
- Response mentions rain timing specifically (not generic)
- Response gives actionable advice (wait / reduce quantity / delay)
- ≥2 TNAU citations with excerpt visible
- Latency ≤ 8 seconds
- No English text in Tamil response body

**When this test passes: UZHAVAN AI exists. Flutter is a presentation layer over a working intelligence engine.**

---

## Sprint 5 (Next — Integration Testing)

Sprint 5 is an integration testing sprint, NOT a Flutter sprint.

By end of Sprint 5:
- 10 farmer scenarios tested end-to-end
- VerificationGraph tested with adversarial inputs (unknown crops, off-topic questions)
- E2E latency benchmarks for all 5 intent types
- Load test: 50 concurrent requests, mean ≤ 8s, p95 ≤ 15s
- Security audit: prompt injection attempts, session isolation

Flutter begins in Sprint 6 — only after the intelligence engine is proven.

---

## Definition of Done (FP-002)

- [ ] Migration 004 applied — `request_traces` + `ai_memory` tables exist
- [ ] All Phase B–F files created
- [ ] Grounding Validator tested: 0-chunk scenario → Tamil fallback (LLM never called)
- [ ] Integration test scenario passes (Thanjavur paddy urea query)
- [ ] POST /chat SSE returns all 5 event types
- [ ] ChromaDB populated with ≥500 TNAU chunks
- [ ] All 18 FP-002 ACs verified
- [ ] Product Quality Agent Murugan walkthrough passed
- [ ] Standards Gate passed (layer boundary compliance)
- [ ] Security Gate passed (prompt injection audit)
- [ ] Coverage ≥80% on `backend/decision/`
- [ ] CI pipeline green
- [ ] Tagged `v0.3-rc1`
