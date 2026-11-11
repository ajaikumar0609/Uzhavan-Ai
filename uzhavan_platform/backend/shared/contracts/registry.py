from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.shared.models.decision import CapabilityRequest, ResolvedCapability
from backend.shared.models.tool import AgentManifest, ToolResult
from backend.shared.contracts.agent import DomainAgentProtocol


@runtime_checkable
class AgentRegistryProtocol(Protocol):
    """
    Formal interface for the AgentRegistry.
    Planner and Capability Resolver depend on this — never on the concrete AgentRegistry.
    """

    def register(self, agent: DomainAgentProtocol) -> None:
        """Register a domain agent. Reads its manifest to index capabilities."""
        ...

    def resolve(self, capability_name: str) -> DomainAgentProtocol:
        """Return the agent that can handle this capability. Raises ToolNotFoundError if none."""
        ...

    def resolve_all(
        self, requests: list[CapabilityRequest]
    ) -> list[ResolvedCapability]:
        """Resolve a list of capability requests to concrete agents. Skips disabled/unhealthy."""
        ...

    def list_capabilities(self) -> list[str]:
        """Return all registered capability names."""
        ...

    def manifest_all(self) -> list[AgentManifest]:
        """Return all registered agent manifests. Used by Planner for context."""
        ...

    async def health_check(self) -> dict[str, bool]:
        """Return {agent_name: is_healthy} for all registered agents."""
        ...
