# UZHAVAN AI — Project Bible

**Version:** 1.0
**Date:** 2026-07-01
**Status:** Constitutional Document — immutable without Master Agent + Architecture Agent joint approval

> This is not documentation. This is the constitution.
> Every contributor — human or agent — reads this before touching the codebase.
> When in doubt about any decision, come back to this document.

---

## I. What Are We Building?

UZHAVAN AI is an AI operating system for Tamil Nadu farmers.

It is a platform that listens to a farmer's question in Tamil, reasons over official agricultural knowledge, real-time data, and the farmer's own history, and returns a specific, grounded, actionable recommendation — with the source cited, the confidence stated, and the next step clear.

It is not a chatbot.
It is not a search engine.
It is not a portal.

It is an intelligent agricultural advisor that happens to run on a ₹12,000 Android phone with intermittent internet.

**The elevator test:** If a Tamil Nadu farmer who has never used a smartphone before can ask "நாளைக்கு தண்ணீர் விடலாமா?" and get back a useful, trustworthy answer within 8 seconds — we are building the right thing.

---

## II. Why Are We Building It?

### The Problem

Tamil Nadu has 6 million farming households. The vast majority have no access to real-time, personalized agricultural guidance. An agronomist visit costs money and takes days. Government extension services are understaffed. Online resources are in English and require high literacy.

Farmers make decisions — when to irrigate, when to spray, what to plant — based on experience, neighbors, and guesswork. Wrong decisions cost yield and income. In a bad year, they cost the farm.

### The Opportunity

Tamil Nadu's farmers:
- Carry smartphones (low-end Android)
- Speak Tamil
- Are increasingly online via JioFi and mobile data
- Trust official government sources (TNAU, ICAR, state government)

The technology exists. The knowledge exists. The gap is delivery.

### Why Now

- bge-m3 makes Tamil-English semantic retrieval practical
- Qwen3 8B runs on commodity hardware with acceptable latency
- TNAU has digitized agricultural knowledge accessible for RAG
- LangGraph enables reliable tool-based orchestration
- Open-Meteo provides free, accurate district-level weather

UZHAVAN AI is the system that closes this gap.

---

## III. What Problems Do We Solve?

| Problem | Solution |
|---------|---------|
| Farmer doesn't know what disease is affecting their crop | Camera → MobileNetV2 disease detection → TNAU treatment in Tamil |
| Farmer doesn't know if it will rain before irrigating | Weather Tool → Open-Meteo → specific irrigation advice |
| Farmer gets contradictory advice from neighbors | RAG → grounded TNAU answer with source cited |
| Farmer misses government scheme eligibility | Schemes Tool → eligibility check → application guidance |
| Farmer makes decisions based on memory and habit | AI Memory → personalized advice based on their farm, crop, and history |
| Agronomist is unavailable in emergencies | 24/7 AI advisor, sub-8-second response |
| Advice is generic and not useful | Farmer profile + farm context → personalized recommendations |

---

## IV. Principles That Can Never Be Violated

These are constitutional. No feature, no sprint, no agent can override them.

### P-1: The AI Never Invents Agricultural Knowledge

The LLM is a reasoning and communication layer. It does not know agriculture. Every agricultural fact it communicates must come from:
- PostgreSQL (seed data: crops, pests, soil types, fertilizers)
- RAG (ChromaDB + TNAU knowledge chunks)
- API (Open-Meteo weather, AGMARKNET prices)
- ML model (MobileNetV2 disease detection, SICKLE satellite models)

If none of these sources have an answer, the LLM says so — in Tamil — and directs the farmer to their BAO or KVK. It does not guess.

**Violation example:** Generating a fertilizer dosage that is not in the TNAU database.
**Consequence of violation:** A farmer follows wrong advice. Crop fails. Trust lost permanently.

### P-2: The LLM Is a Reasoning Layer, Never a Database

The LLM does not store facts. It does not remember previous interactions on its own. It does not have opinions about crop varieties. Its only job is to:
1. Understand what the farmer asked
2. Synthesize the information retrieved by tools
3. Express it clearly in the farmer's language

### P-3: Every Recommendation Must Be Explainable

A farmer should always be able to ask "why?" and get a real answer. The system must be able to show its reasoning: what data it used, where that data came from, what it concluded.

