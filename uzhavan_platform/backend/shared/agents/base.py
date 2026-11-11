from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from backend.shared.models.context import ConversationContext
from backend.shared.models.tool import AgentManifest, ToolResult


class BaseDomainAgent(ABC):
    """
    Every domain agent implements this interface.
    Planner and Capability Resolver depend only on this interface — never on concrete agents.
    To add a new agent: subclass this, implement the abstract methods, register with AgentRegistry.
    """

    @abstractmethod
    def manifest(self) -> AgentManifest:
        """Expose agent metadata. Capability Resolver reads this — no hardcoding."""
        ...

    @abstractmethod
    def can_handle(self, capability_name: str) -> bool:
        """
        Return True if this agent can execute the named capability.
        Format: "agent_name.method_name" e.g. "weather.forecast"
        """
        ...

    @abstractmethod
    async def execute(
        self,
        capability_name: str,
        context: ConversationContext,
        params: dict[str, Any],
    ) -> ToolResult:
        """
        Execute a capability. Always returns ToolResult — never raises to the caller.
        Catch all internal exceptions and return ToolResult(success=False, error=...).
        """
        ...

    async def validate(self, result: ToolResult) -> bool:
        """Post-execution validation. Override to add agent-specific checks."""
        return result.success

    async def health(self) -> bool:
        """Return True if the agent's dependencies (APIs, DB, models) are reachable."""
        return True

    def describe_tools(self) -> list[str]:
        """Short capability descriptions for planner context window."""
        return [
            f"{cap.name}: {cap.description}"
            for cap in self.manifest().capabilities
            if cap.enabled
        ]

    def _timed_result(
        self,
        tool: str,
        start_ns: int,
        success: bool,
        data: Any = None,
        citations: list = [],
        confidence: float = 0.0,
        cached: bool = False,
        error: str | None = None,
        retry_count: int = 0,
    ) -> ToolResult:
        """Helper: build ToolResult with execution_time_ms automatically calculated."""
        execution_time_ms = int((time.monotonic_ns() - start_ns) / 1_000_000)
        return ToolResult(
            tool=tool,
            success=success,
            data=data,
            citations=citations,
            confidence=confidence,
            execution_time_ms=execution_time_ms,
            cached=cached,
            error=error,
            agent_version=self.manifest().version,
            retry_count=retry_count,
        )
