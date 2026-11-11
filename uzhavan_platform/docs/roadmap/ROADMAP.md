# UZHAVAN AI — Product Roadmap

**Mission:** Empower every Tamil Nadu farmer with trustworthy AI-powered agricultural guidance grounded in official knowledge, real-time data, and intelligent automation.

---

## Release Timeline

| Version | Theme | Status |
|---------|-------|--------|
| V0.1 | Infrastructure | ✅ Complete |
| V0.2 | Authentication | ✅ Complete (FP-001) |
| V0.3 | AI Chat | 🔄 In Progress (Sprint 4) |
| V0.4 | Weather Intelligence | Planned |
| V0.5 | Disease Detection | Planned |
| V0.6 | Crop Recommendation | Planned |
| V0.7 | Government Schemes | Planned |
| V0.8 | Farmer Dashboard | Planned |
| V0.9 | Farm Diary | Planned |
| V1.0 | Public MVP | Target |

---

## Phase 0 — Infrastructure ✅ Complete

**Deliverables:** PostgreSQL + PostGIS schema, ChromaDB, Docker Compose, TNAU crawler, embedding pipeline, disease detection API, advisory RAG service.

---

## Phase 1 — Daily Farmer Assistant 🔄 Current

**Goal:** A Tamil Nadu farmer can ask any crop question, check weather, and detect diseases from a photo.

| Feature Pack | Description | Sprint | Status |
|-------------|-------------|--------|--------|
| FP-001 | Farmer Authentication | Sprint 4 | ✅ DONE |
| FP-002 | AI Chat (LangGraph + Qwen3) | Sprint 4 | 🔄 CURRENT |
| FP-003 | Weather Intelligence | Sprint 4 | ⏳ NEXT |
| FP-004 | RAG Quality | Sprint 5 | Planned |
| FP-005 | Disease Detection Flutter | Sprint 5 | Planned |
| FP-006 | Government Schemes | Sprint 5 | Planned |
| FP-007 | Crop Recommendation | Sprint 6 | Planned |

---

## Phase 2 — Farm Management

Farm Diary, Expenses, Income, Profit tracking, Calendar, Notifications, AI Memory.

---

## Phase 3 — Precision Agriculture

Satellite NDVI, Yield prediction, Profit prediction, GIS mapping, Risk analysis.

---

## Phase 4 — Connected Ecosystem

Marketplace, Expert access, Community, WhatsApp integration, Admin panel.

---

## Phase 5 — Enterprise

IoT sensors, Drone integration, Government dashboard, Analytics, Climate, Carbon tracking.

---

## MVP v1.0 — Public Demo Flows

The MVP is complete when a Tamil Nadu farmer can do all nine:

1. Register using OTP — phone number only, no password
2. Create a farm profile — name, district, crop, area
3. Ask questions in Tamil, English, or Tanglish
4. Receive grounded answers from TNAU knowledge with source citations
5. Check weather and get irrigation advice for their district
6. Photograph a diseased plant and identify the disease
7. View TNAU treatment recommendations in Tamil
8. Discover relevant government scheme eligibility
9. See a simple dashboard: farm, weather, and recent activity