### P-4: Every Recommendation Must State Confidence

No recommendation is presented without a confidence level. Low confidence triggers a warning — not an assertion. The farmer deserves to know when we are uncertain.

### P-5: Every Recommendation Must Cite Its Source

Every AI answer cites the source: TNAU URL, government circular, weather station, disease model version. Not a vague "according to research." A specific, verifiable source.

### P-6: Every Recommendation Should Be Personalized

Generic advice is not useful. "Apply 120 kg N/ha" is useless without knowing the farmer's soil type, irrigation source, district, and current season. UZHAVAN AI uses the farmer's profile and farm data to make advice specific to them.

### P-7: Every Recommendation Must Be Actionable

The test: after reading the recommendation, does the farmer know exactly what to do next?

❌ Wrong: "Rain is expected in the region."
✅ Right: "Rain expected tomorrow in Thanjavur (18 mm, 96% confidence). Do not irrigate today. Wait until Thursday. TNAU recommends 50 mm irrigation for paddy at tillering stage — schedule for Thursday morning if rain is below 15 mm."

---

## V. Technologies That Are Fixed

These cannot be changed without an ADR, Architecture Agent review, and Master Agent approval.

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Mobile | Flutter | Cross-platform, single codebase, Tamil rendering |
| Backend | FastAPI (Python) | Async, type-safe, auto-docs, team expertise |
| Orchestration | LangGraph | Stateful graph, conditional routing, tool use (ADR-001) |
| Local LLM | Qwen3 8B via Ollama | Offline capable, 8B quality, no API cost (ADR-002) |
| Cloud LLM fallback | Claude API (claude-sonnet-4-6) | Highest quality fallback when online |
| Vector store | ChromaDB | Local persistent, no server, cosine similarity (ADR-003) |
| Embeddings | BAAI/bge-m3 | Multilingual Tamil+English in same space (ADR-004) |
| Database | PostgreSQL 16 + PostGIS 3.4 | Geospatial, proven, extensions |
| Cache | Redis | OTP rate limiting, weather cache, chat rate limit |
| Disease model | MobileNetV2 (PlantVillage) | 38 classes, 14 crops, validated |
| Weather source | Open-Meteo | Free, accurate, no API key, district-level |
| Container | Docker + Docker Compose | Single-command local + production |

**The stack is frozen. Phase 3+ additions require an ADR. The bar is high.**

---

## VI. Architectural Decisions That Are Immutable

These are fixed for the life of the V1.0 product.

### A-1: Three-Layer Architecture

The AI Orchestrator is built in three independent layers:

```
Conversation Layer    — HTTP, SSE, session, history
        ↓
Decision Layer        — LangGraph, intent, planning, tool execution, verification
        ↓
Knowledge Layer       — RAG, weather, disease, market, satellite, farmer memory
```

No layer calls a layer above it. The Conversation Layer calls only the Decision Layer. The Decision Layer calls only the Knowledge Layer. This separation makes WhatsApp, voice, and web integrations trivially addable — they connect at the Conversation Layer only.

### A-2: Tool-Based Orchestration

The LLM never directly queries databases, APIs, or models. All data retrieval goes through registered tools. The LLM sees only the structured output of tools, assembled by the ContextBuilder.

### A-3: Dynamic Tool Registry

Tools are registered, not hardcoded. Adding a new tool requires: create file → register → add feature flag. Zero graph changes.

### A-4: Modular LangGraph

Seven independent subgraphs. Each testable in isolation. Adding or replacing one graph does not affect others.

### A-5: No Hallucination Guardrail

If the VerificationGraph finds zero sources above the confidence threshold (0.35), the system returns a Tamil fallback message. The LLM is never called with empty context.

### A-6: Feature Flags for Everything New

Every tool, every external integration, every AI capability begins as a feature flag defaulting to False. It is turned on only after the implementation passes all 10 release gates.

### A-7: Observability by Default

Every request generates a trace_id. Every phase writes its latency. Observability is not added later — it is part of the architecture from V0.3.

---

## VII. How Agents Interact

### The Agent Hierarchy

