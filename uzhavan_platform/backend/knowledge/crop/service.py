from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from backend.shared.models.service import ServiceMetadata, ServiceResult


class CropKnowledge(BaseModel):
    """Structured crop knowledge from TNAU Crop Production Guide."""
    crop: str
    npk_base_kg_ha: dict[str, int]          # {"N": 120, "P": 50, "K": 50}
    water_req_mm_day: dict[str, float]       # by crop stage
    seed_rate_kg_ha: float
    rotation_crops: list[str]
    calendar: dict[str, Any]                 # season → sowing/harvest windows
    agroclimatic_zones: list[str]            # zones this crop suits
    source: str = "TNAU Crop Production Guide 2023"


class CropKnowledgeService:
    """
    Structured agricultural database built from TNAU Crop Production Guide.
    Pure data access — no farming reasoning. Returns typed CropKnowledge objects.
    CropAgent applies all agronomic reasoning on top of this data.
    """

    VERSION = "1.0"
    _LAST_UPDATED = datetime(2023, 12, 1, tzinfo=timezone.utc)

    async def get(self, crop: str, **kwargs) -> ServiceResult[CropKnowledge]:
        start = datetime.now(timezone.utc)
        knowledge = self._CROP_DATA.get(crop.lower())
        if not knowledge:
            knowledge = self._CROP_DATA.get("default")
        latency_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
        return ServiceResult(data=knowledge, metadata=ServiceMetadata(source="tnau-crop-guide", version=self.VERSION, latency_ms=latency_ms))

    async def search(self, query: str, **kwargs) -> ServiceResult[list[CropKnowledge]]:
        zone = kwargs.get("zone")
        season = kwargs.get("season")
        results = [k for k in self._CROP_DATA.values() if k.crop != "default"]
        if zone:
            results = [k for k in results if zone in k.agroclimatic_zones]
        return ServiceResult(data=results, metadata=ServiceMetadata(source="tnau-crop-guide", version=self.VERSION))

    async def get_water_requirement(self, crop: str, stage: str) -> float:
        """ETc (mm/day) for crop at given growth stage. Used by WeatherAgent for irrigation advice."""
        result = await self.get(crop)
        return result.data.water_req_mm_day.get(stage.lower(), result.data.water_req_mm_day.get("vegetative", 4.0))

    async def get_zone_crops(self, zone: str, season: str) -> list[str]:
        """Crops recommended for an agroclimatic zone and season."""
        return self._ZONE_CROP_MAP.get(zone, {}).get(season, ["paddy", "groundnut"])

    async def health(self) -> bool:
        return True  # in-memory data — always available

    def version(self) -> str:
        return self.VERSION

    async def last_updated(self) -> datetime:
        return self._LAST_UPDATED

    def get_agroclimatic_zone(self, district: str) -> str:
        return self._DISTRICT_ZONE_MAP.get(district.lower(), "default")

    # ── TNAU data tables ─────────────────────────────────────────────────────
    # Source: TNAU Crop Production Guide 2023, Tamil Nadu Agricultural University

    _CROP_DATA: dict[str, CropKnowledge] = {
        "paddy": CropKnowledge(
            crop="paddy",
            npk_base_kg_ha={"N": 120, "P": 50, "K": 50},
            water_req_mm_day={"seedling": 5.0, "vegetative": 7.0, "tillering": 8.0, "flowering": 6.0, "grain_fill": 4.0, "harvest": 2.0},
            seed_rate_kg_ha=60.0,
            rotation_crops=["green manure (Sesbania)", "pulses (black gram)", "groundnut"],
            calendar={"samba": {"sowing": "Jul–Aug", "transplanting": "Aug–Sep", "harvest": "Jan–Feb"}, "kuruvai": {"sowing": "May–Jun", "harvest": "Sep–Oct"}, "thaladi": {"sowing": "Nov–Dec", "harvest": "Apr–May"}},
            agroclimatic_zones=["cauvery_delta", "northern", "southern"],
        ),
        "rice": CropKnowledge(
            crop="rice",
            npk_base_kg_ha={"N": 120, "P": 50, "K": 50},
            water_req_mm_day={"seedling": 5.0, "vegetative": 7.0, "tillering": 8.0, "flowering": 6.0, "grain_fill": 4.0, "harvest": 2.0},
            seed_rate_kg_ha=60.0,
            rotation_crops=["green manure (Sesbania)", "pulses", "groundnut"],
            calendar={"samba": {"sowing": "Jul–Aug", "harvest": "Jan–Feb"}},
            agroclimatic_zones=["cauvery_delta", "northern", "southern"],
        ),
        "cotton": CropKnowledge(
            crop="cotton",
            npk_base_kg_ha={"N": 100, "P": 50, "K": 50},
            water_req_mm_day={"vegetative": 4.0, "flowering": 6.0, "grain_fill": 5.0, "harvest": 2.5},
            seed_rate_kg_ha=3.0,
            rotation_crops=["groundnut", "sorghum", "paddy"],
            calendar={"kharif": {"sowing": "Jun–Jul", "harvest": "Nov–Feb"}},
            agroclimatic_zones=["northern", "southern"],
        ),
        "banana": CropKnowledge(
            crop="banana",
            npk_base_kg_ha={"N": 200, "P": 60, "K": 300},
            water_req_mm_day={"vegetative": 5.0, "flowering": 6.5, "harvest": 4.0},
            seed_rate_kg_ha=0.0,  # suckers, not seed
            rotation_crops=["paddy", "pulses"],
            calendar={"planting": "Jun–Aug", "harvest": "12–14 months after planting"},
            agroclimatic_zones=["cauvery_delta", "high_rainfall"],
        ),
        "sugarcane": CropKnowledge(
            crop="sugarcane",
            npk_base_kg_ha={"N": 275, "P": 62, "K": 112},
            water_req_mm_day={"vegetative": 5.0, "tillering": 6.0, "grand_growth": 7.0, "harvest": 4.0},
            seed_rate_kg_ha=37500.0,  # buds/ha
            rotation_crops=["paddy", "groundnut"],
            calendar={"planting": "Jan–Feb or Jun–Jul", "harvest": "12 months after planting"},
            agroclimatic_zones=["cauvery_delta", "northern"],
        ),
        "groundnut": CropKnowledge(
            crop="groundnut",
            npk_base_kg_ha={"N": 25, "P": 50, "K": 75},
            water_req_mm_day={"vegetative": 3.5, "flowering": 5.0, "grain_fill": 4.0, "harvest": 2.0},
            seed_rate_kg_ha=100.0,
            rotation_crops=["paddy", "sorghum", "cotton"],
            calendar={"kharif": {"sowing": "Jun–Jul", "harvest": "Sep–Oct"}, "rabi": {"sowing": "Oct–Nov", "harvest": "Feb–Mar"}},
            agroclimatic_zones=["northern", "southern"],
        ),
        "maize": CropKnowledge(
            crop="maize",
            npk_base_kg_ha={"N": 150, "P": 75, "K": 75},
            water_req_mm_day={"vegetative": 4.0, "flowering": 5.5, "grain_fill": 4.5, "harvest": 2.0},
            seed_rate_kg_ha=20.0,
            rotation_crops=["black gram", "groundnut", "sorghum"],
            calendar={"kharif": {"sowing": "Jun–Jul", "harvest": "Sep–Oct"}},
            agroclimatic_zones=["northern", "southern"],
        ),
        "tomato": CropKnowledge(
            crop="tomato",
            npk_base_kg_ha={"N": 120, "P": 60, "K": 60},
            water_req_mm_day={"vegetative": 3.0, "flowering": 4.5, "fruit_development": 4.0, "harvest": 2.5},
            seed_rate_kg_ha=0.4,
            rotation_crops=["paddy", "maize", "sorghum"],
            calendar={"rabi": {"sowing": "Oct–Nov", "harvest": "Feb–Mar"}},
            agroclimatic_zones=["northern", "high_rainfall"],
        ),
        "default": CropKnowledge(
            crop="default",
            npk_base_kg_ha={"N": 80, "P": 40, "K": 40},
            water_req_mm_day={"vegetative": 4.0, "flowering": 5.0, "harvest": 2.0},
            seed_rate_kg_ha=25.0,
            rotation_crops=["pulse crop", "groundnut"],
            calendar={},
            agroclimatic_zones=["default"],
        ),
    }

    _ZONE_CROP_MAP: dict[str, dict[str, list[str]]] = {
        "cauvery_delta": {"kharif": ["paddy", "banana", "sugarcane"], "rabi": ["paddy", "banana"]},
        "northern": {"kharif": ["paddy", "groundnut", "cotton"], "rabi": ["sorghum", "sunflower", "maize"]},
        "southern": {"kharif": ["paddy", "cotton", "groundnut"], "rabi": ["sorghum", "pulses"]},
        "high_rainfall": {"kharif": ["paddy", "banana", "tapioca"], "rabi": ["vegetables", "paddy"]},
        "default": {"kharif": ["paddy", "groundnut"], "rabi": ["pulses", "sorghum"]},
    }

    _DISTRICT_ZONE_MAP: dict[str, str] = {
        "thanjavur": "cauvery_delta", "tiruvarur": "cauvery_delta",
        "nagapattinam": "cauvery_delta", "cuddalore": "cauvery_delta",
        "coimbatore": "northern", "erode": "northern", "tiruppur": "northern",
        "krishnagiri": "northern", "dharmapuri": "northern", "vellore": "northern",
        "madurai": "southern", "virudhunagar": "southern", "ramanathapuram": "southern",
        "tirunelveli": "southern", "thoothukudi": "southern",
        "nilgiris": "high_rainfall",
    }
