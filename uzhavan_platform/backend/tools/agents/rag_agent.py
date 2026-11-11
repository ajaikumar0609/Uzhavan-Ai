from __future__ import annotations

import time
from typing import Any

from backend.knowledge.rag.engine import RAGService
from backend.shared.agents.base import BaseDomainAgent
from backend.shared.models.citation import Citation
from backend.shared.models.context import ConversationContext
from backend.shared.models.tool import AgentManifest, ToolCapability, ToolResult


# App crop id -> crop names used in the TNAU knowledge-base metadata.
_CROP_ALIASES: dict[str, list[str]] = {
    "paddy": ["Rice", "Paddy"],
    "rice": ["Rice", "Paddy"],
    "maize": ["Corn", "Maize"],
    "corn": ["Corn", "Maize"],
    "black_gram": ["Blackgram", "Black Gram"],
    "blackgram": ["Blackgram", "Black Gram"],
    "red_gram": ["Redgram"],
    "redgram": ["Redgram"],
    "chilli": ["Chilli"],
    "tapioca": ["Tapioca"],
}


_STOPWORDS = frozenset("""
about above after again also among because been before being between both can could does doing
during each explain from have having here how importance important improve into just like make
many more most much need needs only other over please should some such tell than that their them
then there these they this those through turning under until upon very want what when where
which while who whom why will with would your you are the and for not but its was were get gets
give help know show use used using way ways does did has had
""".split())


def _lexical_terms(query: str) -> list[str] | None:
    """Content-word prefixes (lower-case, >=4 letters) for the lexical relevance gate.

    Only for Latin-script queries: the knowledge base is English, and for Tamil queries a
    lexical gate would reject everything (cross-lingual match is left to the embedding).
    Returns None (no gate) when there are no usable terms.
    """
    import re
    q = query or ""
    if re.search(r"[\u0b80-\u0bff]", q):
        return None
    words = [w for w in re.findall(r"[a-z]{3,}", q.lower()) if w not in _STOPWORDS]
    terms = sorted({(w[:6] if len(w) > 6 else w) for w in words if len(w) >= 3})
    return terms or None


def _citations_of(result: Any) -> list[Citation]:
    """RAGService.retrieve() returns a ServiceResult; the agent works on its `.data` list.

    (Before this unwrap, iterating the ServiceResult raised
    "'tuple' object has no attribute 'confidence'", which the agent's except-clause hid,
    so RAG silently contributed nothing to any answer.)
    """
    data = getattr(result, "data", result)
    return list(data) if data else []