```
Master Agent
(never writes code — coordinates, reviews, delivers)
         │
         ├── Planning Agent       → produces ROADMAP, SPRINT, TODO
         ├── Product Agent        → farmer experience, Tamil journey
         ├── Product Quality Agent → rejects features that don't serve farmers
         ├── Architecture Agent   → API design, DB schema, ADRs
         │
         ├── Backend Agent        → FastAPI services
         ├── Flutter Agent        → mobile UI
         ├── Database Agent       → PostgreSQL migrations, seed data
         ├── AI Agent             → LangGraph graphs, state, context
         ├── RAG Agent            → embedding, chunking, retrieval
         ├── Vision Agent         → disease detection
         ├── Weather Agent        → Open-Meteo integration
         ├── Market Agent         → AGMARKNET integration
         ├── Satellite Agent      → SICKLE data (Phase 3)
         │
         ├── Testing Agent        → pytest, integration, E2E
         ├── Security Agent       → JWT, SQL, uploads, prompt injection
         ├── DevOps Agent         → Docker, CI/CD, performance
         ├── Documentation Agent  → all docs, READMEs, changelogs
         └── Standards Agent      → merge gate
```

### Interaction Rules

1. **Master Agent coordinates, never implements.** If Master Agent is writing code, something has gone wrong.
2. **Sub-agents work in sequence.** Backend Agent cannot start until Architecture Agent signs off. Flutter Agent cannot start until Backend Agent has a running endpoint.
3. **Every agent produces a deliverable.** The deliverable must exist in the repository before the gate passes. Verbal approval is not a gate.
4. **Product Quality Agent can block any gate.** Even if all 9 other gates pass, Product Quality Agent can reject a feature if it does not serve farmers. This is the only agent with asymmetric veto power.
5. **Temporary agents are created for specific tasks and deleted on completion.** They do not accumulate.
6. **No agent merges to main directly.** All work goes through feature branches → develop → main via Standards Agent gate.

---

## VIII. How Releases Work

### Branch Strategy

```
main          — always stable, always releasable
  │
  develop     — current sprint integration
    │
    feature/FP-002-ai-orchestrator
    feature/FP-003-weather
    feature/FP-005-disease
```

- No direct commits to `main` or `develop`
- Feature branches named: `feature/FP-XXX-short-name`
- Bug fix branches named: `fix/short-description`
- Every merge to `develop` requires Standards Agent approval
- Every merge to `main` requires Master Agent approval + passing CI

### Release Tags

| Tag | Name | Milestone |
|-----|------|-----------|
| v0.1 | Infrastructure | PostgreSQL, ChromaDB, Docker, RAG pipeline |
| v0.2 | Authentication | OTP login, JWT, farmer profile, farm registration |
| v0.3 | Conversation Platform | AI Orchestrator, streaming chat, TNAU citations |
| v0.4 | Weather Intelligence | Open-Meteo, rain alerts, irrigation advice |
| v0.5 | Disease Intelligence | Camera detection, Tamil treatment, TNAU guidance |
| v0.6 | Crop Intelligence | Crop recommendation, season calendar |
| v0.7 | Government Intelligence | Scheme eligibility, application guidance |
| v0.8 | Farm Intelligence | Dashboard, farm health summary |
| v0.9 | Smart Farming | Farm diary, expenses, notifications, AI memory |
| v1.0 | Public MVP | All 9 demo flows working, Tamil-first, Redmi 10 tested |

### Release Gate Requirements (all 10 must pass)

Planning → Architecture → Backend → Flutter → AI → Tests → Security → Performance → Documentation → Standards → **MERGE**

### Feature Freeze Rules

No Feature Pack may introduce:
- A new framework (e.g., replacing FastAPI with Django)
- A new database (e.g., adding MongoDB)
- A new AI model (e.g., replacing bge-m3)
- A new external dependency not in the frozen stack

Unless ALL of the following exist:
1. ADR written and approved
2. Architecture Agent has reviewed
3. Performance impact documented (latency, memory, storage)
4. Migration plan for existing data/services written
5. Master Agent has approved

**The bar is very high. If the existing stack can solve the problem, use the existing stack.**

---

## IX. Coding Philosophy

### The Four Rules

1. **No code without a Feature Pack.** Every line of code traces to an FP, which traces to a User Story, which traces to a real farmer problem.

