# ADR-003 — Use ChromaDB for Vector Storage

**Date:** 2026-06-20
**Status:** ACCEPTED
**Deciders:** Master Agent, Solution Architect Agent

---

## Context
UZHAVAN AI needs a vector database for semantic search over ~50,000 TNAU knowledge chunks. Requirements:
1. Works embedded (no external service for local/offline use)
2. Python-native (FastAPI backend)
3. Persistent storage
4. Metadata filtering (by crop, category, language)
5. Simple deployment (no Kubernetes needed)

## Decision
Use **ChromaDB** with `PersistentClient` (file-based).

## Rationale
ChromaDB:
- Embeds directly in the Python process — no separate service
- Persistent via local filesystem (mounted volume in Docker)
- Metadata filtering with `where=` clauses
- Active development, good Python ecosystem
- Cosine similarity space supported

## Alternatives Considered

| Option | Pros | Cons | Rejected Because |
|--------|------|------|-----------------|
| Qdrant | Production-grade; fast | Requires separate service; more complex setup | Too heavy for current scale |
| Pinecone | Managed; scalable | Cloud-only; cost; no offline | No offline support |
| pgvector | Single database; SQL joins | PostgreSQL extension; slower for pure vector search | Not specialized enough |
| FAISS | Very fast | No metadata filtering; manual persistence | No metadata filtering |
| Weaviate | Full-featured | Heavy; separate service; overkill | Too complex for current scale |

## Consequences

**Positive:**
- Zero additional infrastructure
- Works offline
- Fast enough for current scale (~50k chunks)

**Negative:**
- ChromaDB is not designed for >10M vectors
- Multi-process writes require careful management (one writer at a time)
- Less battle-tested than Qdrant at scale

**Risks:**
- If TNAU corpus grows to millions of chunks, migrate to Qdrant
- Mitigation: `rag_engine.py` abstracts ChromaDB — swap underlying DB without changing API

## Review Date
Reconsider if chunk count exceeds 500k or if concurrent write performance becomes an issue.
