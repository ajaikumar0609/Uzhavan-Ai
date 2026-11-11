# UZHAVAN AI — Project Health Report

**Audited:** 2026-07-01
**Scope:** Full repository read-only scan
**Scale:** 0 (not started) → 100 (production-ready)

---

## Executive Summary

| Subsystem | Score | Status |
|-----------|-------|--------|
| Architecture & Design | 88 | ✅ Strong |
| Database Schema | 82 | ✅ Strong |
| Authentication Service | 90 | ✅ Production-ready |
| Disease Detection Service | 78 | ✅ Functional |
| Advisory RAG (old arch) | 55 | ⚠️ Functional but superseded |
| Decision Layer (LangGraph) | 0 | ❌ Not started |
| Knowledge Layer | 12 | ❌ Not started |
| Conversation Layer (new) | 0 | ❌ Not started |
| Tool Registry | 0 | ❌ Not started |
| Flutter App | 0 | ❌ Not started |
| Testing | 28 | ❌ Critically under-tested |
| CI/CD | 5 | ❌ Not configured |
| Documentation | 72 | ⚠️ Core docs strong; UX/playbooks incomplete |
| Security | 65 | ⚠️ Auth strong; backend/prompts not yet reviewable |
| Observability | 8 | ❌ Tables not migrated; no tracing |
| **Overall** | **42** | ⚠️ Solid foundation; core AI not yet built |

---

## 1. Architecture & Design — Score: 88

**Strengths:**
- All 8 ADRs written with rejected alternatives documented
- Three-layer architecture (ADR-008) is the right decision for multi-interface future
- Modular LangGraph design (ADR-005) prevents monolith creep
- Tool Registry with MCP compatibility (ADR-006) is forward-thinking
- ConversationState, SourceCitation, ResponseObject all fully specified
- No-hallucination guardrail (VerificationGraph) designed before implementation
- Feature flags designed in from day one

**Gaps:**
- STANDARDS.md still references old `api/` layout (not updated to `backend/`)
- 3 duplicate documents exist (ROADMAP, SPRINT, Farmer Journey)
- Architecture docs not yet validated against running code (because no running code in new arch)

**Risk:** Low. The architecture is solid. Execution risk is in implementation.

---

## 2. Database Schema — Score: 82

**Strengths:**
- 21-table schema with PostGIS geometry support
- Correct index strategy (partial indexes on hot query paths)
- Soft-delete pattern consistent across farmer data tables
- SHA-256 hash for OTP (not plaintext)
- Refresh token hash stored, raw token never saved

**Gaps:**
- Migration 004 (request_traces + ai_memory) not written — required for FP-002
- `database/seed/` directory is empty (seed CSVs live in `database/data/`)
- No migration runner in Docker Compose (manual migration required)
- District geometry data not populated (PostGIS columns exist but no coordinates)

**Risk:** Medium. A developer running the project will hit migration 004 before being able to test AI features.

---

## 3. Authentication Service — Score: 90

**Strengths:**
- OTP: SHA-256 with phone salt, constant-time comparison, 5-minute expiry
- JWT: short-lived access token (15min) + hashed refresh token (7 days)
- Rate limiting: Redis-backed, 3 OTP attempts/hour per phone
- Parameterized SQL throughout — no f-strings in queries
- Full test coverage: 7 unit + 9 integration tests

**Gaps:**
- `JWT_SECRET` not in `.env.example` — could cause silent startup failures
- Auth service not in Docker Compose (service only in old docker-compose)
- No refresh token rotation test

**Risk:** Low for the service itself. Medium for deployment (missing JWT_SECRET in env template).

---

## 4. Disease Detection Service — Score: 78

**Strengths:**
- MobileNetV2 with full 38-class PlantVillage support
- TNAU guidance lookup for all 38 disease labels
- Correct hyphenated route naming (/batch-predict, not /batch_predict)
- MIME type validation on uploads (not extension-based)

**Gaps:**
- No integration tests for /predict endpoint
- Model path hardcoded to relative `models/` — may fail when run from different CWD
- No test for oversized file rejection
- Confidence threshold not configurable (hardcoded 0.6 in predict handler)

**Risk:** Medium. Works for happy path. Edge cases (wrong MIME, corrupt file, low confidence) not tested.

---

## 5. Advisory RAG Service (old arch) — Score: 55

**Strengths:**
- bge-m3 multilingual embeddings correctly chosen (Tamil+English same vector space)
- Score threshold (≥0.35) prevents low-quality retrievals
- ChromaDB incremental embedding pipeline written

**Gaps:**
- This service is **superseded by FP-002**. Any work here is throwaway.
- ChromaDB is empty — embed_chunks.py has not been run against real TNAU data
- No hallucination check (LLM called even with 0 retrieved chunks)
- English-only prompt templates (no Tamil)
- No citation tracking (no SourceCitation, no source logging)

