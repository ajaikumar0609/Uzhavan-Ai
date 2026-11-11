# UZHAVAN AI — Project Status Audit

**Audited:** 2026-07-01
**Auditor:** Architecture Agent (read-only scan)
**Scope:** Full repository at `/uzhavan_platform/`

---

## 1. Repository Structure

```
uzhavan_platform/
├── agents/          ✅ 19 agent prompts (all permanent agents + product-quality)
├── api/             ⚠️  OLD location — 3 services (advisory, auth, disease_detection)
│                        Approved arch moves these to backend/
├── apps/            ❌ EMPTY — Flutter app not started
│   ├── farmer/      ❌ empty
│   └── admin/       ❌ empty
├── backend/         ❌ EMPTY — approved three-layer arch not yet implemented
│   ├── conversation/ ❌ empty
│   ├── decision/    ❌ empty
│   ├── knowledge/   ❌ empty
│   ├── tools/       ❌ empty
│   └── (others)     ❌ empty
├── data_pipeline/   ✅ normalize_tnau.py, embed_chunks.py
├── database/
│   ├── migrations/  ⚠️  3 of 4 migrations (004_observability_memory.sql missing)
│   ├── data/        ✅ 9 seed CSV files
│   └── seed/        ❌ empty (seed CSVs are in data/, not seed/)
├── docker/          ⚠️  Compose covers OLD api/ services, not new three-layer backend
├── docs/
│   ├── adr/         ✅ 8 ADRs (complete)
│   ├── architecture/ ✅ CONVERSATION-SERVICE.md v2.0
│   ├── audit/       ✅ this directory
│   ├── feature-packs/ ✅ 5 FPs (FP-001 to FP-005)
│   ├── milestones/  ✅ MILESTONES.md
│   ├── roadmap/     ⚠️  DUPLICATE — docs/ROADMAP.md AND docs/roadmap/ROADMAP.md
│   ├── sprints/     ⚠️  DUPLICATE — docs/SPRINT.md AND docs/sprints/SPRINT-004.md
│   ├── UX/          ⚠️  INCOMPLETE — 4 of 5 files (Design System.md missing); duplicate Farmer Journey
│   ├── FRAMEWORK.md ✅
│   ├── PRD.md       ✅
│   └── PROJECT_BIBLE.md ✅
├── evaluation/      ⚠️  5 of 6 files (weather_eval.py missing); results/ empty
├── infra/           ❌ EMPTY
├── knowledge/       ❌ EMPTY (TNAU crawler output not yet placed here)
├── ml/              ❌ EMPTY
├── models/          ❌ EMPTY (disease/satellite/recommendation stubs)
├── playbooks/       ⚠️  5 of 7 files (Performance Tuning.md and Release Checklist.md missing)
├── rag/             ❌ EMPTY (ChromaDB not yet populated; chunks.jsonl not generated)
├── tests/           ⚠️  Tests for auth only; advisory/disease/graph tests not written
└── .github/workflows/ ❌ EMPTY — CI/CD pipeline not configured
```

---

## 2. Implemented Modules

| Module | Location | Status | Notes |
|--------|----------|--------|-------|
| OTP Auth | `api/auth/` | ✅ Complete | 555 lines, 11 tests |
| JWT utils | `api/auth/jwt_utils.py` | ✅ Complete | HS256, 15min/7day |
| Rate limiting | `api/auth/rate_limit.py` | ✅ Complete | Redis, 3 OTP/hr |
| Disease Detection API | `api/disease_detection/` | ✅ Complete | MobileNetV2, 38 classes |
| TNAU Guidance DB | `api/disease_detection/tnau_guidance.py` | ✅ Complete | All 38 labels |
| Advisory RAG API | `api/advisory/` | ✅ Functional | Old arch — superseded by FP-002 |
| TNAU normalizer | `data_pipeline/normalize_tnau.py` | ✅ Complete | ETL pipeline |
| Embedding pipeline | `data_pipeline/embed_chunks.py` | ✅ Complete | bge-m3, incremental |
| DB schema | `database/migrations/001_initial_schema.sql` | ✅ Complete | 21 tables, PostGIS |
| Seed data | `database/migrations/002_seed_data.sql` | ✅ Complete | 50 crops, 25 fertilizers, 38 districts |
| Auth tables | `database/migrations/003_auth_tables.sql` | ✅ Complete | otp_requests, refresh_tokens |
| Docker stack | `docker/docker-compose.yml` | ⚠️ Partial | Covers old api/ services only |
| Auth tests | `tests/api/auth/` | ✅ Complete | 9 integration tests |

