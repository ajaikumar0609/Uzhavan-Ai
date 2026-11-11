"""
Evidence Fusion Engine Node

Input:  tool_results
Output: evidence (EvidenceBundle)

One job: merge, rank, deduplicate, and summarize all ToolResult data into a single EvidenceBundle.
Detects conflicts. Computes overall_confidence as weighted average of successful results.
Never calls LLM — pure data transformation.
"""
from __future__ import annotations

from typing import Any

from backend.cognitive.models.node_context import EvidenceBundle
from backend.cognitive.observability import observe
from backend.shared.models.citation import Citation
from backend.shared.models.tool import ToolResult


def _dedupe_citations(citations: list[Citation]) -> list[Citation]:
    seen: set[str] = set()
    unique: list[Citation] = []
    for c in sorted(citations, key=lambda x: -x.confidence):
        key = f"{c.source}:{c.title}"
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def _weighted_confidence(results: list[ToolResult]) -> float:
    successful = [r for r in results if r.success and r.has_data]
    if not successful:
        return 0.0
    return round(sum(r.confidence for r in successful) / len(successful), 3)


def _extract_summary(result: ToolResult) -> str | None:
    if not result.has_data:
        return None
    data = result.data
    if hasattr(data, "current") and data.current:
        c = data.current
        temp = c.temperature_c if c.temperature_c is not None else c.temp_max_c
        return f"{data.district}: {c.description or 'Weather'}, temp {temp}°C, rain {c.rain_mm or 0}mm, humidity {c.humidity_pct or 0}%"
    if hasattr(data, "forecast") and data.forecast:
        fc_str = "; ".join(f"{d.date}: {d.description or 'Forecast'}, rain {d.rain_mm or 0}mm" for d in data.forecast[:3])
        return f"{data.district} forecast: {fc_str}"
    if hasattr(data, "irrigation_advice") and data.irrigation_advice:
        return data.irrigation_advice
    if isinstance(data, dict):
        return data.get("advice_tamil") or data.get("reason") or None
    return None


_UNAVAILABLE_LABEL = {
    "weather": "Weather data", "crop": "Crop guidance", "market": "Market price data",
    "scheme": "Scheme data", "disease": "Disease information", "rag": "TNAU knowledge base search",
    "satellite": "Satellite information",
}


def _facts_for(result: ToolResult) -> list[str]:
    """FP-015: the factual lines the LLM may use. Tools put them in data["facts"]; for tools
    without them, the (non-RAG) citation excerpts are used. A failed tool yields an explicit
    "not available" line so the model says so instead of estimating."""
    prefix = result.tool.split(".")[0]
    if not result.success:
        return [f"{_UNAVAILABLE_LABEL.get(prefix, result.tool)} ({result.tool}): not available."]
    if prefix == "rag":
        return []
    if isinstance(result.data, dict) and isinstance(result.data.get("facts"), list):
        return [str(f) for f in result.data["facts"] if f]
    return [f"[{c.source}] {c.title}: {c.excerpt}" for c in result.citations if c.excerpt]


def retrieved_chunks(tool_results: list[ToolResult]) -> list[Citation]:
    """TNAU/RAG chunks actually returned by a successful rag.* retrieval (the only valid sources)."""
    chunks: list[Citation] = []
    for r in tool_results or []:
        if not r.success or not r.tool.startswith("rag.") or not isinstance(r.data, list):
            continue
        for c in r.data:
            if isinstance(c, Citation) and c.category == "rag" and (c.excerpt or "").strip():
                chunks.append(c)
    return chunks


def _detect_conflicts(results: list[ToolResult]) -> list[str]:
    warnings: list[str] = []
    irrigate_signals: list[bool] = []
    for r in results:
        if r.success and isinstance(r.data, dict) and r.data.get("irrigate_today") is not None:
            irrigate_signals.append(bool(r.data["irrigate_today"]))
    if len(set(irrigate_signals)) > 1:
        warnings.append("Conflicting irrigation signals — using highest-confidence recommendation")
    return warnings


async def evidence_fusion(state: dict[str, Any]) -> dict[str, Any]:
    with observe("evidence_fusion", state):
        tool_results: list[ToolResult] = state.get("tool_results", [])

        all_citations: list[Citation] = []
        weather_summary: str | None = None
        crop_summary: str | None = None
        disease_summary: str | None = None
        market_summary: str | None = None
        scheme_summary: str | None = None
        rag_excerpts: list[str] = []
        facts: list[str] = []
        successful = 0
        failed = 0

        for result in tool_results:
            all_citations.extend(result.citations)
            facts.extend(_facts_for(result))
            tool_prefix = result.tool.split(".")[0] if "." in result.tool else result.tool

            if not result.success:
                failed += 1
                continue

            successful += 1
            summary = _extract_summary(result)

            if tool_prefix == "weather":
                weather_summary = weather_summary or summary
            elif tool_prefix == "crop":
                crop_summary = crop_summary or summary
            elif tool_prefix == "disease":
                disease_summary = disease_summary or summary
            elif tool_prefix == "market":
                market_summary = market_summary or summary
            elif tool_prefix == "scheme":
                scheme_summary = scheme_summary or summary
            elif tool_prefix == "rag":
                # FP-015: only chunks actually retrieved (data list), never synthesized citations.
                for c in retrieved_chunks([result]):
                    rag_excerpts.append(c.excerpt[:300])

        disease_context = state.get("disease_context")
        if disease_context and isinstance(disease_context, dict):
            crop = disease_context.get("crop", "Unknown")
            pred_class = disease_context.get("predicted_class", "Unknown")
            conf = float(disease_context.get("confidence", 0.9))
            model = disease_context.get("model_architecture") or disease_context.get("model", "EfficientNetV2-S")
            disease_summary = (
                f"M4 v1 Research Demo (NOT PRODUCTION CERTIFIED): Crop: {crop}, "
                f"Prediction: {pred_class}, Confidence: {conf:.1%}, Model: {model}."
            )
            facts.append(
                f"[M4 v1 Research Demo] Crop: {crop}, Predicted: {pred_class} ({conf:.1%}), "
                f"Model: {model} (RESEARCH DEMO ONLY, NOT PRODUCTION CERTIFIED)"
            )
            all_citations.append(
                Citation(
                    source="UZHAVAN M4 v1 Research Checkpoint",
                    title=f"M4 Scan — {crop} ({pred_class})",
                    excerpt=f"Crop: {crop}, Model: {model}, Predicted: {pred_class}, Confidence: {conf:.1%}. Research demo output, not production certified.",
                    confidence=conf,
                    category="disease",
                )
            )
            successful += 1

        bundle = EvidenceBundle(
            citations=_dedupe_citations(all_citations),
            weather_summary=weather_summary,
            crop_summary=crop_summary,
            disease_summary=disease_summary,
            market_summary=market_summary,
            scheme_summary=scheme_summary,
            rag_excerpts=rag_excerpts[:5],
            facts=list(dict.fromkeys(facts))[:30],
            retrieved_chunks=retrieved_chunks(tool_results)[:6],
            overall_confidence=_weighted_confidence(tool_results),
            tools_used=[r.tool for r in tool_results if r.success],
            conflict_warnings=_detect_conflicts(tool_results),
            successful_tools=successful,
            failed_tools=failed,
        )

        output = {"evidence": bundle, "overall_confidence": bundle.overall_confidence}
    output["trace"] = state.get("trace", [])
    return output
