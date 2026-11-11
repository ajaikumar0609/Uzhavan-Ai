# UZHAVAN AI — Milestones

Milestones are the measurable progress markers inside phases.
A milestone is complete only when all its Feature Packs are COMPLETE.

---

## Phase 2: Core AI Services ✅ COMPLETE

### M-01: Data Foundation ✅
- All 9 TNAU seed CSVs complete
- PostgreSQL schema live (21 tables)
- Embedding pipeline working

### M-02: AI Services Online ✅
- Disease Detection API (port 8001) — 5 endpoints
- Advisory RAG API (port 8002) — POST /ask with Tamil support
- Docker Compose stack running

---

## Phase 3: Delivery System ✅ COMPLETE

### M-03: Agent Organization ✅
- 15 permanent agent prompts
- STANDARDS.md
- Feature Pack template
- ADR template + 4 ADRs written
- Sprint 4 fully planned

---

## Phase 4: Farmer MVP 🔄 IN PROGRESS

**Goal:** Hand a phone to a Tamil Nadu farmer and get value in < 60 seconds.

### M-04: Authentication 🔜
**Feature Packs:** FP-001
**Done when:** Farmer can register with phone number, log in, create farm profile

### M-05: AI Chat 🔜
**Feature Packs:** FP-002
**Done when:** Farmer can ask a question in Tamil and get a TNAU-sourced answer

### M-06: Weather Agent 🔜
**Feature Packs:** FP-003
**Done when:** Farmer sees 7-day weather for their district + irrigation advice

### M-07: RAG Quality 🔜
**Feature Packs:** FP-004
**Done when:** Advisory answers cite source URL, confidence score shown, Tamil works

### M-08: Disease Camera Flow 🔜
**Feature Packs:** FP-005
**Done when:** Farmer photographs leaf, gets disease name in Tamil + treatment in < 5 seconds

---

## Phase 5: LangGraph Orchestration

### M-09: Multi-Tool Advisory
Farmer question triggers correct tool automatically (weather / knowledge / disease / market)

### M-10: Market Prices
Farmer sees today's mandi price for their crop in their district

### M-11: Farmer Profile Intelligence
Advisory considers farmer's district, crops, and season automatically

---

## Phase 6: Satellite

### M-12: SICKLE Integration
NDVI timeseries for farms; crop type prediction

### M-13: Growth Stage Monitoring
Satellite-based alerts for growth stages and anomalies

---

## Phase 7: Production

### M-14: WhatsApp Bot
Farmers can use UZHAVAN AI via WhatsApp (no app install required)

### M-15: IVR / Voice
Farmers can call a number and speak their question in Tamil

### M-16: Production Launch
10,000 farmers onboarded; monitoring live; SLA defined

---

## Progress Tracker

| Milestone | Status | Sprint |
|-----------|--------|--------|
| M-01 Data Foundation | ✅ Complete | Sprint 1-2 |
| M-02 AI Services | ✅ Complete | Sprint 2-3 |
| M-03 Agent Organization | ✅ Complete | Sprint 3 |
| M-04 Authentication | 🔜 Planned | Sprint 4 |
| M-05 AI Chat | 🔜 Planned | Sprint 4 |
| M-06 Weather Agent | 🔜 Planned | Sprint 4 |
| M-07 RAG Quality | 🔜 Planned | Sprint 4 |
| M-08 Disease Camera | 🔜 Planned | Sprint 4 |
| M-09 Multi-Tool | 🔜 Sprint 5 | — |
| M-10 Market Prices | 🔜 Sprint 5 | — |
