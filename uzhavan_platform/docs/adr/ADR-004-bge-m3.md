# ADR-004 — Use BAAI/bge-m3 for Embeddings

**Date:** 2026-06-20
**Status:** ACCEPTED
**Deciders:** Master Agent, Solution Architect Agent

---

## Context
UZHAVAN AI must embed both English TNAU documents and Tamil farmer queries in the same vector space for meaningful semantic search.

## Decision
Use **BAAI/bge-m3** as the embedding model.

## Rationale
bge-m3:
- Multilingual: 100+ languages including Tamil, English, Hindi
- Same model encodes both document and query — aligned vector space
- 1024-dimensional embeddings — good quality/size trade-off
- Runs on CPU (important for servers without GPU)
- Open-source, no API cost

## Alternatives Considered

| Option | Pros | Cons | Rejected Because |
|--------|------|------|-----------------|
| all-MiniLM-L6-v2 | Fast; 90 MB | English only; poor Tamil | Tamil is primary language |
| text-embedding-3-small (OpenAI) | High quality | Cloud API cost; no offline | Offline requirement |
| LaBSE (Google) | Good multilingual | Older; lower quality than bge-m3 | Outperformed by bge-m3 |
| paraphrase-multilingual-mpnet | Good multilingual | Slower; larger | bge-m3 is better quality |

## Consequences

**Positive:**
- Tamil farmer queries match English TNAU documents correctly
- One model — no separate query/document encoders
- 1.1 GB model — acceptable for server deployment

**Negative:**
- ~1.1 GB download on first run
- Slower than MiniLM (~200ms vs ~50ms per query on CPU)
- 1024-dim vectors take more ChromaDB storage than 384-dim

**Risks:**
- First startup slow if model not pre-downloaded in Docker image
- Mitigation: Dockerfile.advisory pre-downloads model during build

## Review Date
Reconsider if Tamil retrieval quality issues emerge in testing.
