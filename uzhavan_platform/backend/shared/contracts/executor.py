from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.shared.models.context import ConversationContext
from backend.shared.models.decision import ResolvedCapability
from backend.shared.models.tool import ToolResult


@runtime_checkable
class ToolExecutorProtocol(Protocol):
    """
    Formal interface for the parallel tool execution node.
    Receives resolved capabilities, executes them concurrently, returns all results.
    """

    async def execute_all(
        self,
        resolved: list[ResolvedCapability],
        context: ConversationContext,
    ) -> list[ToolResult]:
        """
        Execute all resolved capabilities in parallel (asyncio.gather).
        Never raises — failed tool calls return ToolResult(success=False).
        Order of results matches order of resolved list.
        """
        ...
