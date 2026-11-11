"""
SchemeAgent (FP-015) — the FP-012 schemes store + eligibility rules.

Uses the same data and 4-status logic as /api/schemes/{id}/eligibility
(`backend/knowledge/scheme/eligibility.evaluate`). It never claims eligibility beyond
`eligible_known_criteria`, and every status carries the rule's source URL. Missing farm
fields (district, crop, area) stay None and are reported as missing — never assumed.
"""
from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from backend.knowledge.scheme.eligibility import evaluate, load_rules
from backend.knowledge.scheme.store import SchemeStore, get_scheme_store
from backend.meta.catalog import CROP_IDS, district_id_from_name
from backend.shared.agents.base import BaseDomainAgent
from backend.shared.models.citation import Citation
from backend.shared.models.context import ConversationContext
from backend.shared.models.tool import AgentManifest, ToolCapability, ToolResult

MAX_SCHEMES = 5

STATUS_TEXT = {
    "eligible_known_criteria": "meets the criteria stated in the official source (only those criteria were checked; documents and other conditions still apply)",
    "not_eligible_known_criteria": "does not meet a criterion stated in the official source",
    "more_information_required": "more information is needed to check eligibility",
    "cannot_determine": "eligibility cannot be determined (no verified rule; read the official eligibility text)",
}


def _crop_id(crop: str | None) -> str | None:
    if not crop:
        return None
    cid = crop.strip().lower().replace(" ", "_")
    return cid if cid in CROP_IDS else None


class SchemeAgent(BaseDomainAgent):
    VERSION = "2.0"
    _CAPABILITIES = ["eligibility"]

    def __init__(self, store_factory: Callable[[], Awaitable[SchemeStore]] | None = None) -> None:
        self._store_factory = store_factory or get_scheme_store

    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_name="scheme",
            version=self.VERSION,
            description="Government schemes from official sources with rule-based eligibility status (4 statuses)",
            avg_latency_ms=200,
            typical_confidence=0.85,
            feature_flag="ENABLE_SCHEMES",
            dependencies=["postgresql"],
            capabilities=[
                ToolCapability(name="eligibility", description="Relevant schemes and their eligibility status on the stated criteria", avg_latency_ms=200),
            ],
        )

    def can_handle(self, capability_name: str) -> bool:
        parts = capability_name.split(".", 1)
        return len(parts) == 2 and parts[0] == "scheme" and parts[1] in self._CAPABILITIES

    async def execute(self, capability_name: str, context: ConversationContext, params: dict[str, Any]) -> ToolResult:
        start_ns = time.monotonic_ns()
        _, method = capability_name.split(".", 1)
        if method not in self._CAPABILITIES:
            return self._timed_result(capability_name, start_ns, False, error=f"Unknown method: {method}")
        crop = params.get("crop") or (context.farm.crop if context.farm else None)
        district = params.get("district") or (context.farm.district if context.farm else None) or context.farmer.district
        area = params.get("area_ha") if params.get("area_ha") is not None else (context.farm.area_ha if context.farm else None)
        ctx = {
            "district_id": district_id_from_name(district) if district else None,
            "crop_id": _crop_id(crop),
            "area_ha": float(area) if area is not None else None,   # FP-015: never defaulted (was 1.0)
            "_label": None,
        }
        try:
            store = await self._store_factory()
            return await self._eligibility(start_ns, store, ctx)
        except Exception as exc:
            return self._timed_result(capability_name, start_ns, False, error=f"scheme data unavailable: {type(exc).__name__}")

    async def _eligibility(self, start_ns: int, store: SchemeStore, ctx: dict[str, Any]) -> ToolResult:
        rows = await store.list(None, None, ctx["crop_id"], None) if ctx["crop_id"] else []
        if not rows:
            rows = await store.list(None, None, None, None)
        rules = load_rules()
        # Schemes with a verified rule first (they can actually be checked), then the rest.
        rows = sorted(rows, key=lambda s: (s["scheme_id"] not in rules, s.get("active") is False, s.get("name") or ""))[:MAX_SCHEMES]
        if not rows:
            return self._timed_result("scheme.eligibility", start_ns, False, error="No schemes loaded")

        missing = [k for k, label in (("district_id", "district"), ("crop_id", "crop"), ("area_ha", "farm area")) if ctx[k] is None]
        facts = ["Scheme details come from official sources; eligibility is checked only against criteria stated there."]
        if missing:
            facts.append("Not known for this farmer: " + ", ".join(
                {"district_id": "district", "crop_id": "crop", "area_ha": "farm area"}[m] for m in missing) + ".")
        schemes, citations = [], []
        for s in rows:
            result = evaluate(s, [ctx], rules)
            status = result["status"]
            reasons = " ".join(r["en"] for r in result["reasons"] if r.get("en"))
            src = result.get("criteria_source_url") or s.get("official_url")
            line = f"{s['name']}: {STATUS_TEXT[status]} [status: {status}; rule source: {src or 'not available'}]. {reasons}"
            facts.append(line)
            schemes.append({"scheme_id": s["scheme_id"], "name": s["name"], "tamil_name": s.get("tamil_name"),
                            "status": status, "reasons": result["reasons"], "missing_fields": result["missing_fields"],
                            "criteria_source_url": src, "official_url": s.get("official_url")})
            citations.append(Citation(source=s.get("authority") or "Official scheme source", title=s["name"],
                                      excerpt=line[:500], confidence=0.85, url=src, category="scheme"))
        data = {"schemes": schemes, "count": len(schemes), "context": {k: v for k, v in ctx.items() if k != "_label"}, "facts": facts}
        return self._timed_result("scheme.eligibility", start_ns, True, data=data, citations=citations, confidence=0.85)

    async def health(self) -> bool:
        try:
            await self._store_factory()
            return True
        except Exception:
            return False