---

## 3. Missing Modules (Critical for FP-002)

| Module | Should Be At | Blocked On |
|--------|-------------|-----------|
| ConversationState | `backend/decision/state.py` | Implementation start |
| LangGraph graphs (7) | `backend/decision/graph/` | Implementation start |
| ContextBuilder | `backend/decision/context_builder.py` | Implementation start |
| PromptBuilder | `backend/decision/prompt_builder.py` | Implementation start |
| Tool Registry | `backend/tools/registry.py` | Implementation start |
| Tool implementations | `backend/tools/*.py` (6 tools) | Implementation start |
| Knowledge Layer | `backend/knowledge/` (5 sources) | Implementation start |
| Conversation Layer | `backend/conversation/main.py` | Decision Layer complete |
| Feature flags | `backend/feature_flags.py` | Implementation start |
| Shared models | `backend/shared/models.py` | Implementation start |
| Prompt templates | `backend/prompts/*.md` (7 files) | Implementation start |
| Observability logger | `backend/decision/observability.py` | Implementation start |
| Flutter app | `apps/farmer/` | Backend complete |

---

## 4. Missing APIs

| Endpoint | Service | Missing Since | Required By |
|----------|---------|--------------|------------|
| POST /chat (SSE) | Conversation Layer | Not started | FP-002 |
| GET /chat/history | Conversation Layer | Not started | FP-002 |
| GET /chat/session/{id} | Conversation Layer | Not started | FP-002 |
| GET /weather/{district} | Weather Layer | Not started | FP-003 |
| GET /health (conversation) | Conversation Layer | Not started | FP-002 |

**Existing APIs (in old api/ location):**
- POST /predict, POST /batch-predict, GET /supported-crops, GET /supported-diseases, GET /disease/{name} — disease detection ✅
- POST /ask, GET /health — old advisory service ✅ (superseded by FP-002)
- POST /auth/send-otp, POST /auth/verify-otp, POST /farmers/profile, POST /farms, GET /farmers/me ✅

---

## 5. Missing Database Migrations

| File | Content | Status |
|------|---------|--------|
| `004_observability_memory.sql` | `request_traces` + `ai_memory` tables | ❌ NOT WRITTEN |

---

## 6. Missing Documentation

| Document | Status | Priority |
|----------|--------|---------|
| `docs/UX/Design System.md` | ❌ Missing | Medium |
| `docs/UX/Navigation.md` | ❌ Missing | Medium |
| `docs/ENGINEERING_DASHBOARD.md` | ❌ Missing | Low |
| `docs/GOLDEN_USER_STORIES.md` | ❌ Missing | High |
| `playbooks/Performance Tuning.md` | ❌ Missing | Medium |
| `playbooks/Release Checklist.md` | ❌ Missing | High |
| `evaluation/weather_eval.py` | ❌ Missing | Medium |
| `backend/*/README.md` | ❌ Not yet (backend not built) | Low |
| CHANGELOG.md | ❌ Missing | Medium |
| `docs/UX/Farmer Journey.md` (space) | ⚠️ Duplicate of `Farmer_Journey.md` | Low — cleanup |

---

## 7. Missing Tests

| Test File | Coverage Gap | Priority |
|-----------|-------------|---------|
| `tests/api/advisory/test_main.py` | /ask endpoint | High |
| `tests/api/advisory/test_rag_engine.py` | ChromaDB retrieval | High |
| `tests/decision/test_intent_graph.py` | Intent classification | Critical |
| `tests/decision/test_verification_graph.py` | Hallucination guardrail | Critical |
| `tests/decision/test_context_builder.py` | Context assembly | High |
| `tests/tools/test_registry.py` | Tool registry | High |
| `tests/e2e/test_murugan_flow.py` | Golden user story #1 | Critical |
| `tests/e2e/test_lakshmi_flow.py` | Golden user story #2 | High |

---

## 8. Missing Docker Services