2. **Simple and correct beats clever and fast.** A clear function that does one thing is always preferred over an optimized one that does three things.

3. **No abstractions without three use cases.** Don't build a base class for one subclass. Don't extract a utility for one caller. When you see the third similar thing, then abstract.

4. **The farmer's phone is the test.** Code that works in Docker but crashes on a Redmi 10 with 3 GB RAM and a bad 4G connection is not working code.

### What Good Code Looks Like Here

- Functions have type hints. Always.
- No f-strings in SQL. Always parameterized queries.
- API routes use hyphens, not underscores. (`/batch-predict`, not `/batch_predict`)
- Aadhaar is SHA-256 hashed before storage. Raw Aadhaar never touches the database.
- File uploads validate MIME type. Not extension — MIME type.
- All re-raises use `from exc`. (`raise NewError(...) from exc`)
- Comments explain *why*, never *what*. The code explains what.
- No secrets in code. Environment variables only.

### What We Don't Do

- No `git commit --no-verify`
- No `try/except: pass`
- No hardcoded phone numbers, API keys, or test credentials in committed code
- No `print()` in production paths — use structured logging
- No skipping tests because "it's just a small change"

---

## X. AI Philosophy

### The Hierarchy of Truth

When the AI answers a question, facts must come from this hierarchy (top = most trusted):

1. **Verified TNAU/ICAR documents** (RAG chunks, score ≥ 0.35)
2. **Real-time data** (Open-Meteo weather, AGMARKNET prices)
3. **Farmer-specific data** (their farm, crop, soil type, location from PostgreSQL)
4. **ML model output** (disease detection, satellite analysis) with confidence score
5. **LLM reasoning** — connecting the above, never inventing new facts

If no source above level 4 has an answer: Tamil fallback. No LLM generation.

### What the LLM Is For

The LLM's job is to:
- Understand what the farmer asked (any language, any phrasing)
- Select the right tools and interpret their output
- Translate grounded knowledge into natural, conversational Tamil
- Identify what information is missing and ask for it
- Suggest useful follow-up questions

The LLM is not a knowledge source. It is a translator and communicator.

### Confidence as a First-Class Citizen

Every answer has a confidence level, and confidence is communicated to the farmer:
- High (≥ 0.85): Present as recommendation
- Medium (0.50–0.84): Present as recommendation with "based on available data"
- Low (0.35–0.49): Present with explicit warning: "நம்பகத்தன்மை குறைவாக உள்ளது — உங்கள் BAO-ஐ உறுதிப்படுத்திக்கொள்ளுங்கள்"
- Below threshold (< 0.35): Do not call LLM. Return Tamil fallback.

### The Personalization Imperative

Generic advice is worse than no advice — it creates false confidence. Every recommendation must account for:
- The farmer's district (affects weather, pest pressure, soil)
- Their crop and current growth stage
- Their farm's soil type and irrigation source
- Their recent history (what they asked before, what they applied)

---

## XI. Product Philosophy

### The One Question

Every screen, every feature, every recommendation must answer one question for the farmer:

**"What do I need to do next?"**

Not: "What information does the system have?"
Not: "What did the AI calculate?"
Not: "What are all the options?"

The farmer is standing in a field. They need a decision. Give them a decision.

### The Murugan Standard

Every feature is evaluated against the Murugan persona:
- Male, 42 years old, Thanjavur district
- 1.8 hectares: paddy + banana
- Device: Redmi 10 (3 GB RAM, Helio G85, Android 11)
- Connectivity: Jio 4G, intermittent
- Language: Tamil-first, basic English reading
- Tech comfort: makes calls, uses WhatsApp, takes photos
- Does not type long sentences. Prefers camera and voice.

If Murugan cannot use a feature without help, the feature is not ready.

### UX Non-Negotiables

| Rule | Measurement |
|------|-------------|
| Response time | ≤ 5 seconds for simple queries (weather, disease); ≤ 8 seconds for complex advisory |
| Tamil-first | Every user-facing string has a Tamil version. English is secondary. |
| Camera over keyboard | Where possible, let the farmer photograph rather than type |
| One action per screen | Never present more than one primary call-to-action |
| Minimum touch target | 48×48 dp. No exceptions. |
| Error messages in Tamil | All error states show Tamil text with a specific next action |
| Offline graceful | Core flows degrade gracefully; clear "offline" state shown |
| Font size | Minimum 16sp for body text |

