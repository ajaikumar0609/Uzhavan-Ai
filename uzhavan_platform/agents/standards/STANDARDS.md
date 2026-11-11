# UZHAVAN AI — Project Standards

Enforced by the **Project Standards Agent**. Every sub-agent must read this before writing code.

---

## 1. Repository Structure

```
uzhavan_platform/
├── backend/                # Three-layer AI platform (ADR-008)
│   ├── conversation/       # Conversation Layer — HTTP, SSE, sessions, rate limiting
│   ├── decision/           # Decision Layer — LangGraph graphs, state, context, prompts
│   │   └── graph/          # 6 LangGraph subgraphs (intent, planner, tools, verify, response, root)
│   ├── knowledge/          # Knowledge Layer — RAG, weather, disease client, market, memory
│   │   ├── rag/            # ChromaDB retrieval engine
│   │   ├── weather/        # Open-Meteo integration
│   │   ├── disease/        # Disease service HTTP client
│   │   ├── market/         # AGMARKNET stub (ENABLE_MARKET=false)
│   │   ├── satellite/      # SICKLE model stub (ENABLE_SATELLITE=false)
│   │   └── memory/         # ai_memory read/write
│   ├── tools/              # Tool Registry — bridges Decision → Knowledge (ADR-006)
│   ├── prompts/            # Prompt templates as .md files (no strings in Python)
│   ├── shared/             # Shared data models used by all three layers
│   │   ├── models.py       # ConversationState, ResponseObject, SourceCitation, ToolDefinition
│   │   └── exceptions.py   # UzhavanError, RAGError, WeatherError, VerificationError
│   ├── auth/               # Auth service — OTP, JWT (FP-001, complete)
│   └── feature_flags.py    # Feature flag registry, env-var override
├── api/                    # LEGACY — disease_detection service (keep until migrated to backend/)
├── apps/
│   ├── farmer/             # Flutter app (presentation layer only)
│   └── admin/              # Admin dashboard (future)
├── data_pipeline/          # ETL scripts — normalize_tnau.py, embed_chunks.py
├── database/
│   ├── migrations/         # 001_, 002_... numbered SQL files
│   └── data/               # seed CSVs
├── knowledge/              # Raw source data — TNAU PDFs, crawled text
│   └── tnau/               # TNAU crop guides and cultivation manuals
├── rag/
│   └── chroma/             # ChromaDB persistence directory
├── ml/                     # ML model training / evaluation
├── evaluation/             # AI evaluation scripts and benchmarks
├── tests/                  # mirrors backend/ structure
├── docs/                   # Architecture docs, ADRs, PRD, feature packs
├── agents/                 # Agent prompts (this folder)
├── playbooks/              # Operational runbooks
└── docker/                 # Dockerfiles + compose
```

**Layer boundary rules (ADR-008):**
- `conversation/` may call `decision/` only — never call `knowledge/` or `tools/` directly
- `decision/` may call `tools/` only — never call `knowledge/` directly
- `tools/` may call `knowledge/` only — never call `decision/` or `conversation/`
- `shared/` may be imported by any layer — contains only data classes, no logic

**Rules:**
- Never put app code in the project root
- Never mix concerns across service folders
- One `requirements.txt` per service, not one global
- All migrations are numbered: `001_`, `002_` — never edit an existing migration

---

## 2. Python Naming

```python
# Files: snake_case
rag_engine.py
embed_chunks.py

# Classes: PascalCase
class AdvisoryService:

# Functions / variables: snake_case
def retrieve_chunks(query: str) -> list[RetrievedChunk]:

# Constants: UPPER_SNAKE_CASE
TOP_K_DEFAULT = 6
EMBED_MODEL_NAME = "BAAI/bge-m3"

# Private helpers: leading underscore
def _format_context(chunks: list) -> str:
```

**Type hints are mandatory on all function signatures.**

---

## 3. FastAPI Conventions

```python
# Route naming: lowercase with hyphens (not underscores)
@app.post("/batch-predict")     # ✅
@app.post("/batch_predict")     # ❌

# Pydantic models: suffix with Request / Response
class AskRequest(BaseModel): ...
class AskResponse(BaseModel): ...

# Tags on every endpoint
@app.post("/ask", tags=["Advisory"])

# Never return raw dicts from endpoints — always use a response model
@app.get("/health")
async def health() -> dict[str, Any]:  # ✅ (dict is acceptable for health)

@app.post("/ask", response_model=AskResponse)  # ✅ typed endpoints

# Always use lifespan for startup/shutdown — not @app.on_event
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
```

