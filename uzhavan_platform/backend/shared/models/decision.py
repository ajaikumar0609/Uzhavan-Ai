from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CapabilityRequest(BaseModel):
    """
    Planner emits these. Capability Resolver resolves them to concrete agents.
    Planner never names an agent directly — it requests a capability.
    This makes agent swapping (e.g., OpenMeteo → IMD) transparent to the planner.
    """
    capability_name: str          # e.g., "weather.forecast", "rag.advisory"
    params: dict[str, Any] = {}
    priority: int = 0
    required: bool = True         # if False, pipeline continues gracefully on failure


class ResolvedCapability(BaseModel):
    """Capability Resolver output — concrete agent + method selected from manifest registry."""
    agent_name: str
    method_name: str
    agent_version: str
    params: dict[str, Any] = {}
    capability_request: CapabilityRequest


class PlannerOutput(BaseModel):
    intent: str
    capability_requests: list[CapabilityRequest]
    planning_rationale: str


class Decision(BaseModel):
    intent: str
    resolved_capabilities: list[ResolvedCapability]
    planning_rationale: str
