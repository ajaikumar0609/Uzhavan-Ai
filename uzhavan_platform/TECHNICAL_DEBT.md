# UZHAVAN AI — Technical Debt Register

Tracked items that do not block current sprint but must not be forgotten.

---

## Open

### TD-001 — FastAPI/Pydantic compatibility in Auth module
- **File:** `api/auth/main.py`, `api/auth/rate_limit.py`, `tests/api/auth/test_main.py`
- **Description:** `check_and_increment()` in `rate_limit.py` calls `redis.incr()` synchronously, but the test injects `AsyncMock`. The coroutine is compared with `>` against `int`, raising `TypeError`.
- **Root cause:** `api/auth/` was written for sync Redis. Test mocks assume async. Mismatch was introduced before Sprint 4.
- **Impact:** 2 test failures in `tests/api/auth/test_main.py`. No production impact — the auth module is tested at integration level via FastAPI test client.
- **Blocked features:** None
- **Resolution:** Make `rate_limit.py` async (`await redis.incr(key)`) and update mock accordingly.
- **Priority:** Medium
- **Sprint:** Maintenance (does not block Sprint 5)
- **Opened:** 2026-07-01

---

### TD-002 — Observability migration missing
- **File:** `database/migrations/004_observability_memory.sql`
- **Description:** The observability schema (NodeTrace, ConversationTurn persistence to PostgreSQL) was never written. Currently all traces are in-memory.
- **Impact:** Traces lost on restart. Analytics not queryable via SQL.
- **Resolution:** Write migration; add SQLAlchemy models for NodeTrace and ConversationTurn; update `persist_turn()` to write to DB.
- **Priority:** Low
- **Sprint:** Sprint 5
- **Opened:** 2026-07-01

---

### TD-003 — CI/CD pipeline missing
- **File:** `.github/workflows/ci.yml`
- **Description:** No automated test run on push. All test runs are manual.
- **Impact:** Regressions possible if tests not run before merge.
- **Resolution:** Add GitHub Actions workflow: `pytest`, `ruff`, `mypy` on pull_request.
- **Priority:** Medium
- **Sprint:** Sprint 5
- **Opened:** 2026-07-01

---

### TD-004 — In-memory session store
- **File:** `backend/session/store.py`
- **Description:** `_store: dict[str, tuple[str, float]]` with TTL. Sessions do not survive process restart. Not safe for multi-process/multi-worker deployment.
- **Impact:** Session continuity broken on restart. Cannot scale horizontally.
- **Resolution:** Replace with Redis-backed store. Interface is already abstracted (`store_set`, `store_get`, etc.) — swap the implementation only.
- **Priority:** Medium
- **Sprint:** Sprint 7 (pre-production)
- **Opened:** 2026-07-01

---

### TD-005 — RAG ChromaDB not populated
- **File:** `backend/tools/agents/rag_agent.py`, `rag/`
- **Description:** `rag.advisory` capability is registered in `AgentRegistry` but ChromaDB contains no indexed Tamil Nadu agriculture documents. Every call is skipped with a warning.
- **Impact:** All responses rely on structured agent data only. Free-text TNAU/ICAR document retrieval is non-functional.
- **Resolution:** Index TNAU crop management guides, pest bulletins, and scheme documents into ChromaDB. Evaluate retrieval quality in Sprint 5.
- **Priority:** High
- **Sprint:** Sprint 5
- **Opened:** 2026-07-01

---

## Closed

*(None yet — this register was opened at v0.4.0-alpha)*

---

## Process

- New debt is added here at discovery time with a sprint assignment.
- Closed debt is moved to the Closed section with resolution date.
- Priority: **High** = blocks intelligence quality. **Medium** = blocks scaling or correctness. **Low** = improves maintainability.