### What We Do Not Build (Until v1.0)

- No marketplace
- No community forum
- No expert consultation booking
- No IoT integration
- No drone integration
- No government dashboard (farmer-side is MVP; government portal is post-MVP)
- No carbon credits

These belong after a successful MVP with real Tamil Nadu farmer users.

---

## XII. The First Real Demo

Before any v1.0 celebration, this exact scenario must work, flawlessly, on a real Redmi 10:

**Scenario: Murugan decides whether to irrigate tomorrow**

1. Murugan opens UZHAVAN AI on his Redmi 10
2. Logs in with his mobile number → receives OTP → enters it
3. Profile setup: name "முருகன்", district "தஞ்சாவூர்", crop "நெல்"
4. Farm setup: 1.8 ha, alluvial soil, canal irrigation
5. Types: "நாளைக்கு தண்ணீர் விடலாமா?"

**System response (within 8 seconds):**
- Intent detected: irrigation advisory
- Weather Tool called: Thanjavur forecast retrieved (18 mm rain, 96% confidence)
- RAG Tool called: TNAU paddy irrigation guidelines retrieved
- Farmer profile context loaded: tillering stage paddy, canal water available
- ContextBuilder assembles all three inputs
- VerificationGraph confirms: 2 sources above threshold
- Qwen3 generates in Tamil:

> "நாளை தஞ்சாவூரில் 18 மிமீ மழை எதிர்பார்க்கப்படுகிறது (96% நம்பகத்தன்மை).
> இன்று நீர்ப்பாசனம் தேவையில்லை.
> TNAU வழிகாட்டுதல்படி, நெல்லின் பைத்தியம் நிலையில் 50 மிமீ நீர் தேவை.
> வியாழக்கிழமை மழை 15 மிமீ-க்கும் குறைவாக இருந்தால், வெள்ளிக்கிழமை காலை நீர்ப்பாசனம் செய்யுங்கள்."

- Source 1: Open-Meteo Thanjavur forecast (confidence: 96%)
- Source 2: TNAU Paddy Cultivation Manual — Irrigation chapter (confidence: 87%)
- Interaction stored in ai_memory: intent=irrigation, crop=paddy, district=Thanjavur, advice=defer
- request_traces row written: total_ms ≤ 8000

**This is UZHAVAN AI.** If this works, everything works.

---

## XIII. Implementation Priority (Fixed Through v1.0)

The implementation order is fixed. No deviation without Engineering Directive.

| Sprint | Deliverables | Version |
|--------|-------------|---------|
| Sprint 4 | ✅ AI Conversation Platform, ✅ Weather Tool, ✅ RAG quality, ✅ Disease Flutter integration | V0.3–V0.5 |
| Sprint 5 | Crop Recommendation, Government Schemes, Farmer Dashboard | V0.6–V0.8 |
| Sprint 6 | Farm Diary, Notifications, Voice Assistant | V0.9 |
| Sprint 7 | Satellite Intelligence, SICKLE Integration | V0.9 |
| Sprint 8 | Yield & Profit Prediction | V1.0 |

**Not in scope before v1.0:**
Marketplace, IoT, Drone, Community, WhatsApp, Admin portal, Carbon credits, Enterprise dashboards.

---

## XIV. Engineering Directive ED-001

**Directive:** No new features until the existing farmer journey is complete, tested, documented, and usable by a real Tamil Nadu farmer.

**Issued by:** Master Agent
**Date:** 2026-07-01
**Status:** Active — supersedes all sprint planning decisions

Every decision is evaluated against one question:

> **Does this make it easier for a Tamil Nadu farmer to make a better farming decision today?**

If the answer is "no," it does not belong in the MVP.

---

## XV. Document Governance

This document may only be amended by:
1. A written proposal from any agent or contributor
2. Review by Architecture Agent and Product Quality Agent
3. Approval by Master Agent
4. A new version number and change log entry

Minor clarifications (spelling, formatting) do not require this process.

**Amendment history:**

| Version | Date | Change | Approver |
|---------|------|--------|---------|
| 1.0 | 2026-07-01 | Initial constitution | Master Agent |