**Risk:** High if this service is used in production. It WILL hallucinate on unknown topics. The FP-002 VerificationGraph must be built before this is exposed to farmers.

---

## 6. Decision Layer (LangGraph) — Score: 0

**Strengths:** Fully designed in FP-002 + ADR-005. All 7 nodes specified. No architectural ambiguity.

**Gaps:** `backend/decision/` is empty. Nothing implemented.

Required files not yet created:
- `backend/decision/state.py` — ConversationState
- `backend/decision/graph/__init__.py`
- `backend/decision/graph/conversation.py`
- `backend/decision/graph/intent.py`
- `backend/decision/graph/planner.py`
- `backend/decision/graph/tools.py`
- `backend/decision/graph/verification.py`
- `backend/decision/graph/response.py`
- `backend/decision/context_builder.py`
- `backend/decision/prompt_builder.py`
- `backend/decision/observability.py`

**Risk:** Critical. This is the core of the platform. Without it, UZHAVAN AI does not exist.

---

## 7. Knowledge Layer — Score: 12

**Strengths:**
- Open-Meteo integration designed (ADR weather contract documented)
- TNAU normalizer exists (`data_pipeline/normalize_tnau.py`) — can populate RAG
- bge-m3 embedding pipeline exists (`data_pipeline/embed_chunks.py`)

**Gaps:**
- `backend/knowledge/` is empty — none of the refactored knowledge modules exist
- `rag/` directory empty — ChromaDB not populated with TNAU chunks
- `knowledge/tnau/` empty — TNAU PDF crawler output not present
- Weather, disease client, market, satellite, memory modules: not written
- Score: 12 because the data pipeline scripts exist even though they haven't been run

**Risk:** Critical. No knowledge layer = no AI answers.

---

## 8. Conversation Layer (new arch) — Score: 0

**Strengths:** Fully specified in CONVERSATION-SERVICE.md v2.0.

**Gaps:** `backend/conversation/` is empty. Nothing implemented.

Required files not yet created:
- `backend/conversation/main.py` — FastAPI /chat SSE + history
- `backend/conversation/session.py` — session CRUD
- `backend/conversation/streaming.py` — SSE event writer
- `backend/conversation/rate_limit.py` — per-farmer rate limiting

**Risk:** Critical. Without this, no farmer can talk to the AI.

---

## 9. Tool Registry — Score: 0

**Strengths:** Fully specified in ADR-006. ToolDefinition schema documented. MCP manifest contract defined.

**Gaps:** `backend/tools/` is empty. Registry and all 6 tool wrappers not written.

**Risk:** Critical. ToolRegistry is the bridge between Decision Layer and Knowledge Layer.

---

## 10. Flutter App — Score: 0

**Gaps:** `apps/farmer/` is completely empty.

Even FP-001 backend (auth) is complete, but no Flutter screens exist for:
- Phone number entry
- OTP verification
- Profile setup
- Farm setup
- Chat (for FP-002)
- Disease detection photo upload (for FP-002)

**Risk:** High. No UI = no farmer demo = no Product Quality Gate = no v0.3.

---

## 11. Testing — Score: 28

**Strengths:**
- 16 tests covering the auth service (7 unit + 9 integration)
- Test structure correct (unit/integration separation)
- pytest.ini configured with coverage reporting