---

## 4. Database Conventions

```sql
-- Table names: plural, snake_case
crops, fertilizers, chat_sessions

-- Column names: snake_case
english_name, created_at, soil_ph_min

-- PK on transactional tables: UUID
farmer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4()

-- PK on reference/lookup tables: SERIAL
crop_id SERIAL PRIMARY KEY

-- Timestamps: always TIMESTAMPTZ (not TIMESTAMP)
created_at TIMESTAMPTZ DEFAULT NOW()

-- Suffixes
_id    → foreign key or primary key
_at    → timestamp
_pct   → percentage
_mm    → millimetres
_ha    → hectares
_inr   → Indian Rupees
_kg    → kilograms
```

**Migration rules:**
- Every schema change = new numbered migration file
- Never ALTER existing migration files
- Always test rollback before merging

---

## 5. Git Commit Format

```
<type>(<scope>): <short summary>

Types: feat | fix | refactor | test | docs | chore | perf | ci
Scope: conversation | decision | knowledge | tools | shared | auth | disease | db | rag | flutter | devops | agents

Examples:
feat(advisory): add multi-turn conversation support
fix(rag): handle empty ChromaDB collection gracefully
docs(db): update ER diagram with satellite tables
test(disease): add batch predict endpoint tests
chore(devops): pin chromadb version to 0.5.3
```

---

## 6. API Response Standards

Every API response must include:
```json
{
  "status": "ok",          // always present on errors too
  "timestamp": "ISO-8601", // UTC
  "data": { ... },         // actual payload
  "error": null            // null on success, string on failure
}
```

Exception: endpoints with `response_model=` can return the model directly.

---

## 7. Error Handling

```python
# ✅ Correct — specific exception types
except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
except RuntimeError as exc:
    raise HTTPException(status_code=503, detail=str(exc)) from exc

# ❌ Wrong — swallowing exceptions
except Exception:
    return {"error": "something went wrong"}
```

Always re-raise with `from exc` to preserve traceback.

---

## 8. Security Rules

| Rule | Detail |
|------|--------|
| No raw Aadhaar | Always SHA-256 hash before storing |
| No secrets in code | Use `.env` / environment variables only |
| No `SELECT *` | Always name columns explicitly |
| SQL parameters | Never use f-strings in SQL — use `%s` or SQLAlchemy params |
| File uploads | Always validate MIME type + size before processing |
| CORS | `allow_origins=["*"]` is OK in dev; restrict in production |

---

## 9. Language Support

All farmer-facing content must:
1. Be available in **Tamil and English**
2. Use `language: "Tamil" | "English"` in request/response schemas
3. Store Tamil text as Unicode (UTF-8 encoded)
4. Tamil column names follow the pattern `*_tamil_name`

---

## 10. Testing Requirements

| Type | Requirement | Tool |
|------|-------------|------|
| Unit | All utility functions | pytest |
| Integration | Every API endpoint | pytest + httpx |
| DB | Migrations + seed data | pytest + psycopg2 |
| ML | Model loading + inference | pytest |
| Coverage | Minimum 70% per service | pytest-cov |

Test files mirror source structure:
```
backend/decision/graph/intent.py       →  tests/decision/test_intent_graph.py
backend/decision/graph/verification.py →  tests/decision/test_verification_graph.py
backend/knowledge/rag/engine.py        →  tests/knowledge/test_rag_engine.py
backend/conversation/main.py           →  tests/conversation/test_main.py
backend/auth/main.py                   →  tests/api/auth/test_main.py
```

---

## 11. Documentation Requirements

Every completed feature must have:
- [ ] Updated `README.md` (if user-facing)
- [ ] Docstring on every public function (one line max — WHY not WHAT)
- [ ] Endpoint tagged in FastAPI (`tags=["..."]`)
- [ ] Database columns described in `docs/data_dictionary.md` if new table
- [ ] `CHANGELOG.md` entry

---

## 12. Dependency Policy

- Pin versions in `requirements.txt` (e.g. `fastapi>=0.111.0,<0.120.0`)
- No direct `pip install` in production Dockerfiles — use requirements file
- No unused imports — enforced by `ruff`
- Python minimum: 3.11
- No `requirements.txt` at project root — each service has its own
