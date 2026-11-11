from __future__ import annotations

import os


def _flag(name: str, default: bool = True) -> bool:
    return os.getenv(name, str(default)).lower() in ("true", "1", "yes")


class FeatureFlags:
    """
    Read-only view of all feature flags. Every layer reads from this — no os.getenv scattered
    through the codebase.
    """
    ENABLE_WEATHER: bool = _flag("ENABLE_WEATHER", default=True)
    ENABLE_DISEASE: bool = _flag("ENABLE_DISEASE", default=True)
    ENABLE_SCHEMES: bool = _flag("ENABLE_SCHEMES", default=True)
    ENABLE_MARKET: bool = _flag("ENABLE_MARKET", default=True)   # FP-015: observed AGMARKNET prices (FP-011)
    ENABLE_SATELLITE: bool = _flag("ENABLE_SATELLITE", default=False)
    ENABLE_MEMORY: bool = _flag("ENABLE_MEMORY", default=True)
    ENABLE_MCP: bool = _flag("ENABLE_MCP", default=False)
    ENABLE_STREAMING: bool = _flag("ENABLE_STREAMING", default=True)

    @classmethod
    def enabled_agents(cls) -> list[str]:
        """Return names of all enabled domain agents."""
        agents = ["rag", "crop"]  # always on
        if cls.ENABLE_WEATHER:
            agents.append("weather")
        if cls.ENABLE_DISEASE:
            agents.append("disease")
        if cls.ENABLE_SCHEMES:
            agents.append("scheme")
        if cls.ENABLE_MARKET:
            agents.append("market")
        if cls.ENABLE_SATELLITE:
            agents.append("satellite")
        if cls.ENABLE_MEMORY:
            agents.append("memory")
        return agents

    @classmethod
    def summary(cls) -> dict[str, bool]:
        return {
            "ENABLE_WEATHER": cls.ENABLE_WEATHER,
            "ENABLE_DISEASE": cls.ENABLE_DISEASE,
            "ENABLE_SCHEMES": cls.ENABLE_SCHEMES,
            "ENABLE_MARKET": cls.ENABLE_MARKET,
            "ENABLE_SATELLITE": cls.ENABLE_SATELLITE,
            "ENABLE_MEMORY": cls.ENABLE_MEMORY,
            "ENABLE_MCP": cls.ENABLE_MCP,
            "ENABLE_STREAMING": cls.ENABLE_STREAMING,
        }


flags = FeatureFlags()
