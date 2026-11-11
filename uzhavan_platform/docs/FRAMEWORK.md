# UZHAVAN AI Development Framework v1.0

> Every feature must pass through this workflow in order. No exceptions.

## Delivery Pipeline

```
Product Vision
      │
      ▼
Roadmap
      │
      ▼
Phase
      │
      ▼
Milestone
      │
      ▼
Feature Pack (FP)          ← atomic delivery unit; 15 required sections
      │
      ▼
Epic
      │
      ▼
User Story
      │
      ▼
Tasks
      │
      ▼
Sub-Agent Assignment
      │
      ▼
Implementation             ← first line of code written here
      │
      ▼
Testing
      │
      ▼
Security Review
      │
      ▼
Performance Review
      │
      ▼
Documentation
      │
      ▼
Standards Review           ← merge gate
      │
      ▼
Merge
      │
      ▼
Release
```

## Product Principles

Every feature must satisfy all seven:

| Principle | Definition |
|-----------|-----------|
| Explainable | Farmer understands why they received this advice |
| Grounded | Every answer cites a TNAU / official source |
| Tamil-first | Tamil is the default language, not an afterthought |
| Offline-friendly | Core flows work without internet |
| Fast | Result delivered in < 5 seconds on Redmi 10 |
| Modular | Each service deploys independently |
| Production-ready | No dev shortcuts in merged code |
| Secure | Passes Security Agent checklist |

## Feature Pack Template (15 Sections)

Every FP must contain exactly these sections before any code is written:

1. Overview
2. Business Goal
3. User Story
4. Acceptance Criteria
5. UI Design
6. API Contract
7. Database Changes
8. AI Changes
9. Agent Responsibilities
10. Testing
11. Security
12. Performance
13. Documentation
14. Demo Checklist
15. Release Notes

## Release Gates (10 sign-offs required)

| Gate | Owner |
|------|-------|
| Planning | Planning Agent |
| Architecture | Architecture Agent |
| Backend | Backend Agent |
| Flutter | Flutter Agent |
| AI | AI Agent |
| Tests | Testing Agent |
| Security | Security Agent |
| Performance | DevOps Agent |
| Documentation | Documentation Agent |
| Standards | Standards Agent |

**Master Agent signs off last. No merge without all 10.**

## Agent Roster

### Permanent (18)

| Agent | Responsibility |
|-------|---------------|
| Master | Coordination, review, delivery, planning. Never writes code. |
| Planning | ROADMAP, SPRINT, TODO documents |
| Product | UX, farmer journey, prioritization |
| Architecture | APIs, DB, microservices, event flow |
| Backend | FastAPI services |
| Flutter | Mobile app |
| Database | PostgreSQL + PostGIS |
| AI | LangGraph, LangChain, Ollama |
| RAG | Embedding, chunking, retrieval |
| Vision | Disease detection |
| Satellite | SICKLE data |
| Weather | Open-Meteo |
| Market | AGMARKNET |
| Testing | pytest, integration, E2E |
| Security | Prompt injection, JWT, uploads, SQL, secrets |
| DevOps | Docker, Compose, CI/CD |
| Documentation | Everything |
| Standards | Merge gate |

### Temporary
Created per-need, deleted after completion. Examples: Dataset Migration, Crawler, Performance, UI Animation, Bug Fix, Release.

## Sprint Strategy

- 2-week sprints
- Maximum 3 Feature Packs per sprint
- Every FP must be independently deployable at sprint end

## Definition of Done

A feature is COMPLETE only when all are true:

- [ ] Business requirements met
- [ ] Acceptance criteria pass
- [ ] Unit tests pass (≥ 70% coverage)
- [ ] Integration tests pass
- [ ] End-to-end flow works
- [ ] Security review passes
- [ ] Performance targets met
- [ ] API documentation updated
- [ ] Flutter UI connected
- [ ] Standards Agent approved
- [ ] Release notes written
