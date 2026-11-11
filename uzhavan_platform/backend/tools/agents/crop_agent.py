from __future__ import annotations

import time
from typing import Any

from backend.knowledge.crop.service import CropKnowledgeService
from backend.shared.agents.base import BaseDomainAgent
from backend.shared.models.citation import Citation
from backend.shared.models.context import ConversationContext
from backend.shared.models.tool import AgentManifest, ToolCapability, ToolResult


class CropAgent(BaseDomainAgent):
    """
    Owns all agronomic reasoning about crop production.
    Data comes from CropKnowledgeService (TNAU tables).
    This agent applies the calculations, decision rules, and Tamil advice.
    """

    VERSION = "1.0"
    _CAPABILITIES = ["recommend", "crop_calendar", "fertilizer_plan", "rotation", "seed_rate"]

    def __init__(self, service: CropKnowledgeService | None = None) -> None:
        self._service = service or CropKnowledgeService()

    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_name="crop",
            version=self.VERSION,
            description="Crop selection, calendar, fertilizer planning, and rotation advice for Tamil Nadu",
            avg_latency_ms=80,
            typical_confidence=0.85,
            feature_flag=None,  # always active
            capabilities=[
                ToolCapability(name="recommend", description="Recommend suitable crops for district + season", avg_latency_ms=80),
                ToolCapability(name="crop_calendar", description="Sowing and harvest calendar for Tamil Nadu", avg_latency_ms=60),
                ToolCapability(name="fertilizer_plan", description="N-P-K fertilizer schedule by crop stage", avg_latency_ms=80),
                ToolCapability(name="rotation", description="Recommend crop rotation to break pest cycles", avg_latency_ms=60),
                ToolCapability(name="seed_rate", description="Recommended seed quantity per hectare", avg_latency_ms=50),
            ],
        )

    def can_handle(self, capability_name: str) -> bool:
        parts = capability_name.split(".", 1)
        return len(parts) == 2 and parts[0] == "crop" and parts[1] in self._CAPABILITIES

    async def execute(
        self, capability_name: str, context: ConversationContext, params: dict[str, Any]
    ) -> ToolResult:
        start_ns = time.monotonic_ns()
        _, method = capability_name.split(".", 1)
        try:
            # FP-015: missing values stay None — no invented district, area (was 1.0), stage
            # (was "vegetative"), soil (was "medium") or season.
            district = params.get("district") or (context.farm.district if context.farm else None) or context.farmer.district
            crop = params.get("crop") or (context.farm.crop if context.farm else None)
            area_raw = params.get("area_ha") if params.get("area_ha") is not None else (context.farm.area_ha if context.farm else None)
            area_ha = float(area_raw) if area_raw is not None else None

            if method == "recommend":
                return await self._recommend(start_ns, district, params.get("season"))
            if method != "recommend" and not crop:
                return self._timed_result(capability_name, start_ns, False, error="crop unknown: not in the question or the farm")
            knowledge = (await self._service.get(crop)).data
            if knowledge is None or knowledge.crop == "default":
                return self._timed_result(capability_name, start_ns, False,
                                          error=f"No TNAU crop table for {crop!r}; no generic values are used")
            if method == "crop_calendar":
                return await self._crop_calendar(start_ns, crop, district)
            elif method == "fertilizer_plan":
                stage = params.get("crop_stage") or (context.farm.crop_stage if context.farm else None)
                soil = params.get("soil_type") or (context.farm.soil_type if context.farm else None)
                return await self._fertilizer_plan(start_ns, crop, area_ha, stage, soil)
            elif method == "rotation":
                return await self._rotation(start_ns, crop)
            elif method == "seed_rate":
                return await self._seed_rate(start_ns, crop, area_ha)
            else:
                return self._timed_result(capability_name, start_ns, False, error=f"Unknown method: {method}")
        except Exception as exc:
            return self._timed_result(capability_name, start_ns, False, error=str(exc))

    async def _recommend(self, start_ns: int, district: str | None, season: str | None) -> ToolResult:
        if not district:
            return self._timed_result("crop.recommend", start_ns, False, error="district unknown")
        zone = self._service.get_agroclimatic_zone(district)
        if zone == "default":
            return self._timed_result("crop.recommend", start_ns, False,
                                      error=f"District {district!r} is not mapped to an agroclimatic zone")
        seasons = [season] if season else sorted(self._service._ZONE_CROP_MAP.get(zone, {}))
        by_season = {s: self._service._ZONE_CROP_MAP.get(zone, {}).get(s) for s in seasons}
        by_season = {s: c for s, c in by_season.items() if c}
        if not by_season:
            return self._timed_result("crop.recommend", start_ns, False, error=f"No crop list for zone {zone} / season {season}")
        recommendations = by_season.get(season) if season else sorted({c for cs in by_season.values() for c in cs})
        text = "; ".join(f"{s}: {', '.join(c)}" for s, c in by_season.items())
        data = {
            "district": district,
            "season": season,
            "agroclimatic_zone": zone,
            "recommended_crops": recommendations,
            "by_season": by_season,
            "note_tamil": f"{zone} மண்டலத்திற்கு பொருத்தமான பயிர்கள்.",
            "facts": [f"Crops listed for the {zone} zone ({district}) — {text} (TNAU Crop Production Guide)."],
        }
        citation = Citation(source="TNAU Crop Production Guide", title=f"Crop Recommendation — {zone} Zone", excerpt=f"Recommended crops — {text}", confidence=0.87, category="crop")
        return self._timed_result("crop.recommend", start_ns, True, data=data, citations=[citation], confidence=0.87)

    async def _crop_calendar(self, start_ns: int, crop: str, district: str | None) -> ToolResult:
        result = await self._service.get(crop)
        knowledge = result.data
        if not knowledge or not knowledge.calendar:
            return self._timed_result("crop.crop_calendar", start_ns, False, error=f"No calendar data for crop: {crop}")
        data = {"crop": crop, "district": district, **knowledge.calendar, "source": knowledge.source}
        citation = Citation(source=knowledge.source, title=f"{crop} Cultivation Calendar", excerpt=str(list(knowledge.calendar.items())[:2]), confidence=0.90, category="crop")
        return self._timed_result("crop.crop_calendar", start_ns, True, data=data, citations=[citation], confidence=0.90)

    _SOIL_FACTOR = {"sandy": 1.15, "medium": 1.0, "clayey": 0.90, "loamy": 1.0, "red": 1.10, "black": 0.85}
    _STAGE_FACTOR = {"seedling": 0.2, "vegetative": 0.4, "tillering": 0.3, "flowering": 0.1, "grain_fill": 0.0, "harvest": 0.0}

    async def _fertilizer_plan(self, start_ns: int, crop: str, area_ha: float | None, stage: str | None, soil: str | None) -> ToolResult:
        """
        Agronomic reasoning: base NPK from TNAU tables, adjusted by soil type and crop stage.
        FP-015: a stage-specific dose is computed only for a known stage; a soil adjustment only
        for a known soil type; farm totals only for a known area. Unknowns are stated, not assumed.
        """
        knowledge = (await self._service.get(crop)).data
        base = knowledge.npk_base_kg_ha
        facts: list[str] = [f"TNAU base recommendation for {crop}: N {base['N']}, P {base['P']}, K {base['K']} kg/ha for the whole crop ({knowledge.source})."]

        soil_key = (soil or "").lower()
        soil_factor = self._SOIL_FACTOR.get(soil_key)
        if soil_factor is None:
            soil_factor = 1.0
            facts.append("Soil type is not known, so no soil adjustment was applied." if not soil else f"Soil type {soil!r} has no adjustment factor; none applied.")
        stage_lower = (stage or "").lower()
        if stage_lower not in self._STAGE_FACTOR:
            facts.append("Crop stage is not known, so a stage-specific dose cannot be given." if not stage else f"No stage split is defined for stage {stage!r}.")
            data = {"crop": crop, "area_ha": area_ha, "crop_stage": stage, "soil_type": soil,
                    "recommendation": None, "base_npk_kg_per_ha": dict(base), "facts": facts,
                    "advice_tamil": f"{crop} பயிரின் வளர்ச்சி நிலை தெரியாததால் அந்த நிலைக்கான உர அளவை கூற முடியவில்லை."}
            citation = Citation(source=knowledge.source, title=f"{crop} Fertilizer — base NPK", excerpt=facts[0], confidence=0.80, category="crop")
            return self._timed_result("crop.fertilizer_plan", start_ns, True, data=data, citations=[citation], confidence=0.80)

        stage_factor = self._STAGE_FACTOR[stage_lower]
        n_kg_ha = round(base["N"] * soil_factor * stage_factor)
        p_kg_ha = round(base["P"] * (0.5 if stage_lower in ("seedling", "vegetative") else 0.0))
        k_kg_ha = round(base["K"] * stage_factor)

        recommendation: dict[str, Any] = {"N_kg_per_ha": n_kg_ha, "P_kg_per_ha": p_kg_ha, "K_kg_per_ha": k_kg_ha,
                                          "total_N_kg": None, "total_P_kg": None, "total_K_kg": None}
        facts.append(f"Dose at {stage} stage: N {n_kg_ha}, P {p_kg_ha}, K {k_kg_ha} kg per hectare.")
        if area_ha is not None:
            recommendation.update(total_N_kg=round(n_kg_ha * area_ha, 1), total_P_kg=round(p_kg_ha * area_ha, 1),
                                  total_K_kg=round(k_kg_ha * area_ha, 1))
            facts.append(f"For the recorded farm area of {area_ha} ha: N {recommendation['total_N_kg']} kg, "
                         f"P {recommendation['total_P_kg']} kg, K {recommendation['total_K_kg']} kg in total.")
        else:
            facts.append("Farm area is not known, so only per-hectare amounts are given (no farm totals).")

        data = {
            "crop": crop,
            "area_ha": area_ha,
            "crop_stage": stage,
            "soil_type": soil,
            "recommendation": recommendation,
            "facts": facts,
            "advice_tamil": f"{crop} பயிருக்கு {stage} நிலையில் ஒரு ஹெக்டேருக்கு {n_kg_ha}கிலோ தழைச்சத்து போடவும்.",
        }
        citation = Citation(source=knowledge.source, title=f"{crop} Fertilizer Plan — {stage}", excerpt=f"N:{n_kg_ha} P:{p_kg_ha} K:{k_kg_ha} kg/ha at {stage} stage" + (f" for {soil} soil" if soil else " (soil type unknown, not adjusted)"), confidence=0.88, category="crop")
        return self._timed_result("crop.fertilizer_plan", start_ns, True, data=data, citations=[citation], confidence=0.88)

    async def _rotation(self, start_ns: int, crop: str) -> ToolResult:
        result = await self._service.get(crop)
        knowledge = result.data
        data = {
            "current_crop": crop,
            "recommended_rotation": knowledge.rotation_crops,
            "reason_tamil": "சுழல் சாகுபடி மண்ணில் உள்ள நோய்க் கிருமிகளை கட்டுப்படுத்தும்; மண் தழைச்சத்தை மேம்படுத்தும்.",
        }
        citation = Citation(source=knowledge.source, title=f"Crop Rotation after {crop}", excerpt=f"After {crop}: grow {knowledge.rotation_crops[0] if knowledge.rotation_crops else 'not listed'}", confidence=0.83, category="crop")
        return self._timed_result("crop.rotation", start_ns, True, data=data, citations=[citation], confidence=0.83)

    async def _seed_rate(self, start_ns: int, crop: str, area_ha: float | None) -> ToolResult:
        knowledge = (await self._service.get(crop)).data
        rate_kg_ha = knowledge.seed_rate_kg_ha
        total_kg = round(rate_kg_ha * area_ha, 1) if area_ha is not None else None
        facts = [f"Seed rate for {crop}: {rate_kg_ha} kg per hectare ({knowledge.source})."]
        if total_kg is not None:
            facts.append(f"For the recorded farm area of {area_ha} ha: {total_kg} kg of seed.")
            advice = f"{area_ha} ஹெக்டேருக்கு {total_kg} கிலோ விதை தேவை."
        else:
            facts.append("Farm area is not known, so no total seed quantity is given.")
            advice = f"ஒரு ஹெக்டேருக்கு {rate_kg_ha} கிலோ விதை தேவை. நில அளவு தெரியவில்லை."
        data = {
            "crop": crop,
            "area_ha": area_ha,
            "seed_rate_kg_per_ha": rate_kg_ha,
            "total_seed_kg": total_kg,
            "facts": facts,
            "advice_tamil": advice,
        }
        citation = Citation(source=knowledge.source, title=f"Seed Rate — {crop}", excerpt=f"{rate_kg_ha} kg/ha recommended for {crop}", confidence=0.92, category="crop")
        return self._timed_result("crop.seed_rate", start_ns, True, data=data, citations=[citation], confidence=0.92)

    async def health(self) -> bool:
        return await self._service.health()
