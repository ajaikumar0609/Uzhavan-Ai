"""
Tool layer: AgentRegistry + all domain agents.
Import `build_registry()` at application startup.
"""
from backend.tools.registry import AgentRegistry


def build_registry() -> AgentRegistry:
    """
    Instantiate all domain agents and register them.
    AgentRegistry reads each manifest and indexes capabilities.
    Feature-flagged agents are silently skipped if their flag is off.
    """
    from backend.tools.agents import (
        CropAgent, DiseaseAgent, MarketAgent, RAGAgent, SatelliteAgent, SchemeAgent, WeatherAgent,
    )

    registry = AgentRegistry()
    registry.register(RAGAgent())       # always active — core knowledge
    registry.register(CropAgent())      # always active — pure reasoning
    registry.register(WeatherAgent())   # ENABLE_WEATHER
    registry.register(DiseaseAgent())   # ENABLE_DISEASE
    registry.register(SchemeAgent())    # ENABLE_SCHEMES
    registry.register(MarketAgent())    # ENABLE_MARKET — observed AGMARKNET prices only (FP-015)
    registry.register(SatelliteAgent()) # status only: "under validation" (FP-015)
    return registry


__all__ = ["AgentRegistry", "build_registry"]
