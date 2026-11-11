"""
UZHAVAN AI — Advisory RAG Service
===================================
FastAPI microservice for farmer advisory generation.

Tool-based orchestration: LLM never guesses — it calls specialized tools.

Endpoints:
  POST /ask              — main advisory Q&A (RAG + LLM)
  POST /search           — semantic search over TNAU knowledge (no LLM)
  GET  /knowledge/stats  — ChromaDB collection statistics
  GET  /health

Run:
  cp .env.example .env   # set ANTHROPIC_API_KEY or OLLAMA_HOST
  uvicorn main:app --host 0.0.0.0 --port 8002 --reload
"""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, AsyncIterator

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from llm_client import generate_advisory
from rag_engine import RetrievedChunk, collection_stats, retrieve

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("advisory")

TOP_K_RETRIEVAL  = int(os.getenv("TOP_K_RETRIEVAL", "6"))
MAX_HISTORY_MSGS = 10


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    stats = collection_stats()
    log.info(f"ChromaDB: {stats.get('total_chunks', 0)} chunks ready")
    yield
    log.info("Advisory service shutting down")


app = FastAPI(
    title="UZHAVAN AI — Advisory RAG Service",
    description="TNAU knowledge RAG + LLM advisory for Tamil Nadu farmers",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── SCHEMAS ──────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role:    str   # "user" | "assistant"
    content: str


class AskRequest(BaseModel):
    question:    str = Field(..., min_length=3, max_length=2000)
    language:    str = Field(default="English", description="'Tamil' or 'English'")
    crop:        str | None = Field(default=None, description="Filter retrieval by crop (optional)")
    category:    str | None = Field(default=None, description="Filter by knowledge category (optional)")
    history:     list[ChatMessage] = Field(default=[], max_length=MAX_HISTORY_MSGS,
                                           description="Prior conversation turns for multi-turn support")
    top_k:       int = Field(default=TOP_K_RETRIEVAL, ge=1, le=20)


class SourceChunk(BaseModel):
    title:      str
    category:   str
    crop:       str
    source_url: str
    score:      float
    excerpt:    str


class AskResponse(BaseModel):
    answer_id:    str
    answer:       str
    language:     str
    sources:      list[SourceChunk]
    sources_urls: list[str]
    chunks_used:  int
    timestamp:    str


class SearchRequest(BaseModel):
    query:    str = Field(..., min_length=2, max_length=500)
    top_k:    int = Field(default=8, ge=1, le=30)
    crop:     str | None = None
    category: str | None = None


class SearchResponse(BaseModel):
    query:   str
    results: list[SourceChunk]
    total:   int


# ─── TOOL LAYER ───────────────────────────────────────────────────────────────
# The LLM is NOT called without first retrieving context.
# Each advisory call: retrieve → validate → generate.

def _chunks_to_sources(chunks: list[RetrievedChunk]) -> list[SourceChunk]:
    return [
        SourceChunk(
            title      = c.title or "TNAU Knowledge Base",
            category   = c.category,
            crop       = c.crop,
            source_url = c.source_url,
            score      = c.score,
            excerpt    = c.content[:300] + ("..." if len(c.content) > 300 else ""),
        )
        for c in chunks
    ]


# ─── ENDPOINTS ────────────────────────────────────────────────────────────────

@app.post("/ask", response_model=AskResponse, tags=["Advisory"])
async def ask(req: AskRequest) -> AskResponse:
    """
    Main advisory endpoint.

    Flow:
    1. Embed the question
    2. Retrieve top-K TNAU knowledge chunks (RAG)
    3. If no chunks found, return honest "not found" message without hallucinating
    4. Pass chunks + question to LLM (Claude or Ollama/Qwen3)
    5. Return structured response with sources

    The LLM NEVER generates recommendations without retrieved context.
    """
    try:
        # Step 1 & 2 — Retrieve
        chunks = retrieve(
            query           = req.question,
            top_k           = req.top_k,
            crop_filter     = req.crop,
            category_filter = req.category,
        )

        # Step 3 — No-context guardrail
        if not chunks:
            fallback = (
                "உங்கள் கேள்விக்கு TNAU அறிவுத் தளத்தில் பதில் கிடைக்கவில்லை. "
                "உங்கள் வட்ட வேளாண் அலுவலர் (BAO) அல்லது நெருங்கிய கிருஷி விக்யான் கேந்திரத்தை "
                "(KVK) தொடர்பு கொள்ளவும்."
                if req.language == "Tamil" else
                "No relevant information found in the TNAU knowledge base for your question. "
                "Please contact your Block Agriculture Officer (BAO) or nearest Krishi Vigyan Kendra (KVK)."
            )
            return AskResponse(
                answer_id    = str(uuid.uuid4()),
                answer       = fallback,
                language     = req.language,
                sources      = [],
                sources_urls = [],
                chunks_used  = 0,
                timestamp    = datetime.now(UTC).isoformat(),
            )

        # Step 4 — Generate with context
        history = [{"role": m.role, "content": m.content} for m in req.history]
        answer, sources_urls = await generate_advisory(
            question              = req.question,
            chunks                = chunks,
            language              = req.language,
            conversation_history  = history,
        )

        return AskResponse(
            answer_id    = str(uuid.uuid4()),
            answer       = answer,
            language     = req.language,
            sources      = _chunks_to_sources(chunks),
            sources_urls = sources_urls,
            chunks_used  = len(chunks),
            timestamp    = datetime.now(UTC).isoformat(),
        )

    except Exception as exc:
        log.exception("Error in /ask")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search(req: SearchRequest) -> SearchResponse:
    """
    Semantic search over TNAU knowledge base — no LLM involved.
    Returns raw matching chunks with scores. Useful for debugging retrieval.
    """
    chunks = retrieve(
        query           = req.query,
        top_k           = req.top_k,
        crop_filter     = req.crop,
        category_filter = req.category,
    )
    return SearchResponse(
        query   = req.query,
        results = _chunks_to_sources(chunks),
        total   = len(chunks),
    )


@app.get("/knowledge/stats", tags=["Meta"])
async def knowledge_stats() -> dict[str, Any]:
    """ChromaDB collection statistics."""
    return collection_stats()


@app.get("/health", tags=["Meta"])
async def health() -> dict[str, Any]:
    stats = collection_stats()
    return {
        "status":     "ok",
        "chunks":     stats.get("total_chunks", 0),
        "embed_model": stats.get("embed_model", "unknown"),
        "timestamp":  datetime.now(UTC).isoformat(),
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
