from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.shared.models.context import ConversationContext
from backend.shared.models.decision import PlannerOutput
from backend.shared.models.tool import AgentManifest


@runtime_checkable
class PlannerProtocol(Protocol):
    """
    Formal interface for the Planner node.
    Planner sees AgentManifests and emits CapabilityRequests.
    It never imports agents, never calls HTTP, never touches the LLM.
    """

    async def plan(
        self,
        intent: str,
        context: ConversationContext,
        available_manifests: list[AgentManifest],
    ) -> PlannerOutput:
        """
        Given intent + context + available capabilities, decide which capabilities to invoke.
        Returns PlannerOutput with CapabilityRequests — not resolved agents.
        """
        ...
