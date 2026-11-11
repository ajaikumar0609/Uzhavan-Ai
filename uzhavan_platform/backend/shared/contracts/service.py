from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from backend.shared.models.service import ServiceResult


@runtime_checkable
class KnowledgeServiceProtocol(Protocol):
    """
    Uniform interface every knowledge service implements.
    Services are data providers only — no farming reasoning, no LangGraph imports.
    Agents depend on this protocol, never on concrete service classes.
    """

    async def health(self) -> bool:
        """Return True if the service's upstream dependency is reachable."""
        ...

    def version(self) -> str:
        """Semantic version of this service implementation."""
        ...

    async def last_updated(self) -> datetime:
        """When was the underlying data last refreshed?"""
        ...

    async def get(self, key: str, **kwargs: Any) -> ServiceResult[Any]:
        """Retrieve a single item by key."""
        ...

    async def search(self, query: str, **kwargs: Any) -> ServiceResult[list[Any]]:
        """Search / retrieve multiple items matching a query."""
        ...