class RAGAgent(BaseDomainAgent):
    """
    Owns all TNAU knowledge retrieval and agricultural document reasoning.
    RAGService handles ChromaDB; this agent handles query construction and result interpretation.
    """

    VERSION = "1.0"
    _CAPABILITIES = ["search_tnau", "advisory", "summarize", "retrieve_guidelines"]

    def __init__(self, service: RAGService | None = None) -> None:
        self._service = service or RAGService()

    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_name="rag",
            version=self.VERSION,
            description="Semantic search over TNAU crop guides and cultivation manuals (Tamil + English)",
            avg_latency_ms=600,
            typical_confidence=0.80,
            feature_flag=None,  # always active — RAG is core
            dependencies=["chromadb", "bge-m3"],
            capabilities=[
                ToolCapability(name="search_tnau", description="Semantic search in TNAU knowledge base for any farming question", avg_latency_ms=600),
                ToolCapability(name="advisory", description="Alias of search_tnau used by the planner (FP-015)", avg_latency_ms=600),
                ToolCapability(name="summarize", description="Summarize retrieved TNAU guidance into actionable points", avg_latency_ms=100),
                ToolCapability(name="retrieve_guidelines", description="Retrieve TNAU cultivation guidelines for a specific crop and topic", avg_latency_ms=600),
            ],
        )

    def can_handle(self, capability_name: str) -> bool:
        parts = capability_name.split(".", 1)
        return len(parts) == 2 and parts[0] == "rag" and parts[1] in self._CAPABILITIES

    async def execute(
        self, capability_name: str, context: ConversationContext, params: dict[str, Any]
    ) -> ToolResult:
        start_ns = time.monotonic_ns()
        _, method = capability_name.split(".", 1)
        try:
            if method in ("search_tnau", "advisory"):
                return await self._search_tnau(start_ns, context, params)
            elif method == "summarize":
                return self._summarize(start_ns, params.get("chunks", []))
            elif method == "retrieve_guidelines":
                return await self._retrieve_guidelines(start_ns, context, params)
            else:
                return self._timed_result(capability_name, start_ns, False, error=f"Unknown method: {method}")
        except NotImplementedError:
            return self._timed_result(capability_name, start_ns, False, error="RAG service not yet implemented (Phase D) — ChromaDB not populated")
        except Exception as exc:
            return self._timed_result(capability_name, start_ns, False, error=str(exc))

    async def _search_tnau(self, start_ns: int, context: ConversationContext, params: dict[str, Any]) -> ToolResult:
        query = params.get("query") or context.current_question
        if not query:
            return self._timed_result("rag.search_tnau", start_ns, False, error="query required")

        # Enrich query with farmer context for better retrieval
        enriched_query = self._enrich_query(query, context)
        filters = self._build_filters(context, params)

        terms = _lexical_terms(query)
        # English queries: lexical gate + stricter cosine (0.45), since unrelated chunks score
        # 0.45-0.5 against anything. Tamil queries use 0.48, no lexical gate (cross-lingual: on 4 sampled queries relevant ones scored 0.50-0.56, unrelated 0.39-0.43; small sample, recalibrate with a real benchmark).
        citations = _citations_of(
            await self._service.retrieve(
                query=enriched_query, top_k=6, score_threshold=(0.45 if terms else 0.48), filters=filters,
                must_match_terms=terms,
            )
        )

        if not citations:
            # Critical: return empty list, never signal the LLM to guess
            return self._timed_result("rag.search_tnau", start_ns, True, data=[], citations=[], confidence=0.0)

        overall_confidence = sum(c.confidence for c in citations) / len(citations)
        return self._timed_result("rag.search_tnau", start_ns, True, data=citations, citations=citations, confidence=overall_confidence)

    def _summarize(self, start_ns: int, chunks: list[Citation]) -> ToolResult:
        """
        Structural summarization — extracts key points without LLM.
        LLM will produce the final Tamil narrative; this provides structure.
        """
        if not chunks:
            return self._timed_result("rag.summarize", start_ns, False, error="No chunks to summarize")
        key_points = [c.excerpt[:200].strip() for c in chunks[:4]]
        data = {
            "key_points": key_points,
            "sources": [c.source for c in chunks],
            "chunk_count": len(chunks),
        }
        return self._timed_result("rag.summarize", start_ns, True, data=data, citations=chunks, confidence=0.80)

    async def _retrieve_guidelines(self, start_ns: int, context: ConversationContext, params: dict[str, Any]) -> ToolResult:
        """Retrieve cultivation guidelines for a specific crop + topic combination."""
        crop = params.get("crop") or (context.farm.crop if context.farm else "")
        topic = params.get("topic", "cultivation")
        query = f"{crop} {topic} TNAU guidelines cultivation practices"
        citations = _citations_of(await self._service.retrieve(query=query, top_k=4, score_threshold=0.35))
        if not citations:
            return self._timed_result("rag.retrieve_guidelines", start_ns, True, data=[], confidence=0.0)
        confidence = sum(c.confidence for c in citations) / len(citations)
        return self._timed_result("rag.retrieve_guidelines", start_ns, True, data=citations, citations=citations, confidence=confidence)

    # ── Query enrichment ─────────────────────────────────────────────────────

    def _enrich_query(self, query: str, context: ConversationContext) -> str:
        """
        Add crop and district context to improve bge-m3 retrieval.
        bge-m3 handles Tamil + English in the same vector space — no translation needed.
        """
        parts = [query]
        if context.farm and context.farm.crop:
            parts.append(context.farm.crop)
        if context.farmer.district:
            parts.append(context.farmer.district)
        return " ".join(parts)

    def _build_filters(self, context: ConversationContext, params: dict[str, Any]) -> dict | None:
        """Build ChromaDB metadata filters from context. None = no filter."""
        filters: dict[str, Any] = {}
        crop = params.get("crop") or (context.farm.crop if context.farm else None)
        if crop:
            # The knowledge base stores capitalised TNAU crop names ("Rice", "Corn"), not app
            # crop ids ("paddy", "maize"); a lower-case equality filter matched nothing. Match any
            # alias, plus the "General" chunks, which carry crop-independent agronomy.
            key = str(crop).strip().lower()
            names = list(_CROP_ALIASES.get(key, [key.title()]))
            filters["crop"] = {"$in": names + ["General"]}
        return filters if filters else None


    async def health(self) -> bool:
        return await self._service.health()