| Service | Status | Needed For |
|---------|--------|-----------|
| `backend/conversation` service | ❌ No Dockerfile | FP-002 |
| Ollama service definition | ❌ Not in compose | FP-002 local dev |
| Migration runner service | ❌ Not in compose | All |
| Auth service | ❌ Not in compose (only old advisory/disease) | FP-001 prod |

---

## 9. Missing Environment Variables

| Variable | Status | Used By |
|----------|--------|---------|
| `JWT_SECRET` | ❌ Not in `.env.example` | Auth service — **CRITICAL** |
| `ENV` | ❌ Not in `.env.example` | Dev/prod OTP logging toggle |
| `LLM_PROVIDER` | ✅ Present | Advisory |
| `ANTHROPIC_API_KEY` | ✅ Present | Claude fallback |
| `OLLAMA_HOST` | ✅ Present | Qwen3 |
| `DATABASE_URL` | ✅ Present | All services |
| `REDIS_URL` | ✅ Present | Auth + advisory |
| `CHROMA_PATH` | ✅ Present | RAG |

---

## 10. Missing CI/CD

| Item | Status |
|------|--------|
| `.github/workflows/ci.yml` | ❌ Directory exists but empty |
| Black/Ruff/MyPy lint job | ❌ |
| pytest + coverage job | ❌ |
| pip-audit security scan | ❌ |
| Docker build job | ❌ |
| API smoke test job | ❌ |
| Branch protection rules | ❌ Not configurable from repo |

---

## 11. Missing Flutter Integration

**Everything.** `apps/farmer/` is completely empty.

Required for FP-002 demo:
- Flutter project scaffold
- ChatScreen + SSE consumer
- ChatHistoryScreen
- Source citation card widget
- Suggestion chips widget
- Intent chip widget

Required for FP-001 (already implemented backend):
- PhoneInputScreen
- OTPVerifyScreen
- ProfileSetupScreen
- FarmSetupScreen

---

## 12. Missing LangGraph Nodes

All Decision Layer graph nodes are missing (backend not yet built):

| Node | File | Status |
|------|------|--------|
| ConversationGraph (root) | `backend/decision/graph/conversation.py` | ❌ |
| IntentGraph | `backend/decision/graph/intent.py` | ❌ |
| PlanningGraph | `backend/decision/graph/planner.py` | ❌ |
| ToolExecutionGraph | `backend/decision/graph/tools.py` | ❌ |
| VerificationGraph | `backend/decision/graph/verification.py` | ❌ |
| ResponseGraph | `backend/decision/graph/response.py` | ❌ |

---

## 13. Missing RAG Pipeline Pieces

| Piece | Status | Blocker |
|-------|--------|---------|
| TNAU crawler output | `knowledge/tnau/` empty | TNAU crawler not run |
| `chunks.jsonl` | `rag/` empty | normalize_tnau.py not run against real data |
| ChromaDB population | `rag/chroma/` empty | embed_chunks.py not run |
| Score threshold filter (≥0.35) | In old `rag_engine.py` partially | Needs move to `backend/knowledge/rag/engine.py` |
| District metadata filter | Not implemented | FP-004 |

---

## 14. STANDARDS.md Conflict

`agents/standards/STANDARDS.md` still references the **old** folder structure (`api/`, `mobile/`). It has not been updated to reflect the approved three-layer architecture (`backend/conversation/`, `backend/decision/`, `backend/knowledge/`).

---

## 15. Conflicting Architecture Documents

| Conflict | Files | Resolution |
|----------|-------|-----------|
| Old folder layout in STANDARDS.md | `agents/standards/STANDARDS.md` | Update to match ADR-008 |
| Duplicate ROADMAP | `docs/ROADMAP.md` + `docs/roadmap/ROADMAP.md` | Delete `docs/ROADMAP.md` (keep `docs/roadmap/ROADMAP.md`) |
| Duplicate SPRINT | `docs/SPRINT.md` + `docs/sprints/SPRINT-004.md` | Delete `docs/SPRINT.md` (keep `docs/sprints/`) |
| Duplicate Farmer Journey | `docs/UX/Farmer Journey.md` + `docs/UX/Farmer_Journey.md` | Delete space-version |
| pytest.ini coverage target | `--cov=api` but approved arch is `backend/` | Update after backend built |
