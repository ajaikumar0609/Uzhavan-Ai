"""
UZHAVAN AI — RAG Engine
=======================
Wraps ChromaDB for semantic search over TNAU knowledge chunks.
Supports multilingual retrieval (Tamil + English).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger("rag_engine")

CHROMA_PATH      = os.getenv("CHROMA_PATH", str(Path(__file__).parent.parent.parent / "rag" / "chroma"))
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "BAAI/bge-m3")
COLLECTION_NAME  = "tnau_knowledge"
TOP_K_DEFAULT    = 6


@dataclass
class RetrievedChunk:
    chunk_id:    str
    content:     str
    category:    str
    crop:        str
    source_url:  str
    title:       str
    score:       float   # cosine similarity (0-1)


_chroma_client = None
_collection    = None
_embedder      = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        log.info(f"Loading embedding model: {EMBED_MODEL_NAME}")
        _embedder = SentenceTransformer(EMBED_MODEL_NAME)
    return _embedder


def _get_collection():
    global _chroma_client, _collection
    if _collection is None:
        import chromadb
        Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        log.info(f"ChromaDB collection '{COLLECTION_NAME}' — {_collection.count()} chunks")
    return _collection


def embed_text(text: str) -> list[float]:
    return _get_embedder().encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    return _get_embedder().encode(texts, normalize_embeddings=True, batch_size=32).tolist()


def retrieve(
    query: str,
    top_k: int = TOP_K_DEFAULT,
    crop_filter: str | None = None,
    category_filter: str | None = None,
) -> list[RetrievedChunk]:
    collection = _get_collection()
    if collection.count() == 0:
        log.warning("ChromaDB collection is empty — run embed_chunks.py first")
        return []

    query_vec = embed_text(query)

    where: dict[str, Any] = {}
    if crop_filter and category_filter:
        where = {"$and": [{"crop": {"$eq": crop_filter}}, {"category": {"$eq": category_filter}}]}
    elif crop_filter:
        where = {"crop": {"$eq": crop_filter}}
    elif category_filter:
        where = {"category": {"$eq": category_filter}}

    results = collection.query(
        query_embeddings=[query_vec],
        n_results=min(top_k, max(1, collection.count())),
        where=where if where else None,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    docs       = results.get("documents", [[]])[0]
    metas      = results.get("metadatas", [[]])[0]
    distances  = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, distances):
        chunks.append(RetrievedChunk(
            chunk_id   = meta.get("chunk_id", ""),
            content    = doc,
            category   = meta.get("category", ""),
            crop       = meta.get("crop", ""),
            source_url = meta.get("source_url", ""),
            title      = meta.get("title", ""),
            score      = round(1.0 - float(dist), 4),
        ))
    return chunks


def collection_stats() -> dict:
    try:
        col = _get_collection()
        return {
            "collection": COLLECTION_NAME,
            "total_chunks": col.count(),
            "chroma_path": CHROMA_PATH,
            "embed_model": EMBED_MODEL_NAME,
        }
    except Exception as exc:
        return {"error": str(exc)}
