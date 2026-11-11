# UZHAVAN AI — Agent System

## How This Works

You (Product Owner) → tell Claude Master what to build.

Claude Master (CTO role) → never writes code. It:
1. Runs requirement analysis
2. Checks architecture impact
3. Breaks into tasks via Planning Agent
4. Assigns tasks to sub-agents
5. Reviews output via Standards Agent
6. Coordinates merge

---

## Permanent Agents

| Agent | Prompt | Domain |
|-------|--------|--------|
| Master | `master/master_prompt.md` | CTO — plan, review, delegate |
| Planning | `planning/planning_agent.md` | Tasks, sprints, milestones |
| Architecture | `architecture/architecture_agent.md` | APIs, folder structure, scalability |
| **Standards** ⭐ | `standards/standards_agent.md` | Naming, style, review gatekeeper |
| Backend | `backend/backend_agent.md` | FastAPI services |
| Flutter | `flutter/flutter_agent.md` | Mobile app |
| Database | `database/database_agent.md` | PostgreSQL + PostGIS |
| AI | `ai/ai_agent.md` | LangGraph, LLM orchestration |
| RAG | `rag/rag_agent.md` | ChromaDB, embeddings |
| Vision AI | `vision/vision_agent.md` | Disease detection |
| Satellite | `satellite/` | (future) SICKLE integration |
| Testing | `testing/testing_agent.md` | pytest, coverage |
| DevOps | `devops/devops_agent.md` | Docker, CI/CD |
| Documentation | `documentation/documentation_agent.md` | docs/, README |

---

## Temporary Agents

See `temporary/TEMPLATE.md`.
Create only when a one-off specialized task benefits from it.
**Retire after task completes** — delete the folder.

---

## Standards

`standards/STANDARDS.md` is the law.
Every sub-agent must read it before producing any code.
Standards Agent reviews every output before merge.

---

## Planning Documents

| File | Owner | Updated |
|------|-------|---------|
| `docs/ROADMAP.md` | Planning Agent | Per phase |
| `docs/SPRINT.md` | Planning Agent | Weekly |
| `docs/TODO.md` | Planning Agent | Continuously |

---

## SOP (every feature)

```
You say: "Build X"
         ↓
Master → reads agents/master/master_prompt.md
         ↓
Planning Agent → breaks into tasks
         ↓
Architecture Agent → checks impact
         ↓
Sub-agents → implement
         ↓
Testing Agent → writes tests
         ↓
Standards Agent → reviews all output
         ↓
Documentation Agent → updates docs
         ↓
Master → confirms done, updates SPRINT.md
```
