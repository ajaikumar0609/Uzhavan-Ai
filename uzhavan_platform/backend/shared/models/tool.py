from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from backend.shared.models.citation import Citation


class ToolCapability(BaseModel):
    """One callable capability exposed by a domain agent."""
    name: str
    description: str
    description_tamil: str | None = None
    input_schema: dict[str, Any] = {}
    output_schema: dict[str, Any] = {}
    enabled: bool = True
    avg_latency_ms: int = 500


class AgentManifest(BaseModel):
    """
    Metadata every domain agent exposes.
    Capability Resolver reads manifests — never hardcodes agent names or methods.
    Adding a new agent = registering its manifest. No planner changes required.
    """
    agent_name: str
    version: str
    description: str
    capabilities: list[ToolCapability]
    dependencies: list[str] = []
    avg_latency_ms: int
    typical_confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    feature_flag: str | None = None  # None means always active
    healthy: bool = True


class ToolResult(BaseModel):
    """
    Standardized return type for every domain agent tool.
    All agents return this — makes every tool interchangeable at the pipeline level.
    Never return raw dicts from agents.
    """
    tool: str
    success: bool
    data: Any | None = None
    citations: list[Citation] = []
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    execution_time_ms: int = 0
    cached: bool = False
    error: str | None = None
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_version: str = "1.0"
    retry_count: int = 0

    @property
    def has_data(self) -> bool:
        return self.data is not None and self.success
