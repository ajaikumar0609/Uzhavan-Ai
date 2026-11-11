from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from backend.shared.models.context import ConversationContext
from backend.shared.models.tool import AgentManifest, ToolResult


@runtime_checkable
class DomainAgentProtocol(Protocol):
    """
    Formal interface contract for every domain agent.
    Any class that satisfies this protocol can be registered in the AgentRegistry —
    it does not need to inherit from BaseDomainAgent.
    This enables mock agents in tests without subclassing.
    """

    def manifest(self) -> AgentManifest:
        """Return agent metadata. Called once at registration time."""
        ...

    def can_handle(self, capability_name: str) -> bool:
        """Return True if this agent can execute the named capability."""
        ...

    async def execute(
        self,
        capability_name: str,
        context: ConversationContext,
        params: dict[str, Any],
    ) -> ToolResult:
        """Execute a capability. Must never raise — return ToolResult(success=False) on error."""
        ...

    async def validate(self, result: ToolResult) -> bool:
        """Post-execution validation. Return False to mark result as invalid."""
        ...

    async def health(self) -> bool:
        """Return True if agent's external dependencies are reachable."""
        ...

    def describe_tools(self) -> list[str]:
        """Return short human-readable descriptions of all enabled capabilities."""
        ...
