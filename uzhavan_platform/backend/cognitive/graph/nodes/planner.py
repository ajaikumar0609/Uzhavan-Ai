"""
Planner Node

Input:  intent, extracted_entities
Output: planner_output (PlannerOutput with list[CapabilityRequest])

One job: decide which capabilities are needed to answer this question.
No LLM. Rule-based mapping from intent → capability requests.
Planner never names an agent directly — it emits CapabilityRequests.
"""
from __future__ import annotations

from typing import Any

from backend.cognitive.observability import observe
from backend.cognitive.graph.nodes.definitional import is_definitional
from backend.shared.models.decision import CapabilityRequest, PlannerOutput

# ── Intent → Capability mapping ───────────────────────────────────────────────
# Priority: lower number = runs first when sorted
_INTENT_CAPABILITIES: dict[str, list[tuple[str, int, bool]]] = {
    # (capability_name, priority, required)
    "advisory": [
        ("weather.irrigation_advice", 1, True),
        ("crop.fertilizer_plan", 2, True),
        ("rag.advisory", 3, False),
    ],
    "weather": [
        ("weather.current_weather", 1, True),
        ("weather.forecast", 2, True),
        ("weather.rain_alert", 3, False),
    ],
    # FP-015: every name below is a registered capability. disease.identify reports
    # "model_unavailable" (no diagnosis); TNAU text comes from RAG.
    "disease": [
        ("disease.identify", 1, True),
        ("rag.advisory", 2, False),
    ],
    "market": [
        ("market.current_price", 1, True),
        ("market.trend", 2, False),
    ],
    "scheme": [
        ("scheme.eligibility", 1, True),
    ],
    "satellite": [
        ("satellite.status", 1, True),
    ],
    "crop": [
        ("crop.recommend", 1, True),
        ("crop.fertilizer_plan", 2, False),
        ("crop.crop_calendar", 3, False),
        ("rag.advisory", 4, False),
    ],
    "off_topic": [],
}


_DEFINITION_CAPS = [("rag.advisory", 1, True)]


def _build_requests(
    intent: str,
    entities: dict[str, Any],
    question: str = "",
) -> list[CapabilityRequest]:
    caps = _INTENT_CAPABILITIES.get(intent, [])
    # "What is NPK?" / "importance of crop rotation": explain from TNAU text only. Running the
    # weather and fertiliser-plan tools handed the model per-hectare rates and the farm area,
    # which it multiplied into field quantities that the dosage guard then rejected.
    if intent in ("advisory", "crop") and is_definitional(question):
        caps = _DEFINITION_CAPS
    requests: list[CapabilityRequest] = []
    for capability_name, priority, required in caps:
        # Pass all known entities as params — agents take what they need
        requests.append(CapabilityRequest(
            capability_name=capability_name,
            params=dict(entities),
            priority=priority,
            required=required,
        ))
    return requests


async def planner(state: dict[str, Any]) -> dict[str, Any]:
    with observe("planner", state):
        intent: str = state.get("intent", "off_topic")
        entities: dict[str, Any] = state.get("extracted_entities", {})

        ctx = state.get("context")
        question = (getattr(ctx, "current_question", "") if ctx else "") or state.get("user_message", "") or ""
        capability_requests = _build_requests(intent, entities, question)

        rationale = (
            f"Intent '{intent}' requires {len(capability_requests)} capability calls: "
            + ", ".join(r.capability_name for r in capability_requests)
        )

        output = {
            "planner_output": PlannerOutput(
                intent=intent,
                capability_requests=capability_requests,
                planning_rationale=rationale,
            ),
        }
    output["trace"] = state.get("trace", [])
    return output
