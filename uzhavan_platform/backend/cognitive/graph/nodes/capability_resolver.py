"""
Capability Resolver Node

Input:  planner_output (list[CapabilityRequest])
Output: resolved_capabilities (list[ResolvedCapability])

One job: translate capability names into concrete agent + method pairs.
Delegates entirely to AgentRegistry — no hardcoding of agent names here.
"""
from __future__ import annotations

from typing import Any

from backend.cognitive.observability import observe
from backend.shared.exceptions import ToolNotFoundError
from backend.tools.registry import AgentRegistry

_registry: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    global _registry
    if _registry is None:
        from backend.tools import build_registry
        _registry = build_registry()
    return _registry


async def capability_resolver(state: dict[str, Any]) -> dict[str, Any]:
    with observe("capability_resolver", state):
        planner_output = state.get("planner_output")
        if not planner_output or not planner_output.capability_requests:
            output: dict[str, Any] = {"resolved_capabilities": []}
        else:
            registry = get_registry()
            # FP-015: a capability that is not registered (e.g. its feature flag is off) is
            # skipped, never raised: with no tool data, grounding fails and the farmer gets the
            # safe "not available" answer instead of an error event.
            resolved = []
            for req in planner_output.capability_requests:
                try:
                    resolved.extend(registry.resolve_all([req]))
                except ToolNotFoundError:
                    continue
            output = {"resolved_capabilities": resolved}
    output["trace"] = state.get("trace", [])
    return output
