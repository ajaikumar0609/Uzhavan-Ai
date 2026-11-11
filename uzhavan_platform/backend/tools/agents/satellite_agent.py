"""
SatelliteAgent (FP-015, contract §11). Satellite / SICKLE crop predictions are NOT served while
the gates in /api/satellite/status are open: this agent only reports "under validation".
"""
from __future__ import annotations

import time
from typing import Any

from backend.shared.agents.base import BaseDomainAgent
from backend.shared.models.context import ConversationContext
from backend.shared.models.tool import AgentManifest, ToolCapability, ToolResult


class SatelliteAgent(BaseDomainAgent):
    VERSION = "1.0"
    FACT = ("Satellite crop predictions (SICKLE models) are under validation and are not available. "
            "UZHAVAN does not give satellite-based crop, yield or sowing estimates yet.")
    FACT_TAMIL = "செயற்கைக்கோள் பயிர் கணிப்புகள் சரிபார்ப்பில் உள்ளன; தற்போது கிடைக்கவில்லை."

    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_name="satellite", version=self.VERSION,
            description="Satellite prediction status only (under validation; no predictions served)",
            avg_latency_ms=1, typical_confidence=0.9, feature_flag=None,
            capabilities=[ToolCapability(name="status", description="Satellite availability status", avg_latency_ms=1)],
        )

    def can_handle(self, capability_name: str) -> bool:
        return capability_name == "satellite.status"

    async def execute(self, capability_name: str, context: ConversationContext, params: dict[str, Any]) -> ToolResult:
        start_ns = time.monotonic_ns()
        if capability_name != "satellite.status":
            return self._timed_result(capability_name, start_ns, False, error="Satellite predictions are under validation")
        from backend.conversation.routes.satellite import SATELLITE_STATUS

        data = {"available": False, "reason": SATELLITE_STATUS["reason"], "prediction": None,
                "facts": [self.FACT], "message_tamil": self.FACT_TAMIL}
        return self._timed_result("satellite.status", start_ns, True, data=data, confidence=0.9)
