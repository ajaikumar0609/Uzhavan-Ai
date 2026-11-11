"""
CropKnowledgeService integration tests.
No external dependencies — service uses in-memory TNAU data.
Covers: happy path, unknown crop, all 5 TNAU-defined crops, edge cases.
"""
from __future__ import annotations

import asyncio

import pytest

from backend.knowledge.crop.service import CropKnowledgeService
from backend.tools.agents.crop_agent import CropAgent
from backend.shared.models import ConversationContext, FarmerContext, FarmContext, SystemContext
from datetime import datetime
import uuid


@pytest.fixture
def service() -> CropKnowledgeService:
    return CropKnowledgeService()


@pytest.fixture
def agent(service) -> CropAgent:
    return CropAgent(service=service)


@pytest.fixture
def ctx() -> ConversationContext:
    return ConversationContext(
        system=SystemContext(trace_id=str(uuid.uuid4()), session_id="s1", request_id="r1", timestamp=datetime.now()),
        farmer=FarmerContext(farmer_id="f1", district="Thanjavur", language="Tamil"),
        farm=FarmContext(farm_id="farm1", farmer_id="f1", crop="paddy", crop_stage="tillering", area_ha=1.8, district="Thanjavur"),
        current_question="யூரியா போட வேண்டுமா?",
    )


# ── CropKnowledgeService tests ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_paddy_returns_knowledge(service):
    result = await service.get("paddy")
    assert result.data is not None
    assert result.data.crop == "paddy"
    assert result.data.npk_base_kg_ha["N"] == 120
    assert result.data.seed_rate_kg_ha == 60.0
    assert result.metadata.source == "tnau-crop-guide"


@pytest.mark.asyncio
async def test_get_unknown_crop_returns_default(service):
    result = await service.get("dragon_fruit")
    assert result.data is not None
    assert result.data.crop == "default"


@pytest.mark.asyncio
async def test_water_requirement_paddy_tillering(service):
    req = await service.get_water_requirement("paddy", "tillering")
    assert req == 8.0  # TNAU value for paddy tillering


@pytest.mark.asyncio
async def test_water_requirement_unknown_stage(service):
    req = await service.get_water_requirement("paddy", "not_a_stage")
    assert req == 7.0  # falls back to vegetative


@pytest.mark.asyncio
async def test_zone_crops_cauvery_delta_kharif(service):
    crops = await service.get_zone_crops("cauvery_delta", "kharif")
    assert "paddy" in crops
    assert "banana" in crops


@pytest.mark.asyncio
async def test_agroclimatic_zone_thanjavur(service):
    zone = service.get_agroclimatic_zone("Thanjavur")
    assert zone == "cauvery_delta"


@pytest.mark.asyncio
async def test_agroclimatic_zone_unknown_district(service):
    zone = service.get_agroclimatic_zone("unknown_district")
    assert zone == "default"


@pytest.mark.asyncio
async def test_all_crops_have_valid_npk(service):
    for crop_name in ["paddy", "rice", "cotton", "banana", "sugarcane", "groundnut", "maize", "tomato"]:
        result = await service.get(crop_name)
        assert result.data is not None
        assert "N" in result.data.npk_base_kg_ha
        assert result.data.npk_base_kg_ha["N"] > 0


@pytest.mark.asyncio
async def test_health_returns_true(service):
    assert await service.health() is True


# ── CropAgent tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fertilizer_plan_paddy_tillering(agent, ctx):
    result = await agent.execute("crop.fertilizer_plan", ctx, {"crop": "paddy", "crop_stage": "tillering"})
    assert result.success
    assert result.data["recommendation"]["N_kg_per_ha"] > 0
    assert result.data["recommendation"]["total_N_kg"] == round(result.data["recommendation"]["N_kg_per_ha"] * 1.8, 1)
    assert "தழைச்சத்து" in result.data["advice_tamil"]


@pytest.mark.asyncio
async def test_fertilizer_plan_no_n_at_grain_fill(agent, ctx):
    result = await agent.execute("crop.fertilizer_plan", ctx, {"crop": "paddy", "crop_stage": "grain_fill"})
    assert result.success
    assert result.data["recommendation"]["N_kg_per_ha"] == 0  # no N at grain fill


@pytest.mark.asyncio
async def test_seed_rate_paddy_1_8ha(agent, ctx):
    result = await agent.execute("crop.seed_rate", ctx, {"crop": "paddy", "area_ha": 1.8})
    assert result.success
    assert result.data["total_seed_kg"] == 108.0  # 60 kg/ha × 1.8 ha
    assert "ஹெக்டேருக்கு" in result.data["advice_tamil"]


@pytest.mark.asyncio
async def test_rotation_paddy(agent, ctx):
    result = await agent.execute("crop.rotation", ctx, {"crop": "paddy"})
    assert result.success
    assert "Sesbania" in result.data["recommended_rotation"][0]


@pytest.mark.asyncio
async def test_recommend_cauvery_delta(agent, ctx):
    result = await agent.execute("crop.recommend", ctx, {"district": "Thanjavur", "season": "kharif"})
    assert result.success
    assert "paddy" in result.data["recommended_crops"]
    assert result.data["agroclimatic_zone"] == "cauvery_delta"


@pytest.mark.asyncio
async def test_unknown_capability_returns_failure(agent, ctx):
    result = await agent.execute("crop.does_not_exist", ctx, {})
    assert not result.success
    assert "Unknown method" in result.error


@pytest.mark.asyncio
async def test_crop_calendar_paddy(agent, ctx):
    result = await agent.execute("crop.crop_calendar", ctx, {"crop": "paddy"})
    assert result.success
    assert "samba" in result.data


@pytest.mark.asyncio
async def test_missing_soil_type_defaults_to_medium(agent, ctx):
    # FarmContext has soil_type=None — must not raise
    result = await agent.execute("crop.fertilizer_plan", ctx, {"crop": "paddy", "crop_stage": "vegetative"})
    assert result.success, f"Should not fail: {result.error}"
