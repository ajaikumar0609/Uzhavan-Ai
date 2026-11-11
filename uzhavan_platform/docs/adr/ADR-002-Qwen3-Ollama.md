# ADR-002 — Use Qwen3 via Ollama as Primary Local LLM

**Date:** 2026-06-20
**Status:** ACCEPTED
**Deciders:** Master Agent, Solution Architect Agent

---

## Context
UZHAVAN AI needs an LLM that:
1. Works offline (rural Tamil Nadu has unreliable internet)
2. Supports Tamil language
3. Can run on a modest server (8 GB RAM)
4. Is free to use (no per-token cost for local deployment)
5. Is good enough for agricultural advisory within a RAG context

## Decision
Use **Qwen3 8B via Ollama** as the local/offline LLM.
Use **Claude API (claude-sonnet-4-6)** as the cloud fallback for better responses.

## Rationale
Qwen3 8B:
- Strong multilingual performance including Tamil and regional Indian languages
- 8B fits in 6 GB VRAM / 8 GB RAM (Q4 quantized via Ollama)
- Ollama makes local deployment trivial (one command)
- Free — no API cost for local inference

Claude API:
- Better reasoning quality for complex advisory
- Used when internet is available and higher quality matters

The `LLM_PROVIDER` env var switches between them — no code changes needed.

## Alternatives Considered

| Option | Pros | Cons | Rejected Because |
|--------|------|------|-----------------|
| GPT-4 (OpenAI) | High quality | $$$; no offline; no Tamil strength | Cost + no offline |
| Llama 3.1 8B | Free; good English | Weak Tamil | Tamil is primary language |
| Mistral 7B | Fast; good | Weak Tamil | Tamil is primary language |
| Gemma 2 9B | Google; good multilingual | Ollama support less mature | Less tested |
| Claude only | Best quality | No offline; per-token cost at scale | Offline requirement |

## Consequences

**Positive:**
- True offline operation possible
- No recurring LLM cost for local deployment
- Easy model swap via env var

**Negative:**
- Qwen3 8B is slower than API LLMs (2-10s per response on CPU)
- Quality gap between Qwen3 and Claude on complex queries
- Requires ~6 GB disk for model weights

**Risks:**
- Qwen3 may produce incorrect Tamil in rare cases — mitigated by RAG context
- Ollama service must be running — health check required before advisory calls

## Review Date
Reconsider if a smaller (<4B) model achieves comparable Tamil quality (check every 6 months).
