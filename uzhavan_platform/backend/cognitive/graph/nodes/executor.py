"""
Executor Node — Parallel Domain Agents

Input:  resolved_capabilities, context
Output: tool_results

One job: run all resolved capabilities in parallel using asyncio.gather().
Each agent executes independently. Failures are captured in ToolResult.success=False,
never raised — the evidence fusion engine handles partial results gracefully.
"""
from __future__ import annotations

import asyncio
from typing import Any

from backend.cognitive.observability import observe
from backend.shared.models.tool import ToolResult
from backend.tools.registry import AgentRegistry

_registry: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    global _registry
    if _registry is None:
        from backend.tools import build_registry
        _registry = build_registry()
    return _registry


async def _run_one(registry: AgentRegistry, resolved, context) -> ToolResult:
    try:
        agent = registry.get_agent(resolved.agent_name)
        capability_name = f"{resolved.agent_name}.{resolved.method_name}"
        return await agent.execute(capability_name, context, resolved.params)
    except Exception as exc:
        return ToolResult(
            tool=f"{resolved.agent_name}.{resolved.method_name}",
            success=False,
            error=str(exc),
        )


async def executor(state: dict[str, Any]) -> dict[str, Any]:
    with observe("executor", state):
        resolved_capabilities = state.get("resolved_capabilities", [])
        context = state["context"]

        if not resolved_capabilities:
            output: dict[str, Any] = {"tool_results": []}
        else:
            registry = get_registry()
            sorted_caps = sorted(
                resolved_capabilities,
                key=lambda r: r.capability_request.priority if r.capability_request else 0,
            )
            tasks = [_run_one(registry, cap, context) for cap in sorted_caps]
            results: list[ToolResult] = await asyncio.gather(*tasks)
            output = {"tool_results": list(results)}
    output["trace"] = state.get("trace", [])
    return output