**Gaps:**
- No tests for advisory service
- No tests for disease detection service
- No tests for any Decision Layer components (doesn't exist yet)
- No end-to-end Murugan flow test
- No tests for VerificationGraph (the hallucination guardrail)
- Coverage target (`--cov=api`) will miss `backend/` when it's built

**Test Debt Estimate:** ~80 test cases needed to reach acceptable coverage for FP-002 completion.

**Risk:** High. The most critical component (VerificationGraph — the no-hallucination guardrail) has zero test coverage, and it hasn't been built yet. When built, it MUST be tested before connecting to production.

---

## 12. CI/CD — Score: 5

**Strengths:**
- `.github/workflows/` directory exists
- `pytest.ini` configured

**Gaps:**
- No CI workflow file exists
- No automated lint (Black, Ruff, MyPy)
- No automated test run on push
- No pip-audit security scanning
- No Docker build validation
- Score: 5 for having the directory and pytest config only

**Risk:** Medium for now (small team, local testing). High before v0.3 release (any merge to main is unguarded).

---

## 13. Documentation — Score: 72

**Strengths:**
- PROJECT_BIBLE.md complete (500 lines, 15 sections)
- PRD.md complete (13 sections)
- FRAMEWORK.md complete (delivery pipeline, 18 agents)
- All 8 ADRs written with alternatives documented
- CONVERSATION-SERVICE.md v2.0 complete
- 5 of 7 playbooks written
- 5 of 6 evaluation scripts written

**Gaps:**
- docs/UX/Design System.md missing
- docs/UX/Navigation.md missing
- playbooks/Performance Tuning.md missing
- playbooks/Release Checklist.md missing
- GOLDEN_USER_STORIES.md missing
- ENGINEERING_DASHBOARD.md missing
- CHANGELOG.md missing
- 3 duplicate documents (ROADMAP, SPRINT, Farmer Journey with space)
- STANDARDS.md folder paths outdated (references `api/` not `backend/`)

**Risk:** Low for architecture docs. Medium for onboarding a new developer (missing playbooks + outdated STANDARDS.md would cause confusion).

---

## 14. Security — Score: 65

**Strengths:**
- No raw Aadhaar storage (SHA-256 hash)
- No hardcoded secrets (all from env)
- Parameterized SQL throughout existing code
- MIME type validation on file uploads
- Constant-time OTP comparison
- `from exc` pattern enforced on re-raises

**Gaps:**
- JWT_SECRET missing from `.env.example` (security misconfiguration risk)
- Prompt injection check not yet implemented (backend/decision not built)
- No rate limiting on /chat endpoint (Conversation Layer not built)
- pip-audit not run on any service
- No SAST tool in CI (CI not configured)
- Conversation Layer JWT validation not yet built

**Risk:** Medium. Auth layer is secure. Backend LLM prompt injection protection is the highest-priority security item not yet addressed.

---

## 15. Observability — Score: 8

**Strengths:**
- `request_traces` and `ai_memory` tables fully designed in FP-002
- Table schema specified in CONVERSATION-SERVICE.md v2.0
- `backend/decision/observability.py` planned

**Gaps:**
- Migration 004 not written (tables don't exist in DB)
- `backend/decision/observability.py` not implemented
- No trace IDs anywhere in existing code
- No Grafana / dashboard configuration
- Score: 8 for having the design

**Risk:** High for production operation. Without trace IDs, debugging any AI response quality issue requires log-grep instead of structured query.

---

## Key Risks Summary

| Risk | Severity | Owner | Resolution |
|------|----------|-------|-----------|
| Decision Layer (LangGraph) not built | **Critical** | AI Agent | Sprint 4 Step 2 |
| Knowledge Layer not built | **Critical** | AI Agent | Sprint 4 Step 3 |
| Conversation Layer not built | **Critical** | Backend Agent | Sprint 4 Step 4 |
| VerificationGraph (hallucination guard) not built | **Critical** | AI Agent | Sprint 4 Step 2 |
| ChromaDB empty (RAG has no data) | **Critical** | RAG Agent | Run embed_chunks.py |
| Flutter app empty (no farmer UI) | **High** | Flutter Agent | Sprint 4 Step 5 |
| Migration 004 missing | **High** | Database Agent | Sprint 4 Step 1 |
| JWT_SECRET not in .env.example | **High** | Backend Agent | Fix now (5 min) |
| No CI/CD pipeline | **High** | DevOps Agent | Sprint 4 Step 7 |
| STANDARDS.md outdated | **Medium** | Standards Agent | Fix now (15 min) |
| Old advisory service has no hallucination check | **High** | AI Agent | Do not expose until FP-002 complete |

---

## What's Actually Working End-to-End

At this moment, the following can be demonstrated:

1. **OTP Auth flow** — send OTP, verify OTP, get JWT. Works completely. ✅
2. **Farmer profile + farm creation** — works after auth. ✅
3. **Disease detection** — upload leaf photo, get disease label + TNAU guidance. ✅
4. **Old advisory service** — ask a question, get a RAG answer (IF ChromaDB is populated). ⚠️ No hallucination check.
5. **TNAU normalization** — run normalize_tnau.py against PDFs to produce chunks.jsonl. ✅

What **cannot** be demonstrated yet:
- Any FP-002 AI orchestration (Decision Layer is empty)
- Tamil-language farming advice with citations
- Murugan demo (no Flutter UI, no SSE chat API)
- Any conversation history
- Any confidence scoring or source attribution on new architecture

---

## Conclusion

The project has strong architectural foundations and a complete auth service. The core AI platform (FP-002 Decision + Knowledge + Conversation layers) is 0% implemented despite being fully designed and approved. The platform is at TRL 4 (technology validated in lab) for individual components, not yet at TRL 5 (technology validated in relevant environment) as a complete system.

**The single most important next action is:** Begin Sprint 4 Step 1 → Step 2 → Step 3 → Step 4 in sequence. The Murugan demo is the milestone.
