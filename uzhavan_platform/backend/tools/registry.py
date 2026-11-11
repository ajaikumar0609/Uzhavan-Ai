from __future__ import annotations

import logging
from typing import Any

from backend.feature_flags import flags
from backend.shared.contracts.agent import DomainAgentProtocol
from backend.shared.exceptions import ToolNotFoundError
from backend.shared.models.decision import CapabilityRequest, ResolvedCapability
from backend.shared.models.tool import AgentManifest

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Self-registering agent registry. Planner and Capability Resolver depend on this.
    No concrete agent class is ever imported outside of the registration call.
    Adding a new domain agent: instantiate it and call registry.register(agent).
    """

    def __init__(self) -> None:
        self._agents: dict[str, DomainAgentProtocol] = {}           # agent_name → agent
        self._capability_index: dict[str, str] = {}                  # capability_name → agent_name

    def register(self, agent: DomainAgentProtocol) -> None:
        manifest = agent.manifest()

        if manifest.feature_flag and not getattr(flags, manifest.feature_flag, False):
            logger.info("Agent %s skipped — feature flag %s is off", manifest.agent_name, manifest.feature_flag)
            return

        self._agents[manifest.agent_name] = agent
        for cap in manifest.capabilities:
            if cap.enabled:
                key = f"{manifest.agent_name}.{cap.name}"
                self._capability_index[key] = manifest.agent_name

        logger.info("Registered agent: %s v%s (%d capabilities)", manifest.agent_name, manifest.version, len(manifest.capabilities))

    def resolve(self, capability_name: str) -> DomainAgentProtocol:
        agent_name = self._capability_index.get(capability_name)
        if not agent_name:
            raise ToolNotFoundError(f"No agent registered for capability: {capability_name}")
        return self._agents[agent_name]

    def resolve_all(self, requests: list[CapabilityRequest]) -> list[ResolvedCapability]:
        resolved: list[ResolvedCapability] = []
        for req in requests:
            try:
                agent = self.resolve(req.capability_name)
                manifest = agent.manifest()
                agent_name, method_name = req.capability_name.split(".", 1)
                resolved.append(ResolvedCapability(
                    agent_name=agent_name,
                    method_name=method_name,
                    agent_version=manifest.version,
                    params=req.params,
                    capability_request=req,
                ))
            except ToolNotFoundError:
                if req.required:
                    raise
                logger.warning("Optional capability %s not found — skipping", req.capability_name)
        return resolved

    def get_agent(self, agent_name: str) -> DomainAgentProtocol:
        if agent_name not in self._agents:
            raise ToolNotFoundError(f"No agent named: {agent_name}")
        return self._agents[agent_name]

    def list_capabilities(self) -> list[str]:
        return sorted(self._capability_index.keys())

    def manifest_all(self) -> list[AgentManifest]:
        return [agent.manifest() for agent in self._agents.values()]

    async def health_check(self) -> dict[str, bool]:
        results: dict[str, bool] = {}
        for name, agent in self._agents.items():
            try:
                results[name] = await agent.health()
            except Exception as exc:
                logger.warning("Health check failed for %s: %s", name, exc)
                results[name] = False
        return results

    def __repr__(self) -> str:
        return f"AgentRegistry(agents={list(self._agents.keys())}, capabilities={len(self._capability_index)})"
