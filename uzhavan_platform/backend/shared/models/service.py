from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ServiceMetadata(BaseModel):
    """
    Attached to every service response.
    Gives the pipeline — and debugging sessions — full context on where data came from.
    """
    source: str                     # "open-meteo" | "chromadb" | "postgresql" | "cache" | etc.
    version: str = "1.0"
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cache_hit: bool = False
    latency_ms: int = 0


class ServiceResult(BaseModel, Generic[T]):
    """
    Universal service return type. Every KnowledgeService returns this.
    Services never return raw dicts — always ServiceResult.
    """
    data: T
    metadata: ServiceMetadata

    @property
    def from_cache(self) -> bool:
        return self.metadata.cache_hit

    @property
    def source(self) -> str:
        return self.metadata.source
