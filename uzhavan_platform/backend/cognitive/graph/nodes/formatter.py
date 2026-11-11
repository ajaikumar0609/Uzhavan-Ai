"""
Formatter Node

Input:  raw_llm_response, evidence, intent, context, grounding/safety flags
Output: final_response (ResponseObject)

One job: produce a structured ResponseObject from the LLM response and evidence.
Handles both normal responses and Tamil fallback cases.
"""
from __future__ import annotations

import logging
from typing import Any

from backend.cognitive.graph.nodes.evidence_fusion import retrieved_chunks
from backend.cognitive.graph.nodes.llm_node import fallback_for
from backend.cognitive.models.node_context import EvidenceBundle
from backend.cognitive.observability import observe
from backend.cognitive.voice.spoken_planner import plan_spoken_response
from backend.shared.models.citation import SourceCitation
from backend.shared.models.response import ResponseObject


# (Tamil, English) prefixes; index with `language == "English"`.
_GENERAL_GUIDANCE_LABEL = (
    "பொது வழிகாட்டுதல் (TNAU ஆதாரம் இல்லாமல்): ",
    "General guidance (not from TNAU sources): ",
)


def _chunk_key(source: str, title: str, url: str | None) -> tuple[str, str, str]:
    return (source or "", title or "", url or "")


def filter_to_retrieved(sources: list, tool_results: list) -> list:
    """FP-015 guard: keep only sources that match a TNAU/RAG chunk actually retrieved in this
    turn (same source, title and url). Anything else — synthesized titles, tool citations,
    invented URLs — is dropped."""
    allowed = {_chunk_key(c.source, c.title, c.url) for c in retrieved_chunks(tool_results)}
    return [s for s in sources if _chunk_key(s.source, s.title, getattr(s, "url", None)) in allowed]


def _citations_to_sources(evidence: EvidenceBundle, tool_results: list) -> list[SourceCitation]:
    sources = [
        SourceCitation(
            source=c.source,
            title=c.title,
            excerpt=c.excerpt,
            confidence=c.confidence,
            page=c.page,
            url=c.url,
            category=c.category,
        )
        for c in evidence.retrieved_chunks[:6]
    ]
    return filter_to_retrieved(sources, tool_results)


def _extract_recommendations(response: str) -> list[str]:
    recommendations: list[str] = []
    for line in response.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "• ", "* ", "→ ", "1.", "2.", "3.")):
            content = stripped.lstrip("-•*→0123456789. ").strip()
            if len(content) > 10:
                recommendations.append(content)
    return recommendations[:5]


async def formatter(state: dict[str, Any]) -> dict[str, Any]:
    with observe("formatter", state):
        raw_response: str = state.get("raw_llm_response", "")
        evidence: EvidenceBundle | None = state.get("evidence")
        intent: str = state.get("intent", "advisory")
        context = state["context"]

        grounding_passed: bool = state.get("grounding_passed", False)
        safety_passed: bool = state.get("safety_passed", True)
        is_fallback: bool = state.get("is_fallback", False)
        grounding_failures: list[str] = state.get("grounding_failures", [])
        safety_failures: list[str] = state.get("safety_failures", [])

        language = context.system.language or context.farmer.language or "Tamil"
        use_fallback = is_fallback or not grounding_passed or not safety_passed or not (raw_response or "").strip()
        if use_fallback:
            logging.getLogger("uzhavan.formatter").warning(
                "Formatter fallback triggered: is_fallback=%s, grounding_passed=%s (failures=%s), safety_passed=%s (failures=%s), raw_empty=%s, raw_preview=%r",
                is_fallback, grounding_passed, grounding_failures, safety_passed, safety_failures, not (raw_response or "").strip(), (raw_response or "")[:100]
            )
        answer = fallback_for(language) if use_fallback else raw_response.strip()
        grounding_mode: str = "" if use_fallback else str(state.get("grounding_mode", "") or "")
        # Zero-cost local-first policy: an answer without verified TNAU/live evidence is labelled,
        # never presented as sourced.
        if grounding_mode in ("general_guidance", "safety_critical_unverified"):
            answer = _GENERAL_GUIDANCE_LABEL[language == "English"] + answer

        warnings: list[str] = []
        if grounding_failures:
            warnings.append(f"Grounding: {'; '.join(grounding_failures)}")
        if safety_failures:
            warnings.append(f"Safety: {'; '.join(safety_failures)}")
        if evidence and evidence.conflict_warnings:
            warnings.extend(evidence.conflict_warnings)

        confidence = evidence.overall_confidence if evidence else 0.0
        # Contract §9: sources only when TNAU/RAG chunks were actually retrieved and used.
        sources = _citations_to_sources(evidence, state.get("tool_results") or []) if evidence and not use_fallback else []
        tools_used = evidence.tools_used if evidence else []
        recommendations = _extract_recommendations(answer) if not use_fallback else []

        spoken_text = plan_spoken_response(answer, language=language)

        final_response = ResponseObject(
            answer=answer,
            spoken_text=spoken_text,
            language=language,
            intent=intent,
            confidence=confidence,
            sources=sources,
            tools_used=tools_used,
            recommendations=recommendations,
            warnings=warnings,
            is_fallback=use_fallback,
            # "grounded" now means evidence-backed (verified TNAU chunks or live tool data), not
            # merely "the LLM returned text". General guidance is NOT grounded.
            grounded=(not use_fallback) and grounding_mode in ("grounded_verified", "grounded_live_data"),
            grounding_mode=grounding_mode,
        )

        output = {"final_response": final_response, "is_fallback": use_fallback}
    output["trace"] = state.get("trace", [])
    return output
