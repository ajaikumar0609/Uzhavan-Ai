from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from backend.shared.models.citation import Citation
from backend.shared.models.service import ServiceMetadata, ServiceResult

_CHROMA_PATH = os.getenv("CHROMA_PATH", "./rag/chroma")
_COLLECTION_NAME = "tnau_knowledge"
_EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-m3")
_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.35"))


def _passes_lexical_gate(text: str, terms: list[str]) -> bool:
    """>= min(2, len(terms)) of the question's content terms must appear in the chunk."""
    low = (text or "").lower()
    hits = sum(1 for t in terms if t and t in low)
    return hits >= min(2, len(terms))


class RAGService:
    """
    ChromaDB retrieval engine.
    Responsibilities: embed(), retrieve(), rerank(), stats(). Nothing else.
    Key invariant: always returns empty list if collection is empty or score threshold not met.
    Never signals the caller to guess — empty list means "no knowledge available."
    """

    VERSION = "1.0"

    def __init__(self) -> None:
        self._collection = None
        self._embed_model = None
        self._initialized = False

    def _lazy_init(self) -> bool:
        """Lazy initialization — ChromaDB not loaded until first retrieve() call."""
        if self._initialized:
            return self._collection is not None
        self._initialized = True
        try:
            import chromadb
            from chromadb.config import Settings
            client = chromadb.PersistentClient(path=_CHROMA_PATH, settings=Settings(anonymized_telemetry=False))
            self._collection = client.get_or_create_collection(_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
            return True
        except Exception:
            return False

    def _lazy_embed(self):
        if self._embed_model is not None:
            return self._embed_model
        try:
            from sentence_transformers import SentenceTransformer
            self._embed_model = SentenceTransformer(_EMBED_MODEL)
            return self._embed_model
        except Exception:
            return None

    async def get(self, key: str, **kwargs) -> ServiceResult[Citation | None]:
        results = await self.retrieve(key, top_k=1)
        data = results.data[0] if results.data else None
        return ServiceResult(data=data, metadata=results.metadata)

    async def search(self, query: str, **kwargs) -> ServiceResult[list[Citation]]:
        top_k = kwargs.get("top_k", 6)
        filters = kwargs.get("filters")
        return await self.retrieve(query, top_k=top_k, filters=filters)

    async def retrieve(
        self,
        query: str,
        top_k: int = 6,
        score_threshold: float = _SCORE_THRESHOLD,
        filters: dict | None = None,
        must_match_terms: list[str] | None = None,
    ) -> ServiceResult[list[Citation]]:
        """Semantic search. `must_match_terms` (optional) adds a lexical relevance gate: a chunk is
        kept only if its full text contains at least min(2, len(terms)) of the terms (prefix match). bge-m3 cosine alone
        gives ~0.45-0.5 even for unrelated chunks in this small corpus, so without the gate
        unrelated pages ("Site Map") were returned as citations."""
        start_ns = time.monotonic_ns()

        if not self._lazy_init():
            return ServiceResult(data=[], metadata=ServiceMetadata(source="chromadb", version=self.VERSION, latency_ms=self._ms(start_ns)))

        model = self._lazy_embed()
        if model is None:
            return ServiceResult(data=[], metadata=ServiceMetadata(source="chromadb-no-model", version=self.VERSION, latency_ms=self._ms(start_ns)))

        embedding = model.encode(query).tolist()
        where = filters or None
        raw = self._collection.query(
            query_embeddings=[embedding],
            n_results=(top_k * 8 if must_match_terms else top_k),  # wider pool for the lexical gate
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        citations: list[Citation] = []
        docs = raw.get("documents", [[]])[0]
        metas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, distances):
            cosine_similarity = 1.0 - dist  # chromadb cosine returns distance, not similarity
            if cosine_similarity < score_threshold:
                continue
            if must_match_terms and not _passes_lexical_gate(doc, must_match_terms):
                continue
            citations.append(Citation(
                source=meta.get("source", "TNAU"),
                title=meta.get("title", "TNAU Knowledge Base"),
                excerpt=doc[:300],
                confidence=round(cosine_similarity, 3),
                page=meta.get("page"),
                category="rag",
            ))

        citations = citations[:top_k]
        return ServiceResult(
            data=citations,
            metadata=ServiceMetadata(source="chromadb", version=self.VERSION, latency_ms=self._ms(start_ns)),
        )

    async def stats(self) -> dict:
        if not self._lazy_init() or self._collection is None:
            return {"status": "unavailable", "chunk_count": 0}
        return {"status": "ok", "chunk_count": self._collection.count(), "collection": _COLLECTION_NAME, "model": _EMBED_MODEL}

    async def health(self) -> bool:
        if not self._lazy_init():
            return False
        return self._collection is not None and self._collection.count() > 0

    def version(self) -> str:
        return self.VERSION

    async def last_updated(self) -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _ms(start_ns: int) -> int:
        return int((time.monotonic_ns() - start_ns) / 1_000_000)
